"""Modelləri işə salıb XAM cavabları yığır.

    python -m src.run_eval --model Qwen/Qwen3-1.7B --language az
    python -m src.run_eval --model Qwen/Qwen3-1.7B --language en

Bu modul metrika HESABLAMIR. Onun yeganə işi modelin xam mətn cavabını diskə
yazmaqdır. Səbəb brief-in 7-ci bölməsindədir: metrik düsturu sonra dəyişsə,
bütün eksperimenti yenidən işlətmək lazım gəlməsin. Bal hesablama `analyze.py`-nin
işidir və xam fayllar üzərində istənilən qədər təkrar işlədilə bilər.

Dizayn qərarları:

* **Deterministik generasiya.** `do_sample=False` (greedy) və sabit seed.
  Məqalədəki rəqəm təkrar işlədiləndə eyni çıxmalıdır; temperatur > 0 olsaydı,
  hər qaçış fərqli nəticə verərdi və heç bir etibarlılıq intervalı bunu örtməzdi.
* **Davam etdirilə bilən.** Artıq yazılmış `id`-lər oxunub atlanır. 500 nümunəlik
  qaçış yarıda kəsilsə, işin yarısı itmir.
* **AZ və EN eyni `id` dəsti üzərində.** `metrics.compare_paired` cütləşdirilmiş
  müqayisə tələb edir — sətirlər üst-üstə düşməsə, RQ1 hesablanmır.
* **Prompt sualın dilindədir.** Azərbaycan sualına ingilis təlimatı versək,
  ölçdüyümüz şey modelin Azərbaycan bilikləri yox, təlimat izləmə qabiliyyəti olur.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import sys
import time
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from src.build_dataset import load_jsonl

__all__ = [
    "GenerationConfig",
    "Backend",
    "EchoBackend",
    "OracleBackend",
    "TransformersBackend",
    "PROMPT_STYLES",
    "build_prompt",
    "completed_ids",
    "run_evaluation",
]


LANGUAGES = ("az", "en")

#: Qısa cavab tələb edən prompt — sualın dilində, iki nümunə ilə.
#:
#: NÜMUNƏLƏR NİYƏ LAZIMDIR: təkcə "qısa cavab ver" təlimatı işləmir. Empirik
#: olaraq Qwen3-1.7B səkkiz sualın səkkizini də DÜZGÜN bilirdi, amma cavabları
#: "Fransanın paytaxtı Parisdir" şəklində cümlə ilə verirdi və exact match
#: 1/8 çıxırdı. Belə rəqəm modelin biliyini yox, təlimat izləmə davranışını
#: ölçür — RQ1-in cavabı tamamilə yanlış olardı.
#:
#: İki nümunə gözlənilən formatı göstərir. Nümunə faktları datasetdə YOXDUR
#: (yoxlanılıb) — əks halda modelə cavab sızardı.
#:
#: AZ və EN nümunələri eyni faktları soruşur, yoxsa fərqin bir hissəsi prompt
#: fərqindən gələr və RQ1 çirklənər.
PROMPT_TEMPLATES = {
    "az": (
        "Suala qısa cavab ver. Yalnız cavabı yaz — cümlə qurma, izahat vermə.\n\n"
        "Sual: Misirin paytaxtı hansı şəhərdir?\n"
        "Cavab: Qahirə\n\n"
        "Sual: Su molekulunun kimyəvi formulu nədir?\n"
        "Cavab: H2O\n\n"
        "Sual: {question}\n"
        "Cavab:"
    ),
    "en": (
        "Answer the question briefly. Write only the answer — no sentence, "
        "no explanation.\n\n"
        "Question: What is the capital city of Egypt?\n"
        "Answer: Cairo\n\n"
        "Question: What is the chemical formula of a water molecule?\n"
        "Answer: H2O\n\n"
        "Question: {question}\n"
        "Answer:"
    ),
}

#: Əlifba NƏZARƏTİ üçün ikinci prompt dəsti.
#:
#: Layihənin əsas tapıntısı budur ki, qazax dilinə köklənmiş model azərbaycan
#: suallarına kiril əlifbası ilə cavab verir. Hakimin verəcəyi ilk sual isə
#: bunun promptdan asılı olub-olmadığıdır. Bu dəst məhz həmin sualı bağlayır:
#: əlifba AÇIQ şəkildə tələb olunur.
#:
#:   kiril davranışı qalırsa  -> tapıntı promptdan asılı deyil
#:   kiril yox olursa         -> bu, təlimat izləmə problemidir
#:
#: İngilis variantı mənaca eynidir və faktiki olaraq boş nəzarətdir (ingilis
#: onsuz da latındır) — simmetriya RQ1 müqayisəsinin qorunması üçün lazımdır.
SCRIPT_PROMPT_TEMPLATES = {
    "az": (
        "Suala qısa cavab ver. Yalnız cavabı yaz — cümlə qurma, izahat vermə.\n"
        "Cavabı MÜTLƏQ Azərbaycan latın əlifbası ilə yaz.\n\n"
        "Sual: Misirin paytaxtı hansı şəhərdir?\n"
        "Cavab: Qahirə\n\n"
        "Sual: Su molekulunun kimyəvi formulu nədir?\n"
        "Cavab: H2O\n\n"
        "Sual: {question}\n"
        "Cavab:"
    ),
    "en": (
        "Answer the question briefly. Write only the answer — no sentence, "
        "no explanation.\n"
        "Write the answer using the Latin alphabet.\n\n"
        "Question: What is the capital city of Egypt?\n"
        "Answer: Cairo\n\n"
        "Question: What is the chemical formula of a water molecule?\n"
        "Answer: H2O\n\n"
        "Question: {question}\n"
        "Answer:"
    ),
}

#: PROMPT ROBUSTLUĞU üçün iki əlavə dəst.
#:
#: Bütün nəticələr tək şablonla alınsaydı, ən adi etiraz cavabsız qalardı:
#: "bəlkə sizin promptunuz pisdir və uçurum ondan gəlir". Bu iki dəst həmin
#: sualı bağlayır. Fərq QƏSDƏN böyükdür, yoxsa yoxlama formal olardı:
#:
#:   zeroshot  nümunə YOXDUR. Few-shot nümunələrin özü ipucu verirmi?
#:   plain     nümunə var, amma format tamam başqadır: etiketsiz, sadəcə
#:             sual və cavab. Model "Sual:/Cavab:" qəlibinə bağlıdırmı?
#:
#: Nümunə faktları əsas dəstlə eynidir (Misir, su), çünki dəyişdirilsəydi,
#: ölçdüyümüz şey format yox, nümunənin çətinliyi olardı. Həmin iki cavab
#: `build_dataset`-dəki çirklənmə qapısı ilə onsuz da datasetdən kənardadır.
ZEROSHOT_PROMPT_TEMPLATES = {
    "az": (
        "Aşağıdakı suala qısa cavab ver. Yalnız cavabı yaz.\n\n"
        "Sual: {question}\n"
        "Cavab:"
    ),
    "en": (
        "Answer the following question briefly. Write only the answer.\n\n"
        "Question: {question}\n"
        "Answer:"
    ),
}

#: `plain`-in İLK VERSİYASI SƏHV İDİ və düzəliş qeyd edilməlidir.
#:
#: Orada etiketlərlə birlikdə QISALIQ TƏLİMATI da silinmişdi, yəni variant bir
#: yox, İKİ şeyi eyni anda dəyişirdi. Nəticədə bütün modellər sıfıra yaxın bal
#: aldı, amma cavabları DOĞRU idi:
#:
#:     "Fransanın paytaxtı **Paris**dir."
#:     "The capital of Turkey is **Ankara**."
#:
#: Yəni ölçülən şey format bağlılığı deyil, söz çoxluğu idi, və "iddia
#: promptdan asılıdır" kimi yanlış nəticə çıxardı. Təlimat geri qaytarıldı;
#: indi variant `default`-dan YALNIZ etiketlərin olmaması ilə fərqlənir.
PLAIN_PROMPT_TEMPLATES = {
    "az": (
        "Suala qısa cavab ver. Yalnız cavabı yaz.\n\n"
        "Misirin paytaxtı hansı şəhərdir?\n"
        "Qahirə\n\n"
        "Su molekulunun kimyəvi formulu nədir?\n"
        "H2O\n\n"
        "{question}\n"
    ),
    "en": (
        "Answer the question briefly. Write only the answer.\n\n"
        "What is the capital city of Egypt?\n"
        "Cairo\n\n"
        "What is the chemical formula of a water molecule?\n"
        "H2O\n\n"
        "{question}\n"
    ),
}

#: `oneshot` — nümunə sayı oxu üzrə dördüncü nöqtə.
#:
#: NİYƏ ƏLAVƏ EDİLDİ. Möhkəmlik yoxlaması üç şablon tələb edir, amma
#: `Qwen3-VL-4B-Thinking` şablonsuz `zeroshot`-da ingilis sətirlərinin
#: 42.7%-nə BOŞ cavab verir və həmin şərait ölçmə sayılmır. Nəticədə cüt
#: fərqi yalnız iki şablona söykənirdi.
#:
#: DİAQNOZ ƏVVƏLCƏ SƏHV QOYULDU və bunu yazmağa dəyər: struktur işarəsinin
#: (`Cavab:`) çatışmadığını düşündüm, halbuki `zeroshot`-da o, ARTIQ VAR.
#: İşləyən iki şablonun ortaq cəhəti NÜMUNƏ olmasıdır; `zeroshot`-da isə
#: nümunə yoxdur. Deməli çökmə nümunəsizlikdəndir, etiketsizlikdən yox.
#:
#: Ona görə dördüncü şablon nümunə sayı oxunda qurulur:
#:
#:     default   iki nümunə, etiketli
#:     oneshot   BİR nümunə, etiketli
#:     plain     iki nümunə, etiketsiz
#:     zeroshot  nümunə yoxdur
#:
#: Bu, "işləyən şablon seçmək" deyil: `zeroshot` silinmir, hesabatda sınıq
#: şərait kimi qalır və kənarlaşdırma səbəbi ilə birlikdə göstərilir.
ONESHOT_PROMPT_TEMPLATES = {
    "az": (
        "Suala qısa cavab ver. Yalnız cavabı yaz — cümlə qurma, izahat vermə.\n\n"
        "Sual: Misirin paytaxtı hansı şəhərdir?\n"
        "Cavab: Qahirə\n\n"
        "Sual: {question}\n"
        "Cavab:"
    ),
    "en": (
        "Answer the question briefly. Write only the answer — no sentence, "
        "no explanation.\n\n"
        "Question: What is the capital city of Egypt?\n"
        "Answer: Cairo\n\n"
        "Question: {question}\n"
        "Answer:"
    ),
}

PROMPT_STYLES = {
    "default": PROMPT_TEMPLATES,
    "script": SCRIPT_PROMPT_TEMPLATES,
    "zeroshot": ZEROSHOT_PROMPT_TEMPLATES,
    "plain": PLAIN_PROMPT_TEMPLATES,
    "oneshot": ONESHOT_PROMPT_TEMPLATES,
}

QUESTION_FIELD = {"az": "question_az", "en": "question_en"}


@dataclass(frozen=True)
class GenerationConfig:
    """Generasiya parametrləri — xam fayla yazılır ki, qaçış təkrarlana bilsin."""

    max_new_tokens: int = 32
    do_sample: bool = False  # greedy: reproduksiya tələbi
    temperature: float = 0.0
    seed: int = 0
    batch_size: int = 8


# --------------------------------------------------------------------------
# Backend-lər
# --------------------------------------------------------------------------


class Backend(Protocol):
    """Model çağırışının minimal interfeysi."""

    name: str

    def generate(self, prompts: Sequence[str]) -> list[str]:
        """Hər prompt üçün bir xam mətn cavabı."""
        ...


@dataclass
class EchoBackend:
    """Sınaq backend-i: həmişə boş cavab qaytarır.

    Boru xəttinin boş cavabı düzgün emal etdiyini yoxlamaq üçündür.
    """

    name: str = "echo"

    def generate(self, prompts: Sequence[str]) -> list[str]:
        return ["" for _ in prompts]


@dataclass
class OracleBackend:
    """YALNIZ SINAQ ÜÇÜN: etalon cavabı verilmiş ehtimalla qaytarır.

    Boru xəttini uçdan-uca (dataset -> qaçış -> metrik) real model yükləmədən
    yoxlamağa imkan verir. Real qiymətləndirmədə istifadəsi mənasızdır və CLI
    onu `--allow-oracle` bayrağı olmadan işə salmır.
    """

    golds: dict[str, str]
    accuracy: float = 0.6
    seed: int = 0
    name: str = "oracle"
    _order: list[str] = field(default_factory=list, init=False)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._order = list(self.golds)
        # Generator BİR DƏFƏ qurulur. Hər `generate_for` çağırışında yenidən
        # toxumlansaydı, qaçış partiyalara bölündüyü üçün eyni təsadüfi ardıcıllıq
        # hər partiyada təkrarlanardı və faktiki dəqiqlik `accuracy` parametrindən
        # kənara çıxardı — sınaq rəqəmləri yanıldıcı olardı.
        self._rng = random.Random(self.seed)

    def generate(self, prompts: Sequence[str]) -> list[str]:
        raise NotImplementedError("OracleBackend `generate_for` metodunu istifadə edir")

    def generate_for(self, ids: Sequence[str]) -> list[str]:
        responses: list[str] = []
        for record_id in ids:
            gold = self.golds.get(record_id, "")
            if self._rng.random() < self.accuracy:
                responses.append(gold)
            else:
                # Başqa bir sətrin cavabı — realistik "səhv amma məqbul" cavab.
                other = self._rng.choice(self._order)
                responses.append(self.golds.get(other, ""))
        return responses


def _align_bitsandbytes_cuda_version() -> str | None:
    """`bitsandbytes`-i mövcud CUDA kitabxanası ilə uyğunlaşdırır.

    `bitsandbytes` yüklənəcək DLL-i PyTorch-un CUDA versiyasına görə seçir.
    PyTorch cu132-dirsə, `libbitsandbytes_cuda132.dll` axtarır — paketdə isə
    yalnız cuda130-a qədər fayl var və import `RuntimeError` ilə çökür.

    CUDA-nın kiçik versiyaları geriyə uyğundur, ona görə mövcud olan ən yüksək
    variantı `BNB_CUDA_VERSION` dəyişəni ilə göstərmək kifayətdir. Dəyişən
    əvvəlcədən təyin olunubsa, ona toxunulmur.

    Qaytarır: seçilmiş versiya (məs. "130") və ya `None` (müdaxilə lazım deyil).
    """
    import os

    if os.environ.get("BNB_CUDA_VERSION"):
        return None

    # PyTorch opsional asılılıqdır (yalnız `--backend transformers` üçün lazımdır).
    # Quraşdırılmayıbsa, uyğunlaşdırılacaq bir şey yoxdur.
    try:
        import torch
    except ImportError:
        return None

    cuda_version = (torch.version.cuda or "").replace(".", "")
    if not cuda_version:
        return None

    # DİQQƏT: `bitsandbytes` burada IMPORT EDİLMİR. İmport native kitabxananı
    # dərhal yükləyir və səhv versiya ilə çökür — bundan sonra `BNB_CUDA_VERSION`
    # təyin etmək gec olur. `find_spec` modulu icra etmədən yerini tapır.
    import importlib.util

    spec = importlib.util.find_spec("bitsandbytes")
    if spec is None or not spec.origin:
        return None

    package_dir = Path(spec.origin).parent
    if (package_dir / f"libbitsandbytes_cuda{cuda_version}.dll").exists():
        return None  # dəqiq uyğunluq var

    available = sorted(
        int(p.stem.removeprefix("libbitsandbytes_cuda"))
        for p in package_dir.glob("libbitsandbytes_cuda*.dll")
        if p.stem.removeprefix("libbitsandbytes_cuda").isdigit()
    )
    usable = [v for v in available if v <= int(cuda_version)]
    if not usable:
        return None

    os.environ["BNB_CUDA_VERSION"] = str(usable[-1])
    return str(usable[-1])


class TransformersBackend:
    """HuggingFace `transformers` ilə lokal model.

    `torch` və `transformers` yalnız bu backend seçiləndə import olunur — sınaq
    backend-ləri ilə işləyəndə ağır asılılıqlar tələb olunmasın.
    """

    def __init__(
        self,
        model_id: str,
        config: GenerationConfig,
        load_in_4bit: bool = False,
        device: str | None = None,
        trust_remote_code: bool = False,
        use_chat_template: bool = True,
    ) -> None:
        import torch
        from transformers import AutoTokenizer

        self.name = model_id
        self.config = config
        # Şablonun tətbiqini SÖNDÜRMƏK imkanı cüt müqayisələri üçün məcburidir.
        #
        # `Mistral-7B-v0.1`-in chat şablonu YOXDUR, ondan köklənmiş
        # `Trendyol-LLM-7b-base`-in isə VAR (Mistral-ın `[INST]` formatı).
        # Nəticədə eyni prompt iki üzvə fərqli formada çatırdı: biri xam
        # few-shot mətn alırdı və 36.9% yığırdı, digəri `[INST]` içinə salınmış
        # mətn alırdı, həmin formatı tanımırdı (o, təlimat modeli deyil, davam
        # etdirilmiş ön-təlimdir) və 0.0% yığırdı.
        #
        # Belə cütdə ölçülən şey fine-tune-un təsiri yox, şablon fərqi olur.
        self.use_chat_template = use_chat_template
        self._torch = torch

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id, padding_side="left", trust_remote_code=trust_remote_code
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        kwargs: dict[str, Any] = {"dtype": "auto", "device_map": device or "auto"}
        if load_in_4bit:
            aligned = _align_bitsandbytes_cuda_version()
            if aligned:
                print(f"  bitsandbytes CUDA {aligned} kitabxanasına yönləndirildi")

            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                # CPU-ya daşınmaya icazə. Bu olmadan `device_map="auto"` modeli
                # tam GPU-ya yerləşdirə bilməyəndə ValueError atır və qaçış
                # ümumiyyətlə başlamır — 8 GB kartda 8B+ modellər məhz buna
                # ilişir.
                #
                # Sürətə demək olar təsir etmir: biz yalnız MƏTN sualı veririk,
                # ona görə görmə və audio qüllələri heç vaxt işə düşmür. CPU-ya
                # düşən məhz onlardır; dil qatları GPU-da qalır.
                llm_int8_enable_fp32_cpu_offload=True,
            )

        if trust_remote_code:
            kwargs["trust_remote_code"] = True

        self.model = self._load_model(model_id, kwargs)
        self.model.eval()

    @staticmethod
    def _load_model(model_id: str, kwargs: dict[str, Any]) -> Any:
        """Modeli yükləyir; multimodal arxitekturalar üçün geri dönüş zənciri.

        `AutoModelForCausalLM` yalnız mətn modellərini tanıyır. Layihənin əsas
        hook modeli `issai/Qolda-AVL-5B` isə `qwen3_vl` tipindədir (mətn gövdəsi
        + görmə + audio enkoderləri) və o siniflə yüklənmir. Mətn-only sual
        verdiyimiz üçün multimodal başlıq işimizə mane olmur — sadəcə düzgün
        `Auto...` sinfi lazımdır.

        Sıra: mətn -> mətn+şəkil -> ümumi. Hər biri ayrıca sınanır, çünki
        `transformers` versiyaları arasında sinif adları dəyişir.

        DİQQƏT — yalnız istisnaya baxmaq YETƏRLİ DEYİL. `AutoModelForCausalLM`
        `qwen3_vl` modelləri üçün xəta vermir, amma dil başlığı olmayan çılpaq
        gövdəni (`Qwen3VLModel`) qaytarır. Belə obyektin `generate` metodu yoxdur
        və qaçış 96 sətrin hamısında çökür — özü də çıxış kodu 0 ilə, yəni
        səssizcə. Ona görə qaytarılan obyektin YARARLILIĞI da yoxlanılır.
        """
        import transformers

        candidates = [
            "AutoModelForCausalLM",
            "AutoModelForImageTextToText",
            "AutoModelForVision2Seq",
            "AutoModel",
        ]
        errors: list[str] = []
        for class_name in candidates:
            auto_class = getattr(transformers, class_name, None)
            if auto_class is None:
                continue
            try:
                model = auto_class.from_pretrained(model_id, **kwargs)
            except (ValueError, KeyError, OSError, TypeError) as exc:
                errors.append(f"{class_name}: {type(exc).__name__}: {exc}")
                continue

            if not hasattr(model, "generate"):
                errors.append(
                    f"{class_name}: {type(model).__name__} obyektində `generate` yoxdur"
                )
                del model
                continue
            return model

        raise RuntimeError(
            f"`{model_id}` heç bir Auto sinfi ilə yüklənmədi:\n  " + "\n  ".join(errors)
        )

    def describe(self) -> dict[str, Any]:
        """Sətirlərə yazılan backend məlumatı: chat şablonunun VƏZİYYƏTİ.

        NİYƏ MƏHZ BU. Şablonun tətbiq olunub-olunmadığı çıxış faylından
        GÖRÜNMÜRDÜ: `prompt` sahəsi şablondan ƏVVƏLKİ mətni saxlayır. Ona görə
        cüt daxilindəki asimmetriya (baza modelində şablon var, köklənmişdə
        yox) fayllara baxaraq tapıla bilmirdi.

        Bu, nəzəri narahatlıq deyil. Layihədə eyni səhv İKİ DƏFƏ baş verib:
        `Mistral-7B-v0.1 -> Trendyol` cütündə simptom kəskin idi (EN 0.0%) və
        tutuldu; `Qwen3-VL-4B-Thinking -> Qolda` və `Qwen3.5-4B-Base ->
        ...-Kazakh` cütlərində isə səssiz idi və uzun müddət keçdi.

        İki sahə ayrıdır və hər ikisi lazımdır: istifadəçi şablonu İSTƏYİBMİ
        (`requested`) və modelin şablonu VARMI (`available`). Tətbiq yalnız
        hər ikisi doğru olanda baş verir.
        """
        template = getattr(self.tokenizer, "chat_template", None)
        return {
            "chat_template_requested": self.use_chat_template,
            "chat_template_available": bool(template),
            "chat_template_applied": bool(self.use_chat_template and template),
            "model_revision": self._revision(),
        }

    def _revision(self) -> str | None:
        """Modelin işlədilən commit hash-ı, tapıla bilirsə.

        NİYƏ LAZIMDIR. HuggingFace-də çəkilər dəyişə bilər və bəzi model
        kartları bunu açıq yazır (`RuadaptQwen3-4B-Hybrid`: "веса модели могут
        обновляться"). Model adı ilə qaçış təkrarlanmaya bilər; hash ilə
        təkrarlanır. Rəqəm çıxa bilməsə `None` yazılır, uydurulmur.
        """
        # `getattr(self, ...)`: `describe()` model yüklənmədən də çağırıla
        # bilir (testlərdə və şablon yoxlamasında). Revizyon tapılmasa `None`
        # yazılır; sahənin olmaması qaçışı dayandırmamalıdır.
        for source in (
            getattr(getattr(self, "model", None), "config", None),
            getattr(getattr(self, "tokenizer", None), "init_kwargs", None),
        ):
            revision = None
            if isinstance(source, dict):
                revision = source.get("_commit_hash") or source.get("revision")
            elif source is not None:
                revision = getattr(source, "_commit_hash", None)
            if isinstance(revision, str) and revision:
                return revision
        return None

    def _apply_chat_template(self, prompt: str) -> str:
        """Təlimat modelləri öz chat şablonlarını gözləyir; baza modelləri yox.

        `enable_thinking=False` — Qwen3 kimi hibrid düşünmə modelləri üçün
        VACİBDİR. Onların chat şablonu susmadan düşünmə rejimini açır və model
        cavabdan əvvəl uzun `<think>...</think>` bloku yazır. Qısa cavab
        tapşırığında bu, fəlakətdir: 24-32 token limitində generasiya düşünmə
        blokunun ortasında kəsilir və model ƏSL CAVABA HEÇ VAXT ÇATMIR — bütün
        sətirlər sıfır bal alır və rəqəm modelin biliyini deyil, çıxış formatını
        ölçür.

        Parametri dəstəkləməyən şablonlar onu sadəcə nəzərə almır; bəziləri isə
        xəta verir, ona görə geri dönüş yolu saxlanılır.
        """
        if not self.use_chat_template:
            return prompt
        template = getattr(self.tokenizer, "chat_template", None)
        if not template:
            return prompt

        messages = [{"role": "user", "content": prompt}]
        try:
            rendered = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except (TypeError, ValueError):
            rendered = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        return self._close_forced_thinking(rendered)

    @staticmethod
    def _close_forced_thinking(rendered: str) -> str:
        """Şablon açıq `<think>` teqi ilə bitirsə, onu dərhal bağlayır.

        Bəzi şablonlar `enable_thinking` parametrini ÜMUMİYYƏTLƏ tanımır və
        generasiya promptunun sonuna `<think>` teqini sabit yazır — layihənin
        hook modeli `issai/Qolda-AVL-5B` məhz belədir. O halda model həmişə
        mühakimə ilə başlayır və qısa cavab limitində əsl cavaba çatmır: 96
        sətrin 96-sı kəsilmiş mühakimə oldu, yəni bal sıfır.

        Teqi promptun özündə bağlamaq modeli birbaşa cavab rejiminə salır.
        Bu, təkcə texniki rahatlıq deyil, MÜQAYİSƏNİN ŞƏRTİDİR: digər modellər
        `enable_thinking=False` ilə işləyir, biri mühakimə edib digərləri
        etməsəydi, ölçülən fərq modelin biliyindən yox, rejim fərqindən gələrdi.
        """
        if rendered.rstrip().endswith("<think>"):
            return rendered.rstrip() + "\n</think>\n\n"
        return rendered

    def generate(self, prompts: Sequence[str]) -> list[str]:
        torch = self._torch
        torch.manual_seed(self.config.seed)

        texts = [self._apply_chat_template(p) for p in prompts]
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True).to(
            self.model.device
        )

        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                do_sample=self.config.do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        # Yalnız YENİ tokenlər — prompt cavabın içinə qarışmasın.
        generated = output[:, inputs["input_ids"].shape[1] :]
        return [
            text.strip()
            for text in self.tokenizer.batch_decode(generated, skip_special_tokens=True)
        ]


# --------------------------------------------------------------------------
# Qaçış
# --------------------------------------------------------------------------


def build_prompt(
    record: dict[str, Any], language: str, style: str = "default"
) -> str:
    """Sətir, dil və prompt üslubu üçün promptu qurur."""
    if language not in LANGUAGES:
        raise ValueError(f"naməlum dil: {language!r}; gözlənilən: {LANGUAGES}")
    if style not in PROMPT_STYLES:
        raise ValueError(
            f"naməlum prompt üslubu: {style!r}; gözlənilən: {sorted(PROMPT_STYLES)}"
        )
    question = record[QUESTION_FIELD[language]]
    return PROMPT_STYLES[style][language].format(question=question)


def completed_ids(path: Path) -> set[str]:
    """Artıq yazılmış `id`-lər — yarımçıq qaçışın davamı üçün."""
    if not path.exists():
        return set()
    done: set[str] = set()
    for _, record in load_jsonl(path):
        if isinstance(record, dict) and isinstance(record.get("id"), str):
            done.add(record["id"])
    return done


def _batches(items: Sequence[Any], size: int) -> Iterator[Sequence[Any]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def run_evaluation(
    records: Sequence[dict[str, Any]],
    backend: Backend,
    language: str,
    output_path: Path,
    config: GenerationConfig,
    resume: bool = True,
    progress: bool = True,
    prompt_style: str = "default",
) -> int:
    """Modeli sətirlər üzərində işlədib xam cavabları JSONL-ə əlavə edir.

    Fayla `append` rejimində və hər partiyadan sonra yazılır — qaçış kəsilsə,
    o ana qədərki iş diskdə qalır.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    done = completed_ids(output_path) if resume else set()
    pending = [r for r in records if r["id"] not in done]

    if not pending:
        if progress:
            print(f"  hamısı hazırdır ({len(done)} sətir) — atlanır")
        return 0

    if progress and done:
        print(f"  {len(done)} sətir artıq var, {len(pending)} qalıb")

    environment = {
        "python": platform.python_version(),
        "platform": platform.platform(),
    }

    # Backend özü haqqında əlavə məlumat verirsə, hər sətrə yazılır. API
    # backend-ləri üçün bu VACİBDİR: faktiki model versiyası və determinizm
    # sinfi rəqəmlə birlikdə saxlanmasa, altı ay sonra sətrin nəyi ölçdüyü
    # bilinməz. Lokal backend-lərdə metod yoxdur və sahə də yazılmır.
    #
    # Metod hər partiyadan SONRA çağırılır, əvvəl yox: faktiki model versiyası
    # yalnız birinci cavab gələndən sonra məlum olur.
    describe = getattr(backend, "describe", None)
    if not callable(describe):
        describe = None

    written = 0
    with open(output_path, "a", encoding="utf-8", newline="\n") as handle:
        for batch in _batches(pending, config.batch_size):
            prompts = [build_prompt(r, language, prompt_style) for r in batch]

            started = time.perf_counter()
            if isinstance(backend, OracleBackend):
                responses = backend.generate_for([r["id"] for r in batch])
            else:
                responses = backend.generate(prompts)
            elapsed = time.perf_counter() - started

            if len(responses) != len(batch):
                raise RuntimeError(
                    f"backend {len(batch)} promptа {len(responses)} cavab qaytardı"
                )

            backend_meta = describe() if describe else None

            # Uğursuz çağırışlar fayla YAZILMIR — yazılsaydı, `completed_ids`
            # onları hazır sayardı və növbəti qaçış həmin sualları atlayardı.
            # Maska verməyən backend-lərdə (lokal modellər) bütün sətirlər
            # uğurlu sayılır.
            failed = getattr(backend, "last_failed", None) or [False] * len(batch)

            for record, prompt, response, is_failed in zip(
                batch, prompts, responses, failed, strict=True
            ):
                if is_failed:
                    continue
                row: dict[str, Any] = {
                    "id": record["id"],
                    "model": backend.name,
                    "language": language,
                    "prompt_style": prompt_style,
                    "prompt": prompt,
                    "raw_response": response,
                    "generation": asdict(config),
                    "environment": environment,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                if backend_meta:
                    row["backend"] = backend_meta
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            written += sum(1 for is_failed in failed if not is_failed)

            if progress:
                rate = len(batch) / elapsed if elapsed > 0 else float("inf")
                print(
                    f"  {written}/{len(pending)}  ({rate:.1f} sual/san)",
                    flush=True,
                )

    return written


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def default_output_path(
    model_id: str, language: str, root: Path, prompt_style: str = "default"
) -> Path:
    """`results/raw_outputs/<model>__<dil>[__<üslub>].jsonl`.

    Prompt üslubu fayl adına yalnız standartdan fərqli olduqda əlavə olunur —
    əks halda mövcud qaçış faylları adını dəyişər və `--resume` işləməzdi.
    """
    safe = model_id.replace("/", "__").replace(":", "_")
    suffix = "" if prompt_style == "default" else f"__{prompt_style}"
    return root / f"{safe}__{language}{suffix}.jsonl"


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="run_eval", description="Modelləri işə salıb xam cavabları yığır"
    )
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--model", required=True, help="HF model id və ya sınaq backend adı")
    parser.add_argument("--language", choices=LANGUAGES, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None, help="ilk N sətir (sınaq üçün)")
    parser.add_argument("--max-new-tokens", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--prompt-style",
        choices=sorted(PROMPT_STYLES),
        default="default",
        help="`script`: cavabın latın əlifbası ilə yazılmasını açıq tələb edir",
    )
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="modelin öz kodunu icra etməyə icazə (Qolda kimi xüsusi arxitekturalar)",
    )
    parser.add_argument(
        "--no-chat-template",
        action="store_true",
        help="chat şablonunu tətbiq etmə (baza modelləri və cüt müqayisələri)",
    )
    parser.add_argument("--device", default=None)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--backend",
        choices=("transformers", "echo", "oracle", "api"),
        default="transformers",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="api backend: paralel sorğu sayı (rate limit-ə görə ehtiyatlı seç)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=(
            "api backend: OpenAI-uyğun üçüncü tərəf endpoint-i "
            "(GLM, DeepSeek, OpenRouter, Groq...)"
        ),
    )
    parser.add_argument(
        "--no-reasoning",
        action="store_true",
        help=(
            "hibrid mühakimə modellərində düşünməni söndür (OpenRouter). "
            "Müqayisə üçün lazımdır: lokal Thinking modeli də söndürülmüş "
            "qaçır, açıq qalsa 32 tokenlik büdcə mühakiməyə gedir və cavab "
            "boş çıxır."
        ),
    )
    parser.add_argument(
        "--api-key-env",
        default=None,
        help="api backend: açarın oxunacağı mühit dəyişəni (məs. ZAI_API_KEY)",
    )
    parser.add_argument("--oracle-accuracy", type=float, default=0.6)
    parser.add_argument(
        "--allow-oracle",
        action="store_true",
        help="oracle backend-inə icazə (YALNIZ boru xəttinin sınağı üçün)",
    )
    args = parser.parse_args(argv)

    records = [r for _, r in load_jsonl(args.dataset) if isinstance(r, dict)]
    if not records:
        print(
            f"Dataset boşdur: {args.dataset}\n"
            "Əvvəlcə `python -m src.review ...` ilə sətirləri təsdiqlə, "
            "sonra `python -m src.build_dataset build` işlət.",
            file=sys.stderr,
        )
        return 1
    if args.limit:
        records = records[: args.limit]

    config = GenerationConfig(
        max_new_tokens=args.max_new_tokens,
        seed=args.seed,
        batch_size=args.batch_size,
    )

    # Sınaq backend-lərində də `--model` dəyəri ad kimi işlənir. Əks halda
    # bütün sınaq qaçışları eyni ad altında yazılır və `analyze.py` onları BİR
    # qaçış kimi birləşdirir — iki modeli müqayisə etmək mümkün olmur.
    backend: Backend
    if args.backend == "echo":
        backend = EchoBackend(name=args.model)
    elif args.backend == "oracle":
        if not args.allow_oracle:
            print(
                "oracle backend etalon cavabları oxuyur — real nəticə vermir.\n"
                "Boru xəttini sınayırsansa `--allow-oracle` əlavə et.",
                file=sys.stderr,
            )
            return 1
        backend = OracleBackend(
            golds={r["id"]: r["answer" if args.language == "az" else "answer_en"]
                   for r in records},
            accuracy=args.oracle_accuracy,
            seed=args.seed,
            name=args.model,
        )
    elif args.backend == "api":
        from src.backends_api import APIBackend

        try:
            backend = APIBackend.from_reference(
                args.model,
                max_tokens=args.max_new_tokens,
                max_workers=args.max_workers,
                base_url=args.base_url,
                api_key_env=args.api_key_env,
                disable_reasoning=args.no_reasoning,
            )
        except (ValueError, RuntimeError) as exc:
            print(exc, file=sys.stderr)
            return 1
    else:
        backend = TransformersBackend(
            args.model,
            config,
            load_in_4bit=args.load_in_4bit,
            device=args.device,
            trust_remote_code=args.trust_remote_code,
            use_chat_template=not args.no_chat_template,
        )

    output = args.out or default_output_path(
        backend.name, args.language, args.out_dir, args.prompt_style
    )
    print(f"{backend.name}  [{args.language}]  {len(records)} sətir -> {output}")

    # Kvota tükənməsi XƏTA DEYİL, dayanma səbəbidir: o ana qədərki sətirlər
    # diskdədir və kvota bərpa olunanda `--resume` davam etdirir. Ona görə
    # traceback yerinə aydın mesaj verilir və xülasə yenə yazılır.
    aborted = False
    try:
        written = run_evaluation(
            records,
            backend,
            args.language,
            output,
            config,
            resume=not args.no_resume,
            prompt_style=args.prompt_style,
        )
        print(f"Bitdi: {written} yeni cavab yazıldı.")
    except Exception as exc:
        from src.backends_api import QuotaExhausted

        if not isinstance(exc, QuotaExhausted):
            raise
        aborted = True
        print(f"\nDAYANDIRILDI: {exc}", file=sys.stderr)

    # API qaçışlarında xərc və sızma xülasəsi xam faylın yanına yazılır.
    # Ayrıca fayl, çünki xülasə bütün qaçışa aiddir, tək sətrə yox — və
    # `--resume` ilə davam edən qaçış onu üstündən yazır, birləşdirmir.
    summarize = getattr(backend, "summary", None)
    if callable(summarize):
        summary = summarize()
        meta_path = output.with_suffix(".meta.json")
        meta_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        usage = summary["usage"]
        cost = usage["cost_usd"]
        cost_text = f"${cost:.2f}" if cost is not None else "qiymət cədvəldə yoxdur"
        print(
            f"  {usage['calls']} çağırış, {usage['input_tokens']}+"
            f"{usage['output_tokens']} token, {cost_text}"
        )
        if usage["failures"]:
            print(
                f"  DİQQƏT: {usage['failures']} çağırış uğursuz oldu və fayla "
                f"yazılmadı. Eyni əmri yenidən işlət — yalnız çatışmayan sətirlər "
                f"soruşulacaq."
            )
        # Neçə sətrin hazır olduğunu göstər — kvota ilə işləyəndə ən vacib rəqəm
        # budur, çünki qaçış bir neçə günə yayıla bilər.
        done = len(completed_ids(output))
        print(f"  Fayl: {done}/{len(records)} sətir hazırdır")
        if summary["leaked_internal_tags"]:
            print(
                f"  DİQQƏT: {summary['leaked_internal_tags']} cavabda daxili teq "
                f"sızıntısı var — bu modelin rəqəmi əl ilə yoxlanmalıdır."
            )

    return 2 if aborted else 0


if __name__ == "__main__":
    raise SystemExit(main())
