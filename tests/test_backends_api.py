"""API backend testləri.

Heç bir real API çağırışı edilmir - adapterlər saxta obyektlərlə əvəz olunur.
Səbəb: testlər açar tələb etməməli, pul xərcləməməli və şəbəkəsiz işləməlidir.
Yoxlanan şey adapterin daxili məntiqi deyil, `APIBackend`-in müqaviləsidir:
sıra, uğursuzluq maskası, istifadə sayğacı və metadata.
"""

from __future__ import annotations

import json

import pytest

from src.backends_api import (
    PRICES,
    APIBackend,
    Usage,
    leaked_tag_count,
    parse_model_ref,
)
from src.run_eval import GenerationConfig, run_evaluation


class FakeAdapter:
    """Verilmiş cavabları sıra ilə qaytaran adapter; bəziləri xəta atır."""

    provider = "fake"

    def __init__(self, responses: dict[str, str | Exception], model: str = "fake-v1"):
        self.responses = responses
        self.model = model
        self.calls: list[str] = []

    def complete(self, prompt: str, max_tokens: int) -> tuple[str, int, int, str]:
        self.calls.append(prompt)
        value = self.responses[prompt]
        if isinstance(value, Exception):
            raise value
        return value, 10, 5, self.model


def make_backend(responses, **kwargs) -> APIBackend:
    return APIBackend(
        name="anthropic:claude-opus-5",
        adapter=FakeAdapter(responses),
        max_tokens=32,
        **kwargs,
    )


# --------------------------------------------------------------------------
# parse_model_ref
# --------------------------------------------------------------------------


def test_parse_model_ref_splits_provider_and_model():
    assert parse_model_ref("anthropic:claude-opus-5") == (
        "anthropic",
        "claude-opus-5",
    )


def test_parse_model_ref_keeps_colons_inside_model_id():
    # Model adında ikinci `:` ola bilər; yalnız BİRİNCİSİ ayırıcıdır.
    assert parse_model_ref("openai:ft:gpt-4o:acme") == ("openai", "ft:gpt-4o:acme")


@pytest.mark.parametrize("bad", ["claude-opus-5", "anthropic:", ":model", ""])
def test_parse_model_ref_rejects_missing_provider(bad):
    with pytest.raises(ValueError):
        parse_model_ref(bad)


def test_parse_model_ref_rejects_unknown_provider():
    with pytest.raises(ValueError, match="naməlum provayder"):
        parse_model_ref("deepmind:gemini")


# --------------------------------------------------------------------------
# Sıra
# --------------------------------------------------------------------------


def test_generate_preserves_order_under_concurrency():
    """Paralel icra SIRANI pozmamalıdır.

    Bu, sadəcə səliqə məsələsi deyil: `run_evaluation` cavabları sətirlərlə
    mövqeyə görə birləşdirir. Sıra pozulsa, cavablar səhv suallara yazılar və
    heç bir xəta görünməz - bütün nəticə səssizcə yanlış olar.
    """
    prompts = [f"sual {i}" for i in range(20)]
    backend = make_backend({p: f"cavab {i}" for i, p in enumerate(prompts)},
                           max_workers=8)

    assert backend.generate(prompts) == [f"cavab {i}" for i in range(20)]


# --------------------------------------------------------------------------
# Uğursuzluq
# --------------------------------------------------------------------------


def test_failed_call_is_marked_and_counted():
    prompts = ["a", "b", "c"]
    backend = make_backend({"a": "A", "b": RuntimeError("429"), "c": "C"})

    assert backend.generate(prompts) == ["A", "", "C"]
    assert backend.last_failed == [False, True, False]
    assert backend.usage.failures == 1
    assert backend.usage.calls == 2  # uğursuz çağırış token sayğacına düşmür


def test_failed_rows_are_not_written_so_resume_retries_them(tmp_path):
    """Uğursuz sətir fayla düşməməlidir.

    Yazılsaydı, `completed_ids` onu hazır sayar və növbəti qaçış həmin sualı
    ATLAYARDI - bir 429 xətası datasetdə daimi boşluğa çevrilərdi.
    """
    records = [
        {"id": "az-001", "question_az": "birinci", "question_en": "first"},
        {"id": "az-002", "question_az": "ikinci", "question_en": "second"},
    ]
    out = tmp_path / "run.jsonl"

    # Birinci qaçış: ikinci sual çökür.
    first = APIBackend(
        name="anthropic:claude-opus-5",
        adapter=FakeAdapter({}),
        max_tokens=32,
    )
    first.adapter.responses = {
        p: (RuntimeError("boom") if "ikinci" in p else "Bakı")
        for p in (
            _prompt_for(records[0]),
            _prompt_for(records[1]),
        )
    }
    run_evaluation(records, first, "az", out, GenerationConfig(batch_size=8))

    written = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [row["id"] for row in written] == ["az-001"]

    # İkinci qaçış: yalnız çatışmayan sətir soruşulur.
    second = APIBackend(
        name="anthropic:claude-opus-5",
        adapter=FakeAdapter({_prompt_for(records[1]): "Gəncə"}),
        max_tokens=32,
    )
    run_evaluation(records, second, "az", out, GenerationConfig(batch_size=8))

    assert len(second.adapter.calls) == 1
    written = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [row["id"] for row in written] == ["az-001", "az-002"]


def _prompt_for(record: dict) -> str:
    from src.run_eval import build_prompt

    return build_prompt(record, "az")


# --------------------------------------------------------------------------
# Metadata
# --------------------------------------------------------------------------


def test_describe_records_resolved_model_after_first_call():
    backend = make_backend({"a": "A"})

    # Çağırışdan əvvəl faktiki versiya məlum deyil.
    assert backend.describe()["resolved_model"] is None

    backend.generate(["a"])
    assert backend.describe()["resolved_model"] == "fake-v1"


def test_describe_marks_api_runs_as_non_deterministic():
    """API sətirləri lokal sətirlərlə eyni etibarlılıq sinfində deyil.

    Lokal qaçış `do_sample=False` + sabit seed ilə təkrarlanır; API qaçışı
    təkrarlanmır (Claude 5 ailəsi `temperature` parametrini ümumiyyətlə qəbul
    etmir). Fərq hər sətrə yazılmalıdır, yoxsa cədvəldə itir.
    """
    meta = make_backend({}).describe()
    assert meta["determinism"] == "best-effort"
    assert meta["thinking"] == "disabled"


def test_describe_records_third_party_endpoint():
    """Üçüncü tərəf endpoint rəqəmlə birlikdə saxlanılmalıdır.

    Eyni model adı fərqli hostlarda fərqli versiya və ya kvantlaşdırma ola
    bilər (birinci tərəf Z.ai vs OpenRouter). Endpoint yazılmasa, rəqəmin
    hardan gəldiyi bilinməz.
    """
    backend = make_backend({}, base_url="https://api.z.ai/api/paas/v4")
    assert backend.describe()["base_url"] == "https://api.z.ai/api/paas/v4"


def test_describe_omits_base_url_for_first_party():
    assert "base_url" not in make_backend({}).describe()


def test_backend_metadata_lands_in_every_row(tmp_path):
    records = [{"id": "az-001", "question_az": "sual", "question_en": "q"}]
    out = tmp_path / "run.jsonl"
    backend = make_backend({_prompt_for(records[0]): "Bakı"})

    run_evaluation(records, backend, "az", out, GenerationConfig(batch_size=8))

    row = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert row["backend"]["provider"] == "fake"
    assert row["backend"]["resolved_model"] == "fake-v1"


def test_local_backends_write_no_backend_field(tmp_path):
    """`describe` metodu olmayan backend sətrə əlavə sahə yazmamalıdır.

    v1-də yığılmış xam fayllarla sxem uyğunluğu qorunur.
    """
    from src.run_eval import EchoBackend

    records = [{"id": "az-001", "question_az": "sual", "question_en": "q"}]
    out = tmp_path / "run.jsonl"

    run_evaluation(records, EchoBackend(name="echo"), "az", out, GenerationConfig())

    row = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert "backend" not in row


# --------------------------------------------------------------------------
# Sızan teqlər
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    ["<thinking>bir az düşünüm", "</think>", "<SCRATCHPAD>", "cavab <think> Bakı"],
)
def test_leaked_tag_detected(text):
    assert leaked_tag_count([text]) == 1


@pytest.mark.parametrize("text", ["Bakı", "", "2 < 3 və 5 > 4", "thinking haqqında"])
def test_clean_answer_not_flagged(text):
    assert leaked_tag_count([text]) == 0


def test_leaked_tags_accumulate_across_batches():
    backend = make_backend({"a": "<thinking>x", "b": "Bakı", "c": "</think>"})
    backend.generate(["a", "b"])
    backend.generate(["c"])
    assert backend.leaked_tags == 2


def test_failed_call_is_not_counted_as_leak():
    """Uğursuz çağırışın boş cavabı sızıntı kimi sayılmamalıdır."""
    backend = make_backend({"a": RuntimeError("boom")})
    backend.generate(["a"])
    assert backend.leaked_tags == 0


# --------------------------------------------------------------------------
# Xərc
# --------------------------------------------------------------------------


def test_cost_uses_published_rates():
    usage = Usage(calls=1, input_tokens=1_000_000, output_tokens=1_000_000)
    in_rate, out_rate = PRICES["claude-opus-5"]
    assert usage.cost_usd("claude-opus-5") == pytest.approx(in_rate + out_rate)


def test_cost_is_none_for_unpriced_model():
    """Cədvəldə olmayan model üçün uydurma rəqəm yox, `None` qaytarılır."""
    usage = Usage(calls=1, input_tokens=1000, output_tokens=1000)
    assert usage.cost_usd("gpt-nonexistent") is None
    # Tokenlər yenə də saxlanılır ki, qiymət sonra kənarda hesablana bilsin.
    assert usage.as_dict("gpt-nonexistent")["input_tokens"] == 1000


# --------------------------------------------------------------------------
# Konfiqurasiya pilləsi (Google)
# --------------------------------------------------------------------------


class VariantAdapter:
    """`GoogleAdapter`-in pillə məntiqini SDK olmadan təkrarlayan sınaq adapteri.

    Real `GoogleAdapter` `google.genai` import edir və klient qurur; testdə bu,
    şəbəkə və açar tələb edərdi. Pillə məntiqi isə SDK-dan asılı deyil, ona görə
    eyni `_VARIANTS` cədvəli üzərində ayrıca yoxlanılır.
    """

    provider = "google"
    _VARIANTS = __import__(
        "src.backends_api", fromlist=["GoogleAdapter"]
    ).GoogleAdapter._VARIANTS

    def __init__(self, accepts: str):
        self.accepts = accepts  # hansı variantdan sonra qəbul edir
        self._variant = 0
        self.attempts: list[str] = []

    variant = property(lambda self: self._VARIANTS[self._variant][0])
    thinking_state = property(
        lambda self: "disabled"
        if self._VARIANTS[self._variant][1]
        else "not-disabled (model rejected the parameter)"
    )

    def complete(self, prompt, max_tokens):
        from src.backends_api import _is_invalid_argument

        while True:
            self.attempts.append(self.variant)
            if self.variant == self.accepts:
                return "OK", 10, 5, "fake"
            exc = RuntimeError("400 INVALID_ARGUMENT")
            if not _is_invalid_argument(exc) or self._variant + 1 >= len(self._VARIANTS):
                raise exc
            self._variant += 1


def test_variant_ladder_starts_with_most_control():
    """Birinci variant düşünməni söndürən və temperaturu sıfırlayan olmalıdır."""
    from src.backends_api import GoogleAdapter

    name, sends_thinking, sends_temperature = GoogleAdapter._VARIANTS[0]
    assert sends_thinking and sends_temperature, name


def test_variant_ladder_descends_until_accepted():
    adapter = VariantAdapter(accepts="temp0")
    backend = APIBackend(name="google:gemini-3.6-flash", adapter=adapter)

    assert backend.generate(["sual"]) == ["OK"]
    assert adapter.attempts == ["thinking-off+temp0", "temp0"]


def test_describe_reports_thinking_was_not_disabled():
    """Ən vacib test: düşünmə söndürülə bilməyəndə metadata bunu deməlidir.

    Sabit `"disabled"` yazsaydıq, cədvəldə iki fərqli şəraitdə alınmış rəqəm
    eyni sətir kimi görünərdi.
    """
    adapter = VariantAdapter(accepts="temp0")
    backend = APIBackend(name="google:gemini-3.6-flash", adapter=adapter)
    backend.generate(["sual"])

    meta = backend.describe()
    assert meta["thinking"].startswith("not-disabled")
    assert meta["config_variant"] == "temp0"


def test_variant_does_not_descend_on_non_parameter_errors():
    """404 və 429 pilləni endirməməlidir.

    Endirsəydi, model tapılmadı xətası konfiqurasiya problemi kimi görünər və
    qaçış səssizcə fərqli şəraitdə davam edərdi.
    """
    from src.backends_api import _is_invalid_argument

    assert _is_invalid_argument(RuntimeError("400 INVALID_ARGUMENT"))
    assert not _is_invalid_argument(RuntimeError("404 NOT_FOUND"))
    assert not _is_invalid_argument(RuntimeError("429 RESOURCE_EXHAUSTED"))


def test_exhausted_ladder_reports_failure():
    adapter = VariantAdapter(accepts="heç-vaxt")
    backend = APIBackend(name="google:x", adapter=adapter)

    assert backend.generate(["sual"]) == [""]
    assert backend.last_failed == [True]
    assert len(adapter.attempts) == len(adapter._VARIANTS)


# --------------------------------------------------------------------------
# Kvota dayandırıcısı
# --------------------------------------------------------------------------


def test_run_aborts_after_consecutive_failures():
    """Kvota bitəndə qaçış dayanmalıdır.

    Dayanmasaydı, qalan yüzlərlə sətir yalnız 429 alar, hər biri üçün təkrar
    cəhdlər gözlənilər və ekran 2 KB-lıq xəta mətnləri ilə dolar.
    """
    from src.backends_api import QuotaExhausted

    prompts = [f"p{i}" for i in range(5)]
    backend = make_backend(
        {p: RuntimeError("429 RESOURCE_EXHAUSTED") for p in prompts},
        abort_after=3,
    )

    with pytest.raises(QuotaExhausted):
        backend.generate(prompts)


def test_success_resets_the_failure_chain():
    """Aralıq uğur zənciri qırmalıdır - tək-tük şəbəkə xətası qaçışı dayandırmasın."""
    backend = make_backend(
        {
            "a": RuntimeError("timeout"),
            "b": RuntimeError("timeout"),
            "c": "Bakı",
        },
        abort_after=3,
    )

    backend.generate(["a", "b", "c"])  # çökməməlidir
    assert backend.consecutive_failures == 0


def test_failure_chain_carries_across_batches():
    """Zəncir partiyalar arasında saxlanılmalıdır.

    Kvota tükənməsi partiya sərhədində dayanmır; sayğac sıfırlansaydı, hədd heç
    vaxt keçilməzdi və dayandırıcı işləməzdi.
    """
    from src.backends_api import QuotaExhausted

    backend = make_backend(
        {p: RuntimeError("429") for p in ["a", "b", "c", "d"]}, abort_after=4
    )

    backend.generate(["a", "b"])
    assert backend.consecutive_failures == 2
    with pytest.raises(QuotaExhausted):
        backend.generate(["c", "d"])


def test_abort_disabled_when_threshold_is_zero():
    backend = make_backend({p: RuntimeError("429") for p in ["a", "b"]}, abort_after=0)
    assert backend.generate(["a", "b"]) == ["", ""]


def test_error_message_is_shortened():
    """2 KB-lıq API xətası bir sətrə sığmalıdır."""
    from src.backends_api import _short_error

    huge = RuntimeError("429 RESOURCE_EXHAUSTED. " + "x" * 5000)
    line = _short_error(huge)
    assert len(line) < 220
    assert "RuntimeError" in line and "429" in line


def test_summary_shape_is_serializable():
    backend = make_backend({"a": "A"})
    backend.generate(["a"])
    json.dumps(backend.summary(), ensure_ascii=False)  # çökməməlidir
