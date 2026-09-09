"""API modelləri üçün backend - Anthropic, OpenAI, Google.

    python -m src.run_eval --backend api --model anthropic:claude-opus-5 --language az

NİYƏ LAZIMDIR: v1-də yalnız lokal açıq modellər ölçülür (`Qwen3-1.7B`,
`Qolda-AVL-5B`). Azərbaycanda chatbot yerləşdirən heç bir təşkilat həmin
modelləri işlətmir - hamısı API modelləri işlədir. "GPT Azərbaycan dilində X%
səhv edir" cümləsi həm korporativ alıcı, həm mətbuat üçün lokal modellərin
rəqəmindən qat-qat aktualdır.

Bu modul `run_eval.py`-nin `Backend` protokolunu təmin edir və eyni müqaviləyə
tabedir: **metrika hesablamır**, yalnız xam mətn qaytarır.

Dizayn qərarları:

* **Prompt DƏYİŞDİRİLMİR.** Provayder üçün xüsusi təlimat əlavə etmək cazibədar
  görünür (aşağıdakı "sızan teq" problemi), amma promptu bir model üçün
  dəyişsək, müqayisə etibarını itirir - RQ1 modellərin biliyini yox, prompt
  fərqini ölçər. Prompt bütün modellər üçün eynidir; risklər ölçülür, gizlədilmir.

* **Düşünmə SÖNDÜRÜLÜR.** Bu, layihənin artıq bir dəfə öyrəndiyi dərsdir:
  `run_eval._close_forced_thinking` sənədləşdirir ki, mühakimə rejimi açıq
  qalanda 32 token limiti düşünmənin ortasında kəsilir və 96 sətrin 96-sı sıfır
  bal alır. API modellərində eyni tələ var, özü də daha pisi - Claude Opus 5-də
  düşünmə SUSMAYA GÖRƏ AÇIQDIR (Opus 4.8-dən fərqli olaraq) və `max_tokens`
  düşünmə + cavab üçün ORTAQ limitdir.

* **Determinizm mümkün deyil - və bu, qeyd olunur.** Lokal qaçışlarda
  `do_sample=False` və sabit seed nəticəni təkrarlanan edir. API-də belə zəmanət
  yoxdur: Claude 5 ailəsi `temperature` parametrini ümumiyyətlə rədd edir (400),
  OpenAI-də isə temperature=0 belə eyni cavabı zəmanət etmir. Ona görə hər qaçış
  `determinism: "best-effort"` kimi yazılır. Bunu məqalədə gizlətmək olmaz:
  API sətirləri lokal sətirlərlə eyni etibarlılıq sinfində DEYİL.

* **Model versiyası qeyd olunur.** `gpt-5` və ya `claude-opus-5` sabit ad deyil,
  altındakı çəkilər dəyişə bilər. Cavabın qaytardığı faktiki model adı
  `describe()`-a yazılır ki, altı ay sonra rəqəmin hansı versiyaya aid olduğu
  bilinsin.

* **Token sayı yığılır, qiymət təxmini opsionaldır.** Tokenlər həmişə dəqiqdir;
  qiymət cədvəli isə köhnəlir. `PRICES` yalnız mənbəyi təsdiqlənmiş sətirləri
  saxlayır, qalanı üçün `cost_usd = None` qaytarılır - uydurma rəqəm verməkdənsə
  boş qaytarmaq düzgündür.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Protocol

__all__ = [
    "APIBackend",
    "QuotaExhausted",
    "Usage",
    "ProviderAdapter",
    "AnthropicAdapter",
    "OpenAIAdapter",
    "GoogleAdapter",
    "PROVIDERS",
    "PRICES",
    "parse_model_ref",
    "leaked_tag_count",
]


#: `<thinking>`, `<think>` və bənzəri daxili teqlər.
#:
#: Claude Opus 5-də düşünmə söndürüləndə model bəzən daxili XML teqlərini görünən
#: cavaba yazır. Sənədləşdirilmiş həlli promptda "daxili teq yazma" təlimatı
#: verməkdir - amma biz promptu dəyişmirik (yuxarıya bax). Ona görə hadisəni
#: SAYIRIQ: qaçış xülasəsində `leaked_tags` sıfırdan böyükdürsə, həmin modelin
#: rəqəmi şübhəlidir və əl ilə baxılmalıdır.
#:
#: Bu, layihənin kiril əlifbasını sayma üsulunun eynisidir: davranışı prompt ilə
#: bastırmaq əvəzinə ölçüb hesabata yazmaq.
_INTERNAL_TAG = re.compile(r"</?(?:thinking|think|scratchpad|antml:thinking)\b", re.I)


def leaked_tag_count(responses: list[str]) -> int:
    """Cavablarda daxili teq sızması sayı."""
    return sum(1 for text in responses if _INTERNAL_TAG.search(text or ""))


class QuotaExhausted(RuntimeError):
    """Ardıcıl uğursuzluq həddi keçildi - qaçış davam etdirilmir."""


def _short_error(exc: Exception, limit: int = 150) -> str:
    """Uzun API xətasından oxunaqlı bir sətir.

    Provayder cavabları JSON-un içində kvota pozuntusu siyahısı, sənəd linkləri
    və təkrar cəhd təfərrüatı daşıyır. Bizə lazım olan status və səbəbdir.
    """
    text = " ".join(str(exc).split())
    return f"{type(exc).__name__}: {text[:limit]}"


#: 1M token üçün (giriş, çıxış) USD.
#:
#: DİQQƏT: yalnız mənbəyi təsdiqlənmiş sətirlər. Qiymətlər dəyişir - istifadədən
#: əvvəl provayderin qiymət səhifəsi ilə yoxla. Cədvəldə olmayan model üçün
#: `cost_usd` None qaytarılır; tokenlər yenə də yazılır, ona görə qiyməti sonra
#: kənarda hesablamaq mümkündür.
PRICES: dict[str, tuple[float, float]] = {
    # Anthropic - mənbə: platform.claude.com qiymət cədvəli (2026-06-24)
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    # OpenAI və Google: təsdiqlənməyib - qəsdən boş saxlanılıb.
}


@dataclass
class Usage:
    """Qaçış boyu yığılan istifadə. Qiymət hesablana bilməyəndə `None` qalır."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    failures: int = 0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def cost_usd(self, model_id: str) -> float | None:
        price = PRICES.get(model_id)
        if price is None:
            return None
        in_rate, out_rate = price
        return (self.input_tokens * in_rate + self.output_tokens * out_rate) / 1_000_000

    def as_dict(self, model_id: str) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "failures": self.failures,
            "cost_usd": self.cost_usd(model_id),
        }


class ProviderAdapter(Protocol):
    """Bir provayderin minimal interfeysi.

    `complete` BİR promptu emal edir; paralelləşdirmə `APIBackend`-in işidir.
    Qaytarır: (mətn, giriş tokenləri, çıxış tokenləri, faktiki model adı).
    """

    provider: str

    def complete(self, prompt: str, max_tokens: int) -> tuple[str, int, int, str]:
        ...


# --------------------------------------------------------------------------
# Anthropic
# --------------------------------------------------------------------------


class AnthropicAdapter:
    """Anthropic Messages API.

    İki parametr bu tapşırıq üçün kritikdir:

    * `thinking={"type": "disabled"}` - Claude Opus 5-də düşünmə susmaya görə
      AÇIQDIR və `max_tokens` düşünmə ilə cavab arasında bölünür. 32 token
      limitində açıq düşünmə bütün cavabları boşaldar. (Söndürməyə yalnız
      `effort` `high` və ya aşağı olanda icazə var; biz `effort` təyin etmirik,
      susma dəyəri `high`-dır, ona görə qəbul olunur.)

    * `temperature` VERİLMİR - Claude 5 ailəsində bu parametr silinib və
      göndərilsə 400 qaytarır. Determinizm API tərəfdə mümkün deyil.
    """

    provider = "anthropic"

    def __init__(
        self,
        model_id: str,
        max_retries: int = 5,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        import anthropic

        self.model_id = model_id
        self._client = anthropic.Anthropic(
            max_retries=max_retries, base_url=base_url, api_key=api_key
        )

    def complete(self, prompt: str, max_tokens: int) -> tuple[str, int, int, str]:
        message = self._client.messages.create(
            model=self.model_id,
            max_tokens=max_tokens,
            thinking={"type": "disabled"},
            messages=[{"role": "user", "content": prompt}],
        )

        # Təhlükəsizlik təsnifatçıları sorğunu rədd edə bilər: HTTP 200 gəlir,
        # amma `content` boş olur. `content[0]` birbaşa oxunsa, qaçış çökür.
        if message.stop_reason == "refusal":
            text = ""
        else:
            text = "".join(
                block.text for block in message.content if block.type == "text"
            )

        return (
            text.strip(),
            message.usage.input_tokens,
            message.usage.output_tokens,
            message.model,
        )


# --------------------------------------------------------------------------
# OpenAI
# --------------------------------------------------------------------------


class OpenAIAdapter:
    """OpenAI Chat Completions - **və onunla uyğun hər hansı provayder**.

    `base_url` verilsə, eyni adapter Z.ai (GLM), DeepSeek, Qwen API, Mistral,
    OpenRouter, Groq, Together və digər OpenAI-uyğun endpoint-lərə gedir. Hər
    biri üçün ayrıca adapter yazmaq lazım deyil - protokol eynidir, yalnız ünvan
    və açar dəyişir.

    Nümunə (GLM-5.2):

        --model openai:glm-5.2 --base-url https://api.z.ai/api/paas/v4
        --api-key-env ZAI_API_KEY

    İki uyğunluq tələsi var və hər ikisi mühakimə modellərində üzə çıxır:

    * `max_tokens` mühakimə modellərində rədd olunur, əvəzinə
      `max_completion_tokens` gözlənilir;
    * `temperature` həmin modellərdə yalnız susma dəyərini qəbul edir.

    Hər ikisi birinci uğursuz cağırışda AVTOMATİK aşkarlanır və yadda saxlanılır
    - model adına görə təxmin etmək etibarsızdır, çünki adlar dəyişir.
    """

    provider = "openai"

    def __init__(
        self,
        model_id: str,
        max_retries: int = 5,
        base_url: str | None = None,
        api_key: str | None = None,
        seed: int | None = 0,
        disable_reasoning: bool = False,
    ) -> None:
        from openai import OpenAI

        self.model_id = model_id
        self.base_url = base_url
        self._client = OpenAI(
            max_retries=max_retries, base_url=base_url, api_key=api_key
        )
        self.seed = seed
        self._token_param = "max_tokens"
        self._send_temperature = True
        self._send_seed = seed is not None
        self.disable_reasoning = disable_reasoning

    def _kwargs(self, prompt: str, max_tokens: int) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            self._token_param: max_tokens,
        }
        # DÜŞÜNMƏNİ SÖNDÜRMƏK MÜQAYİSƏ ÜÇÜNDÜR, qənaət üçün yox.
        #
        # Hibrid mühakimə modeli (`qwen3-32b` kimi) 32 tokenlik büdcəni daxili
        # mühakiməyə xərcləyir və cavaba ÇATMIR: ölçüldü, 10 sualdan 9-u boş
        # gəldi. Lokal Thinking modeli isə `enable_thinking=False` ilə qaçır.
        # Şərait eyni olmasa, API modeli ilə lokal model müqayisə edilə bilməz.
        #
        # `reasoning` OpenRouter genişlənməsidir, OpenAI protokolunun özündə
        # yoxdur. Dəstəkləməyən endpoint onu rədd edir, ona görə yalnız açıq
        # istənəndə göndərilir.
        if self.disable_reasoning:
            kwargs["extra_body"] = {"reasoning": {"effort": "none"}}
        if self._send_temperature:
            kwargs["temperature"] = 0
        # `seed` API tərəfdə təkrarlanabilirliyi YAXŞILAŞDIRIR, zəmanət vermir.
        # Provayder onu dəstəkləyirsə, eyni prompt eyni cavabı vermə ehtimalı
        # xeyli artır - bu, layihənin ən zəif yeri olan determinizm iddiasını
        # gücləndirir. Dəstəkləməyən endpoint-lər parametri rədd edir, ona görə
        # aşağıdakı uyğunluq döngəsi onu bir dəfə sınayıb söndürür.
        if self._send_seed:
            kwargs["seed"] = self.seed
        return kwargs

    @property
    def thinking_state(self) -> str:
        """OpenAI-uyğun protokolda düşünməni söndürmək üçün standart açar yoxdur.

        `"disabled"` yazmaq YANLIŞ olardı: GLM-5.2 kimi mühakimə edən modellərdə
        düşünmə işləyir, sadəcə cavab mətnindən ayrı sahədə qaytarılır. Nə
        söndürdüyümüzü, nə də açıq qoyduğumuzu iddia edə bilmərik - nəzarətimiz
        yoxdur, və qeyd bunu deməlidir.
        """
        if self.disable_reasoning:
            return "disabled via OpenRouter `reasoning.effort=none`"
        return "not-controlled (no standard toggle in OpenAI-compatible API)"

    @property
    def determinism(self) -> str:
        if self._send_seed and self._send_temperature:
            return "seeded (temperature=0, seed set) - best-effort"
        if self._send_temperature:
            return "temperature=0 only - best-effort"
        return "best-effort"

    def complete(self, prompt: str, max_tokens: int) -> tuple[str, int, int, str]:
        for _ in range(4):  # ən çox üç uyğunluq düzəlişi + son cəhd
            try:
                response = self._client.chat.completions.create(
                    **self._kwargs(prompt, max_tokens)
                )
                break
            except Exception as exc:  # noqa: BLE001 - mesajın mətninə baxılır
                message = str(exc)
                if "max_tokens" in message and self._token_param == "max_tokens":
                    self._token_param = "max_completion_tokens"
                    continue
                if "temperature" in message and self._send_temperature:
                    self._send_temperature = False
                    continue
                if "seed" in message and self._send_seed:
                    self._send_seed = False
                    continue
                raise
        else:
            raise RuntimeError(f"{self.model_id}: parametr uyğunluğu tapılmadı")

        usage = response.usage
        return (
            (response.choices[0].message.content or "").strip(),
            getattr(usage, "prompt_tokens", 0) or 0,
            getattr(usage, "completion_tokens", 0) or 0,
            response.model,
        )


# --------------------------------------------------------------------------
# Google
# --------------------------------------------------------------------------


def _is_invalid_argument(exc: Exception) -> bool:
    """400 INVALID_ARGUMENT - parametr uyğunsuzluğu, əlçatanlıq problemi yox."""
    text = str(exc)
    return "INVALID_ARGUMENT" in text or "400" in text


class GoogleAdapter:
    """Google Gemini (`google-genai`).

    KONFİQURASİYA PİLLƏSİ. Gemini model ailələri fərqli parametr dəsti qəbul
    edir və rədd edəndə **sahənin adını demir** - mesaj hərfən "Request contains
    an invalid argument" olur. `gemini-3.5-flash` `thinking_budget=0` qəbul edir,
    `gemini-3.6-flash` etmir; hansının nəyi qəbul etdiyini sənəddən oxumaq
    etibarsızdır, çünki modellər aylıq dəyişir.

    Ona görə adapter özü uyğunlaşır: birinci variantla başlayır, 400 alanda
    növbəti variantа keçir, işləyəni tapıb ona kilidlənir. Sıra ƏN ÇOX
    NƏZARƏTDƏN ƏN AZA doğrudur - düşünməni söndürmək və temperaturu sıfırlamaq
    ölçmə üçün dəyərlidir, ona görə əvvəlcə onlar sınanır.

    HANSI VARİANTIN İŞLƏDİYİ QEYD OLUNUR. Bu, rahatlıq deyil, metodoloji
    tələbdir: düşünmə söndürülə bilməyən modelin rəqəmi söndürülənlə eyni
    şəraitdə alınmayıb və cədvəldə belə göstərilməlidir.
    """

    provider = "google"

    #: (ad, thinking_config göndər, temperature göndər)
    _VARIANTS: tuple[tuple[str, bool, bool], ...] = (
        ("thinking-off+temp0", True, True),
        ("temp0", False, True),
        ("thinking-off", True, False),
        ("minimal", False, False),
    )

    def __init__(
        self,
        model_id: str,
        max_retries: int = 5,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        from google import genai
        from google.genai import types

        self.model_id = model_id
        # Pulsuz səviyyənin dəqiqəlik limiti var və 356 çağırışlıq qaçış ona
        # mütləq dəyir. Təkrar cəhd qurulmasa, hər 429 bir sətri itirir və
        # qaçışı əl ilə dəfələrlə yenidən işlətmək lazım gəlir.
        #
        # 429 SİYAHIYA DAXİLDİR, çünki SDK-nın susma dəyəri yalnız server
        # xətalarını (5xx) təkrarlayır - limit xətası isə məhz bizim gözlədiyimiz
        # haldır.
        http_options = types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=max_retries,
                http_status_codes=[429, 500, 502, 503, 504],
            )
        )
        if base_url:
            http_options.base_url = base_url
        self._client = genai.Client(api_key=api_key, http_options=http_options)
        self._variant = 0

    @property
    def variant(self) -> str:
        return self._VARIANTS[self._variant][0]

    @property
    def thinking_state(self) -> str:
        sends_thinking_config = self._VARIANTS[self._variant][1]
        if sends_thinking_config:
            return "disabled"
        # Model `thinking_budget=0` parametrini rədd etdi - düşünmə çox güman
        # AÇIQ qalıb. Cavabların qısalığı bunu gizlədə bilər, amma `max_tokens`
        # düşünmə ilə cavab arasında bölünürsə, bal süni şəkildə aşağı düşür.
        return "not-disabled (model rejected the parameter)"

    def _config(self, max_tokens: int) -> Any:
        from google.genai import types

        _, sends_thinking, sends_temperature = self._VARIANTS[self._variant]
        kwargs: dict[str, Any] = {"max_output_tokens": max_tokens}
        if sends_temperature:
            kwargs["temperature"] = 0
        if sends_thinking:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        return types.GenerateContentConfig(**kwargs)

    def complete(self, prompt: str, max_tokens: int) -> tuple[str, int, int, str]:
        while True:
            try:
                response = self._client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=self._config(max_tokens),
                )
                break
            except Exception as exc:  # noqa: BLE001
                # Yalnız parametr xətasında pilləni endir. 404 (model yoxdur)
                # və 429 (limit) başqa problemlərdir; onlarda variant dəyişmək
                # səhvi gizlədər və qaçış səssizcə fərqli şəraitdə davam edər.
                if not _is_invalid_argument(exc):
                    raise
                if self._variant + 1 >= len(self._VARIANTS):
                    raise
                self._variant += 1

        usage = getattr(response, "usage_metadata", None)
        return (
            (response.text or "").strip(),
            getattr(usage, "prompt_token_count", 0) or 0,
            getattr(usage, "candidates_token_count", 0) or 0,
            self.model_id,
        )


PROVIDERS: dict[str, type] = {
    "anthropic": AnthropicAdapter,
    "openai": OpenAIAdapter,
    "google": GoogleAdapter,
}

#: Açar mühit dəyişəni - açar yoxdursa, qaçışa başlamazdan ƏVVƏL deyilir.
#: 356 sətrin ortasında autentifikasiya xətası ilə çökmək vaxt itkisidir.
_API_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def load_dotenv(path: Path | None = None) -> dict[str, str]:
    """`.env` faylını oxuyur. Xarici asılılıq işlədilmir.

    NİYƏ LAZIMDIR. Açar `setx` ilə qurulanda YALNIZ yeni proseslər onu görür;
    artıq işləyən terminal köhnə mühiti saxlayır. Uzun sessiyada bu, "açar
    qurdum, amma proqram görmür" vəziyyəti yaradır və səbəbi aydın olmur.

    `.env` faylı bu problemi aradan qaldırır: proqram hər dəfə oxuyur.

    MÜHİT ÜSTÜNDÜR. Mühitdə dəyişən varsa, fayl ona TOXUNMUR. Əks halda köhnə
    fayl aktiv mühiti səssizcə üstələyərdi və bu, izlənməsi çətin səhvdir.

    Fayl `.gitignore`-dadır və repoya düşmür.
    """
    path = path or Path(".env")
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        value = value.strip()
        # Dırnaqlar istəyə bağlıdır; qoyulubsa, dəyərə daxil edilmir.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[name.strip()] = value
    return values


def read_api_key(env_var: str, path: Path | None = None) -> str | None:
    """Açar: əvvəlcə mühitdən, sonra `.env` faylından."""
    return os.environ.get(env_var) or load_dotenv(path).get(env_var) or None


def parse_model_ref(reference: str) -> tuple[str, str]:
    """`"anthropic:claude-opus-5"` -> `("anthropic", "claude-opus-5")`.

    Provayder AÇIQ yazılır, model adından təxmin edilmir. Ad şablonları
    provayderlər arasında üst-üstə düşür və dəyişir; səhv təxmin isə səssizcə
    yanlış API-yə gedər.
    """
    provider, separator, model_id = reference.partition(":")
    if not separator or not model_id:
        raise ValueError(
            f"model istinadı `provayder:model` formatında olmalıdır: {reference!r}\n"
            f"mövcud provayderlər: {', '.join(sorted(PROVIDERS))}"
        )
    if provider not in PROVIDERS:
        raise ValueError(
            f"naməlum provayder: {provider!r}; gözlənilən: {', '.join(sorted(PROVIDERS))}"
        )
    return provider, model_id


# --------------------------------------------------------------------------
# Backend
# --------------------------------------------------------------------------


@dataclass
class APIBackend:
    """`run_eval.Backend` protokolunu təmin edən API backend-i.

    Paralellik: API-lər partiya qəbul etmir, ona görə partiya iplərə bölünür.
    `ThreadPoolExecutor.map` SIRANI QORUYUR - bu, sadəcə rahatlıq deyil, şərtdir:
    `run_evaluation` cavabları sətirlərlə `zip(strict=True)` ilə birləşdirir,
    sıra pozulsa cavablar səhv suallara yazılar və heç bir xəta görünməz.
    """

    name: str
    adapter: ProviderAdapter
    max_tokens: int = 64
    max_workers: int = 4
    usage: Usage = field(default_factory=Usage)
    resolved_model: str = ""
    leaked_tags: int = 0

    #: Hansı endpoint cavab verdi. Eyni model adı fərqli hostlarda fərqli
    #: kvantlaşdırma və fərqli versiya ola bilər (OpenRouter vs birinci tərəf),
    #: ona görə rəqəmlə birlikdə saxlanılır.
    base_url: str | None = None

    #: Neçə ardıcıl uğursuzluqdan sonra qaçış dayandırılsın.
    #:
    #: NİYƏ LAZIMDIR: pulsuz səviyyələrin gündəlik kvotası var (Gemini-də bəzi
    #: modellər üçün cəmi 20 sorğu). Kvota bitəndən sonra qalan 340 sətir
    #: yalnız 429 qaytarır - hər biri üçün təkrar cəhdlər gözləyir və 2 KB xəta
    #: mətni çap olunur. Dayanmaq həm vaxta, həm ekrana qənaətdir; itən heç nə
    #: yoxdur, çünki uğurlu sətirlər onsuz da diskdədir və `--resume` sabah
    #: davam etdirir.
    abort_after: int = 12

    #: Sonuncu `generate` çağırışında hansı promptların UĞURSUZ olduğu.
    #:
    #: `run_evaluation` bu maskaya baxıb uğursuz sətirləri fayla YAZMIR. Səbəb
    #: `--resume` ilə bağlıdır: davam etmə məntiqi artıq yazılmış `id`-ləri
    #: atlayır, ona görə uğursuz çağırış üçün boş sətir yazsaydıq, həmin sual
    #: bir daha heç vaxt soruşulmazdı - 429 və ya şəbəkə xətası datasetdə daimi
    #: boşluğa çevrilərdi. Yazmamaqla sual növbəti qaçışda avtomatik təkrarlanır.
    last_failed: list[bool] = field(default_factory=list)
    consecutive_failures: int = 0

    @classmethod
    def from_reference(
        cls,
        reference: str,
        max_tokens: int = 64,
        max_workers: int = 4,
        max_retries: int = 5,
        base_url: str | None = None,
        api_key_env: str | None = None,
        disable_reasoning: bool = False,
    ) -> APIBackend:
        provider, model_id = parse_model_ref(reference)

        # Üçüncü tərəf endpoint-i işlədiləndə açar həmin provayderindir, ona
        # görə dəyişənin adı verilə bilər. Belə olmasa, Z.ai açarını
        # `OPENAI_API_KEY`-ə yazmaq lazım gələrdi və istifadəçinin əsl OpenAI
        # açarı üstündən yazılardı.
        env_var = api_key_env or _API_KEY_ENV[provider]
        api_key = read_api_key(env_var)
        if not api_key:
            raise RuntimeError(
                f"{env_var} nə mühitdə, nə də `.env` faylında tapıldı - "
                f"{provider} çağırışları alınmayacaq."
            )

        kwargs: dict[str, Any] = {
            "max_retries": max_retries,
            "base_url": base_url,
            "api_key": api_key,
        }
        # Yalnız dəstəkləyən adapterə ötürülür: `anthropic` və `google`
        # adapterlərində belə parametr yoxdur və TypeError verərdi.
        if disable_reasoning and provider == "openai":
            kwargs["disable_reasoning"] = True
        adapter = PROVIDERS[provider](model_id, **kwargs)
        backend = cls(
            name=reference,
            adapter=adapter,
            max_tokens=max_tokens,
            max_workers=max_workers,
        )
        backend.base_url = base_url
        return backend

    def generate(self, prompts: list[str]) -> list[str]:
        def one(prompt: str) -> tuple[str, bool]:
            try:
                text, in_tok, out_tok, model = self.adapter.complete(
                    prompt, self.max_tokens
                )
            except Exception as exc:  # noqa: BLE001
                # Bir sətrin çökməsi 356 sətirlik qaçışı dayandırmamalıdır.
                # Uğursuz sətir fayla yazılmır (bax: `last_failed`), ona görə
                # növbəti qaçış onu avtomatik təkrarlayır.
                self.usage.failures += 1
                # Mətn QISALDILIR. Provayderlər 429 cavabına kvota təfərrüatı,
                # sənəd linkləri və pozuntu siyahısı qoşur - sətir başına 2 KB.
                # 340 uğursuz sətirdə ekran oxunmaz olur və əsl səbəb itir.
                print(f"  XƏTA: {_short_error(exc)}", flush=True)
                return "", True
            self.usage.add(in_tok, out_tok)
            if not self.resolved_model:
                self.resolved_model = model
            return text, False

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            results = list(pool.map(one, prompts))

        responses = [text for text, _ in results]
        self.last_failed = [failed for _, failed in results]
        self.leaked_tags += leaked_tag_count(
            [text for text, failed in results if not failed]
        )

        # Ardıcıl uğursuzluq sayğacı. Partiya daxilində sıra qorunduğu üçün
        # sayğac sondan geriyə hesablanır: partiyanın sonunda bir uğur olsa,
        # zəncir qırılıb deməkdir.
        for failed in reversed(self.last_failed):
            if failed:
                self.consecutive_failures += 1
            else:
                self.consecutive_failures = 0
                break

        if self.abort_after and self.consecutive_failures >= self.abort_after:
            raise QuotaExhausted(
                f"{self.consecutive_failures} ardıcıl uğursuz çağırış - qaçış "
                f"dayandırıldı.\n"
                f"Ən çox ehtimal olunan səbəb gündəlik kvotadır. Uğurlu sətirlər "
                f"diskdədir; kvota bərpa olunanda eyni əmri təkrar işlət."
            )

        return responses

    def describe(self) -> dict[str, Any]:
        """Qaçışın hər sətrinə yazılan sabit metadata.

        `determinism` sahəsi bilərəkdən açıqdır: lokal qaçışlar `greedy+seed`
        ilə təkrarlanır, API qaçışları təkrarlanmır. Bu fərq nəticə cədvəlində
        görünməlidir.
        """
        _, model_id = parse_model_ref(self.name)
        meta: dict[str, Any] = {
            "provider": self.adapter.provider,
            "requested_model": model_id,
            "resolved_model": self.resolved_model or None,
            "max_tokens": self.max_tokens,
            # Adapter düşünməni söndürə bilmədiyini bildirirsə, ONUN sözü
            # yazılır. Sabit "disabled" yazmaq yalan olardı: bəzi modellər
            # söndürmə parametrini rədd edir və düşünmə açıq qalır.
            "thinking": getattr(self.adapter, "thinking_state", "disabled"),
            # Adapter daha dəqiq iddia edə bilirsə (seed qəbul olunubsa),
            # onun sözü yazılır. Hər halda "best-effort" qalır: seed heç bir
            # provayderdə bit-bərabər təkrar zəmanət etmir.
            "determinism": getattr(self.adapter, "determinism", "best-effort"),
        }
        variant = getattr(self.adapter, "variant", None)
        if variant:
            meta["config_variant"] = variant
        if self.base_url:
            meta["base_url"] = self.base_url
        return meta

    def summary(self) -> dict[str, Any]:
        """Qaçışın sonunda sidecar fayla yazılan xülasə."""
        _, model_id = parse_model_ref(self.name)
        return {
            "model": self.name,
            **self.describe(),
            "usage": self.usage.as_dict(model_id),
            "leaked_internal_tags": self.leaked_tags,
        }
