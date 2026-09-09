"""prompt_robustness.py üçün testlər."""

from __future__ import annotations

from src.analyze import Run, RunKey
from src.prompt_robustness import PAIR, STYLES, build_report, verdict


def record(record_id):
    return {
        "id": record_id,
        "question_az": f"{record_id} sualı?",
        "question_en": f"{record_id} question?",
        "answer": f"cavab{record_id}",
        "answer_en": f"answer{record_id}",
        "answer_aliases": [],
        "category": "world",
        "provenance": "manual",
    }


def dataset(n=40):
    return {f"q{i}": record(f"q{i}") for i in range(n)}


def run(model, language, style, predictions):
    return Run(
        key=RunKey(model, language, style),
        predictions=predictions,
        raw=dict(predictions),
    )


def build_runs(ds, az_right_by_style, en_right=38):
    """`az_right_by_style` şablon başına neçə azərbaycan sualının düz olduğunu verir."""
    ids = sorted(ds)
    runs = {}
    for style, az_right in az_right_by_style.items():
        for model in PAIR:
            # Baza modelində daha çox düz cavab olsun ki, cüt fərqi müsbət çıxsın.
            correct = az_right if model == PAIR[0] else max(0, az_right - 15)
            runs[(model, "az", style)] = run(
                model,
                "az",
                style,
                {
                    i: (ds[i]["answer"] if k < correct else "yanlış")
                    for k, i in enumerate(ids)
                },
            )
            runs[(model, "en", style)] = run(
                model,
                "en",
                style,
                {
                    i: (ds[i]["answer_en"] if k < en_right else "wrong")
                    for k, i in enumerate(ids)
                },
            )
    return runs


def test_verdict_confirms_when_every_style_agrees():
    """Üç şablonda da uçurum eyni istiqamətdə qalırsa, iddia promptdan asılı deyil."""
    ds = dataset()
    runs = build_runs(ds, {s: 20 for s in STYLES})
    text = verdict(ds, runs)
    assert "XEYR" not in text
    assert "prompt seçiminə söykənmir" in text


def test_verdict_flags_a_claim_that_depends_on_the_prompt():
    """Bir şablonda uçurum itirsə, hesabat bunu GİZLƏTMƏMƏLİDİR.

    Bu, ciddi tapıntıdır: həmin iddia prompt seçiminin nəticəsi ola bilər.
    """
    ds = dataset()
    # `plain` şablonunda azərbaycanca ingiliscədən yaxşı olsun: uçurum çevrilir.
    runs = build_runs(ds, {"default": 20, "zeroshot": 20, "plain": 40})
    text = verdict(ds, runs)
    assert "XEYR" in text
    assert "ŞABLONDAN ASILIDIR" in text


def test_report_lists_every_style():
    ds = dataset()
    runs = build_runs(ds, {s: 20 for s in STYLES})
    report = build_report(ds, runs)
    for style in STYLES:
        assert style in report


def test_report_separates_the_two_claims():
    """Dil uçurumu və cüt fərqi ayrı yoxlanılır, çünki fərqli şeylərdir."""
    ds = dataset()
    runs = build_runs(ds, {s: 20 for s in STYLES})
    report = build_report(ds, runs)
    assert "AZ/EN uçurumu" in report
    assert "Cüt fərqi" in report


def test_single_style_is_not_called_robust():
    """Bir şablonla robustluq iddiası qurula bilməz."""
    ds = dataset()
    runs = build_runs(ds, {"default": 20})
    text = verdict(ds, runs)
    assert "prompt seçiminə söykənmir" not in text


def run_with_raw(model, language, style, predictions, raw):
    return Run(key=RunKey(model, language, style), predictions=predictions, raw=raw)


def test_a_run_with_mostly_empty_answers_is_not_a_measurement():
    """Model heç nə yazmayıbsa, qiymətləndiriləcək şey yoxdur.

    `Qwen3-VL-4B-Thinking` şablonsuz `zeroshot`-da ingilis sətirlərinin
    42.7%-nə cavab vermirdi. Nəticədə ingilis balı çökdü və AZ/EN uçurumu
    "itdi". Bu, iddianın uğursuzluğu deyil, ölçmənin uğursuzluğudur.
    """
    from src.prompt_robustness import MAX_EMPTY, _degenerate

    ds = dataset(10)
    ids = sorted(ds)
    good = run_with_raw("m", "en", "zeroshot", {i: "x" for i in ids}, {i: "x" for i in ids})
    bad = run_with_raw(
        "m", "en", "zeroshot",
        {i: "" for i in ids},
        {i: ("" if k < 6 else "x") for k, i in enumerate(ids)},
    )
    assert _degenerate(good) is None
    assert _degenerate(bad) is not None
    assert _degenerate(bad) > MAX_EMPTY


def test_the_gate_reads_raw_text_not_the_extracted_answer():
    """Xam cavab boşdursa model susub; çıxarış boşdursa ÇIXARICI qüsurlu ola bilər.

    Qapı ikincisini cəzalandırmamalıdır, yoxsa çıxarıcı səhvi "model sınıb"
    kimi görünər və əsl səbəb gizlənər.
    """
    from src.prompt_robustness import _degenerate

    ds = dataset(10)
    ids = sorted(ds)
    # Xam cavab VAR, sadəcə çıxarıcı onu oxuya bilməyib.
    run = run_with_raw(
        "m", "az", "plain",
        {i: "" for i in ids},
        {i: "uzun izahat, cavab içindədir" for i in ids},
    )
    assert _degenerate(run) is None


def test_a_broken_style_is_dropped_for_the_model_in_every_comparison():
    """Şərait bir dildə sınıbsa, həmin model üçün hər iki müqayisədən çıxır.

    Yalnız sınıq dili atsaydıq, cüt fərqi hesablanmağa davam edərdi, halbuki
    modelin həmin şəraitdə çökdüyü digər dildən aşkardır.
    """
    ds = dataset()
    runs = build_runs(ds, {s: 20 for s in STYLES})
    ids = sorted(ds)
    # `zeroshot` şablonunda YALNIZ ingilis tərəfi sınır.
    for model in PAIR:
        runs[(model, "en", "zeroshot")] = run_with_raw(
            model, "en", "zeroshot",
            {i: "" for i in ids},
            {i: "" for i in ids},
        )
    text = verdict(ds, runs)
    assert "Müqayisəyə girməyən şəraitlər" in text
    assert "zeroshot" in text
    # İddia uğursuz sayılmamalıdır: qalan iki şablonda hər şey yerindədir.
    assert "XEYR" not in text


def test_the_report_separates_a_failed_claim_from_a_failed_measurement():
    """İki hal fərqli mətn verməlidir, yoxsa oxucu onları qarışdırar."""
    ds = dataset()
    runs = build_runs(ds, {s: 20 for s in STYLES})
    ids = sorted(ds)
    for model in PAIR:
        runs[(model, "en", "zeroshot")] = run_with_raw(
            model, "en", "zeroshot", {i: "" for i in ids}, {i: "" for i in ids}
        )
    invalid = verdict(ds, runs)
    assert "ÖLÇMƏNİN UĞURSUZLUĞUDUR" in invalid

    # Həqiqi uğursuzluq: şablonlar yararlıdır, amma nəticə çevrilir.
    flipped = verdict(ds, build_runs(ds, {"default": 20, "zeroshot": 20, "plain": 40}))
    assert "ŞABLONDAN ASILIDIR" in flipped
