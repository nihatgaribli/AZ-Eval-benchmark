"""run_eval.py üçün testlər — model yükləmədən, sınaq backend-ləri ilə."""

from __future__ import annotations

import json

import pytest

from src.build_dataset import write_jsonl
from src.run_eval import (
    EchoBackend,
    GenerationConfig,
    OracleBackend,
    build_prompt,
    completed_ids,
    default_output_path,
    run_evaluation,
)

RECORDS = [
    {
        "id": "az-001",
        "question_az": "Fransanın paytaxtı hansı şəhərdir?",
        "question_en": "What is the capital city of France?",
        "answer": "Paris",
        "answer_en": "Paris",
    },
    {
        "id": "az-002",
        "question_az": "Türkiyənin paytaxtı hansı şəhərdir?",
        "question_en": "What is the capital city of Turkey?",
        "answer": "Ankara",
        "answer_en": "Ankara",
    },
]


class CountingBackend:
    """Çağırış sayını və partiya ölçülərini qeyd edən sınaq backend-i."""

    name = "counting"

    def __init__(self) -> None:
        self.batches: list[int] = []

    def generate(self, prompts):
        self.batches.append(len(prompts))
        return [f"cavab-{i}" for i in range(len(prompts))]


def read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# --------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------


def test_prompt_uses_the_azerbaijani_question_and_instruction():
    prompt = build_prompt(RECORDS[0], "az")
    assert "Fransanın paytaxtı" in prompt
    assert "Cavab:" in prompt
    assert "Question:" not in prompt


def test_prompt_uses_the_english_question_and_instruction():
    prompt = build_prompt(RECORDS[0], "en")
    assert "capital city of France" in prompt
    assert "Answer:" in prompt
    assert "Cavab:" not in prompt


def test_prompt_language_matches_question_language():
    # İngilis təlimatı + azərbaycan sualı ölçmə şərtini korlayır: ölçdüyümüz
    # modelin bilikləri yox, təlimat izləmə qabiliyyəti olardı.
    az, en = build_prompt(RECORDS[0], "az"), build_prompt(RECORDS[0], "en")
    assert az != en
    assert RECORDS[0]["question_az"] in az
    assert RECORDS[0]["question_en"] in en


def test_unknown_language_raises():
    with pytest.raises(ValueError, match="naməlum dil"):
        build_prompt(RECORDS[0], "tr")


# --------------------------------------------------------------------------
# Xam çıxışın yazılması
# --------------------------------------------------------------------------


def test_writes_one_raw_row_per_record(tmp_path):
    out = tmp_path / "run.jsonl"
    written = run_evaluation(
        RECORDS, CountingBackend(), "az", out, GenerationConfig(), progress=False
    )
    assert written == 2
    assert len(read(out)) == 2


def test_raw_row_records_everything_needed_to_reproduce(tmp_path):
    out = tmp_path / "run.jsonl"
    config = GenerationConfig(max_new_tokens=16, seed=7)
    run_evaluation(RECORDS, CountingBackend(), "az", out, config, progress=False)

    row = read(out)[0]
    assert row["id"] == "az-001"
    assert row["model"] == "counting"
    assert row["language"] == "az"
    assert row["generation"]["seed"] == 7
    assert row["generation"]["max_new_tokens"] == 16
    assert row["generation"]["do_sample"] is False   # greedy — reproduksiya
    assert "prompt" in row and "raw_response" in row
    assert "timestamp" in row and "environment" in row


def test_no_metric_is_computed_at_run_time(tmp_path):
    # Xam fayl bal saxlamamalıdır — metrik düsturu sonra dəyişə bilər və
    # eksperimentin yenidən işlədilməsi tələb olunmamalıdır.
    out = tmp_path / "run.jsonl"
    run_evaluation(RECORDS, CountingBackend(), "az", out, GenerationConfig(), progress=False)
    row = read(out)[0]
    assert not {"em", "f1", "score", "correct"} & set(row)


def test_azerbaijani_characters_survive(tmp_path):
    out = tmp_path / "run.jsonl"
    run_evaluation(RECORDS, CountingBackend(), "az", out, GenerationConfig(), progress=False)
    assert "Türkiyənin" in out.read_text(encoding="utf-8")


def test_empty_responses_are_written_not_skipped(tmp_path):
    # Boş cavab da nəticədir — sətri atmaq balı süni yüksəldərdi.
    out = tmp_path / "run.jsonl"
    run_evaluation(RECORDS, EchoBackend(), "az", out, GenerationConfig(), progress=False)
    rows = read(out)
    assert len(rows) == 2
    assert all(row["raw_response"] == "" for row in rows)


# --------------------------------------------------------------------------
# Davam etdirmə
# --------------------------------------------------------------------------


def test_completed_ids_reads_existing_output(tmp_path):
    out = tmp_path / "run.jsonl"
    write_jsonl(out, [{"id": "az-001", "raw_response": "x"}])
    assert completed_ids(out) == {"az-001"}


def test_completed_ids_on_missing_file_is_empty(tmp_path):
    assert completed_ids(tmp_path / "yoxdur.jsonl") == set()


def test_resume_skips_already_answered_rows(tmp_path):
    out = tmp_path / "run.jsonl"
    backend = CountingBackend()

    run_evaluation(RECORDS[:1], backend, "az", out, GenerationConfig(), progress=False)
    written = run_evaluation(RECORDS, backend, "az", out, GenerationConfig(), progress=False)

    assert written == 1                 # yalnız qalan sətir
    assert len(read(out)) == 2          # fayl üstünə yazılmır, əlavə olunur
    assert [r["id"] for r in read(out)] == ["az-001", "az-002"]


def test_resume_on_a_complete_run_writes_nothing(tmp_path):
    out = tmp_path / "run.jsonl"
    run_evaluation(RECORDS, CountingBackend(), "az", out, GenerationConfig(), progress=False)
    assert run_evaluation(
        RECORDS, CountingBackend(), "az", out, GenerationConfig(), progress=False
    ) == 0


def test_no_resume_reruns_everything(tmp_path):
    out = tmp_path / "run.jsonl"
    run_evaluation(RECORDS, CountingBackend(), "az", out, GenerationConfig(), progress=False)
    written = run_evaluation(
        RECORDS, CountingBackend(), "az", out, GenerationConfig(),
        resume=False, progress=False,
    )
    assert written == 2
    assert len(read(out)) == 4  # köhnə sətirlər silinmir


# --------------------------------------------------------------------------
# Partiyalama və xətalar
# --------------------------------------------------------------------------


def test_records_are_sent_in_configured_batches(tmp_path):
    backend = CountingBackend()
    records = [{**RECORDS[0], "id": f"az-{i:03d}"} for i in range(1, 8)]
    run_evaluation(
        records, backend, "az", tmp_path / "run.jsonl",
        GenerationConfig(batch_size=3), progress=False,
    )
    assert backend.batches == [3, 3, 1]


def test_backend_returning_wrong_count_is_an_error(tmp_path):
    class BrokenBackend:
        name = "broken"

        def generate(self, prompts):
            return ["yalnız bir cavab"]

    with pytest.raises(RuntimeError, match="cavab qaytardı"):
        run_evaluation(
            RECORDS, BrokenBackend(), "az", tmp_path / "run.jsonl",
            GenerationConfig(), progress=False,
        )


# --------------------------------------------------------------------------
# Oracle backend (yalnız sınaq)
# --------------------------------------------------------------------------


def test_oracle_backend_is_deterministic():
    golds = {"az-001": "Paris", "az-002": "Ankara"}
    a = OracleBackend(golds, accuracy=0.5, seed=3).generate_for(["az-001", "az-002"])
    b = OracleBackend(golds, accuracy=0.5, seed=3).generate_for(["az-001", "az-002"])
    assert a == b


def test_oracle_accuracy_one_returns_every_gold():
    golds = {f"az-{i:03d}": f"cavab{i}" for i in range(1, 21)}
    responses = OracleBackend(golds, accuracy=1.0, seed=0).generate_for(list(golds))
    assert responses == list(golds.values())


def test_oracle_accuracy_zero_returns_no_gold_by_design():
    # accuracy=0 hər dəfə BAŞQA sətrin cavabını verir; təsadüfən üst-üstə düşə
    # bilər, ona görə dəqiq bərabərlik yox, aşağı üst-üstə düşmə gözlənilir.
    golds = {f"az-{i:03d}": f"cavab{i}" for i in range(1, 51)}
    ids = list(golds)
    responses = OracleBackend(golds, accuracy=0.0, seed=0).generate_for(ids)
    hits = sum(1 for i, r in zip(ids, responses) if r == golds[i])
    assert hits < 10


def test_oracle_generate_without_ids_is_refused():
    with pytest.raises(NotImplementedError):
        OracleBackend({}).generate(["prompt"])


def test_oracle_hit_rate_matches_accuracy_across_batches():
    """Generator partiyalar arasında sıfırlanmamalıdır.

    Sıfırlansaydı, eyni təsadüfi ardıcıllıq hər partiyada təkrarlanardı və
    faktiki dəqiqlik `accuracy` parametrindən kənara çıxardı — boru xəttini
    sınayan adam yanlış rəqəm görərdi.
    """
    golds = {f"az-{i:03d}": f"cavab{i}" for i in range(1, 401)}
    ids = list(golds)
    backend = OracleBackend(golds, accuracy=0.5, seed=0)

    responses = []
    for start in range(0, len(ids), 8):          # qaçışdakı kimi partiyalarla
        responses.extend(backend.generate_for(ids[start : start + 8]))

    hits = sum(1 for i, r in zip(ids, responses) if r == golds[i])
    assert 0.42 < hits / len(ids) < 0.58


def test_oracle_batched_and_single_calls_agree():
    golds = {f"az-{i:03d}": f"cavab{i}" for i in range(1, 33)}
    ids = list(golds)

    one_shot = OracleBackend(golds, accuracy=0.5, seed=1).generate_for(ids)

    batched_backend = OracleBackend(golds, accuracy=0.5, seed=1)
    batched: list[str] = []
    for start in range(0, len(ids), 8):
        batched.extend(batched_backend.generate_for(ids[start : start + 8]))

    assert batched == one_shot


# --------------------------------------------------------------------------
# Fayl adları
# --------------------------------------------------------------------------


def test_output_path_is_filesystem_safe(tmp_path):
    path = default_output_path("Qwen/Qwen3-1.7B", "az", tmp_path)
    assert path.name == "Qwen__Qwen3-1.7B__az.jsonl"


def test_output_paths_differ_per_language(tmp_path):
    az = default_output_path("issai/Qolda-AVL-5B", "az", tmp_path)
    en = default_output_path("issai/Qolda-AVL-5B", "en", tmp_path)
    assert az != en


# --------------------------------------------------------------------------
# Backend adları
# --------------------------------------------------------------------------


def test_test_backends_accept_a_custom_name():
    """Sınaq backend-ləri də `--model` dəyərini ad kimi daşımalıdır.

    Daşımasaydılar, bütün sınaq qaçışları eyni ("oracle") ad altında yazılardı
    və `analyze.py` iki fərqli modeli BİR qaçış kimi birləşdirərdi — RQ2
    müqayisəsi səssizcə yox olardı.
    """
    assert EchoBackend(name="modelA").name == "modelA"
    assert OracleBackend({}, name="modelB").name == "modelB"


def test_named_backends_write_distinct_models(tmp_path):
    out = tmp_path / "run.jsonl"
    run_evaluation(RECORDS, EchoBackend(name="modelA"), "az", out,
                   GenerationConfig(), progress=False)
    run_evaluation(RECORDS, EchoBackend(name="modelB"), "az", out,
                   GenerationConfig(), resume=False, progress=False)

    assert {row["model"] for row in read(out)} == {"modelA", "modelB"}


# --------------------------------------------------------------------------
# bitsandbytes CUDA uyğunlaşdırması
# --------------------------------------------------------------------------


def test_bitsandbytes_alignment_does_not_import_the_package(monkeypatch):
    """Köməkçi `bitsandbytes`-i IMPORT ETMƏMƏLİDİR.

    İmport native kitabxananı dərhal yükləyir; versiya uyğun gəlmirsə çökür və
    bundan sonra `BNB_CUDA_VERSION` təyin etmək gec olur — məhz həll etməyə
    çalışdığımız problem.
    """
    import sys

    from src.run_eval import _align_bitsandbytes_cuda_version

    monkeypatch.delenv("BNB_CUDA_VERSION", raising=False)
    monkeypatch.delitem(sys.modules, "bitsandbytes", raising=False)

    _align_bitsandbytes_cuda_version()
    assert "bitsandbytes" not in sys.modules


def test_bitsandbytes_alignment_respects_an_existing_setting(monkeypatch):
    from src.run_eval import _align_bitsandbytes_cuda_version

    monkeypatch.setenv("BNB_CUDA_VERSION", "124")
    assert _align_bitsandbytes_cuda_version() is None
    import os

    assert os.environ["BNB_CUDA_VERSION"] == "124"   # istifadəçi seçimi qorunur


# --------------------------------------------------------------------------
# Mühakimə rejiminin bağlanması
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rendered", "expected_suffix"),
    [
        ("<|im_start|>assistant\n<think>\n", "<think>\n</think>\n\n"),
        ("<|im_start|>assistant\n<think>", "<think>\n</think>\n\n"),
    ],
)
def test_forced_thinking_tag_is_closed(rendered, expected_suffix):
    """Şablon `<think>` teqini sabit yazırsa, prompt onu bağlamalıdır.

    `issai/Qolda-AVL-5B` şablonu `enable_thinking` parametrini tanımır və
    generasiya promptunu `<think>` ilə bitirir. Bağlanmasa, model həmişə
    mühakimə edir və qısa cavab limitində cavaba çatmır — 96 sətrin 96-sı
    sıfır bal alırdı.
    """
    from src.run_eval import TransformersBackend

    result = TransformersBackend._close_forced_thinking(rendered)
    assert result.endswith(expected_suffix)


@pytest.mark.parametrize(
    "rendered",
    [
        "<|im_start|>assistant\n",
        "<think>mühakimə</think>\n<|im_start|>assistant\n",
        "Sual: X\nCavab:",
    ],
)
def test_prompts_without_an_open_think_tag_are_untouched(rendered):
    from src.run_eval import TransformersBackend

    assert TransformersBackend._close_forced_thinking(rendered) == rendered


# --------------------------------------------------------------------------
# Əlifba nəzarəti üçün prompt üslubu
# --------------------------------------------------------------------------


def test_script_prompt_demands_the_latin_alphabet():
    from src.run_eval import build_prompt

    prompt = build_prompt(RECORDS[0], "az", "script")
    assert "latın əlifbası" in prompt
    assert RECORDS[0]["question_az"] in prompt


def test_script_and_default_prompts_differ_only_by_the_instruction():
    from src.run_eval import build_prompt

    default = build_prompt(RECORDS[0], "az", "default")
    script = build_prompt(RECORDS[0], "az", "script")
    assert default != script
    # Nümunələr eyni qalmalıdır, yoxsa fərq təlimatdan yox, nümunələrdən gələr.
    assert "Cavab: Qahirə" in default and "Cavab: Qahirə" in script


def test_both_languages_have_a_script_variant():
    from src.run_eval import PROMPT_STYLES

    assert set(PROMPT_STYLES["script"]) == {"az", "en"}


def test_unknown_prompt_style_raises():
    from src.run_eval import build_prompt

    with pytest.raises(ValueError, match="prompt üslubu"):
        build_prompt(RECORDS[0], "az", "yoxdur")


def test_prompt_style_is_recorded_in_the_raw_output(tmp_path):
    out = tmp_path / "run.jsonl"
    run_evaluation(RECORDS, CountingBackend(), "az", out, GenerationConfig(),
                   progress=False, prompt_style="script")
    assert all(row["prompt_style"] == "script" for row in read(out))


def test_script_runs_get_a_separate_output_file(tmp_path):
    default = default_output_path("m", "az", tmp_path)
    script = default_output_path("m", "az", tmp_path, "script")
    assert default != script
    assert default.name == "m__az.jsonl"       # mövcud fayllar adını dəyişmir


# --------------------------------------------------------------------------
# Model yükləmə zənciri
# --------------------------------------------------------------------------


def test_model_loader_rejects_an_object_without_generate(monkeypatch):
    """`AutoModelForCausalLM` `qwen3_vl` üçün xəta VERMİR, çılpaq gövdə qaytarır.

    Belə obyektin `generate` metodu yoxdur; yalnız istisnaya baxan zəncir onu
    qəbul edir və qaçış 96 sətrin hamısında çökür — özü də çıxış kodu 0 ilə.
    """
    import types

    from src.run_eval import TransformersBackend

    class Backbone:            # `generate` yoxdur — yararsız
        pass

    class WithHead:            # yararlı
        def generate(self, *a, **k):
            return []

    calls = []

    class FakeAuto:
        def __init__(self, result):
            self.result = result

        def from_pretrained(self, model_id, **kwargs):
            calls.append(self.result.__name__)
            return self.result()

    fake = types.SimpleNamespace(
        AutoModelForCausalLM=FakeAuto(Backbone),
        AutoModelForImageTextToText=FakeAuto(WithHead),
    )
    monkeypatch.setitem(__import__("sys").modules, "transformers", fake)

    model = TransformersBackend._load_model("dummy", {})
    assert isinstance(model, WithHead)
    assert calls == ["Backbone", "WithHead"]   # birinci sınandı və rədd edildi


def test_model_loader_reports_every_failed_class(monkeypatch):
    import types

    from src.run_eval import TransformersBackend

    class Backbone:
        pass

    class FakeAuto:
        def from_pretrained(self, model_id, **kwargs):
            return Backbone()

    fake = types.SimpleNamespace(AutoModelForCausalLM=FakeAuto())
    monkeypatch.setitem(__import__("sys").modules, "transformers", fake)

    with pytest.raises(RuntimeError, match="`generate` yoxdur"):
        TransformersBackend._load_model("dummy", {})


def test_prompt_styles_cover_both_languages():
    """Hər üslub hər iki dildə olmalıdır.

    Biri əskik olsaydı, həmin üslubla AZ/EN müqayisəsi qurula bilməzdi və
    robustluq yoxlaması yarımçıq qalardı.
    """
    from src.run_eval import PROMPT_STYLES

    for name, templates in PROMPT_STYLES.items():
        assert set(templates) == {"az", "en"}, name
        for language, text in templates.items():
            assert "{question}" in text, f"{name}/{language}"


def test_robustness_styles_differ_structurally():
    """Variantlar QƏSDƏN fərqlidir, sadəcə söz dəyişikliyi deyil.

    Yalnız ifadə dəyişsəydi, yoxlama formal olardı: "promptunuz pisdir"
    etirazına cavab vermək üçün format da dəyişməlidir.
    """
    from src.run_eval import PROMPT_STYLES

    zeroshot = PROMPT_STYLES["zeroshot"]["az"]
    plain = PROMPT_STYLES["plain"]["az"]
    default = PROMPT_STYLES["default"]["az"]

    # zeroshot-da nümunə yoxdur
    assert "Qahirə" not in zeroshot
    assert "Qahirə" in default
    # plain-də etiket yoxdur, amma nümunə var
    assert "Cavab:" not in plain
    assert "Qahirə" in plain


def test_robustness_styles_reuse_the_same_example_facts():
    """Nümunə faktları dəyişməməlidir.

    Dəyişsəydi, ölçülən şey formatın təsiri yox, yeni nümunənin çətinliyi
    olardı. Həmin cavablar çirklənmə qapısı ilə datasetdən kənardadır.
    """
    from src.run_eval import PROMPT_STYLES

    for name in ("default", "script", "plain"):
        text = PROMPT_STYLES[name]["az"]
        assert "Qahirə" in text and "H2O" in text, name


def test_chat_template_can_be_disabled():
    """Şablonu söndürmək CÜT müqayisələri üçün məcburidir.

    `Mistral-7B-v0.1`-in chat şablonu yoxdur, ondan köklənmiş
    `Trendyol-LLM-7b-base`-in isə var. Söndürmə imkanı olmasaydı, eyni prompt
    cütün iki üzvünə fərqli formada çatardı: biri xam few-shot mətn alır və
    36.9% yığır, digəri `[INST]` içinə salınmış mətn alır, həmin formatı
    tanımır və 0.0% yığır. Ölçülən şey fine-tune-un təsiri yox, şablon fərqi
    olardı.
    """

    class FakeTokenizer:
        chat_template = "{{ bos_token }}[INST] {{ messages[0]['content'] }} [/INST]"

        def apply_chat_template(self, messages, **kwargs):
            return f"[INST] {messages[0]['content']} [/INST]"

    from src.run_eval import TransformersBackend

    class Probe:
        def __init__(self, use_chat_template):
            self.tokenizer = FakeTokenizer()
            self.use_chat_template = use_chat_template

        _apply_chat_template = TransformersBackend._apply_chat_template
        _close_forced_thinking = staticmethod(
            TransformersBackend._close_forced_thinking
        )

    prompt = "Sual: Bakı haradadır?\nCavab:"
    assert Probe(use_chat_template=True)._apply_chat_template(prompt) != prompt
    assert Probe(use_chat_template=False)._apply_chat_template(prompt) == prompt
