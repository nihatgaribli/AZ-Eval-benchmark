"""fine_tune_pairs.py üçün testlər."""

from __future__ import annotations

from src.analyze import Run, RunKey
from src.fine_tune_pairs import PAIRS, build_report


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


def run(model, language, predictions):
    return Run(key=RunKey(model, language), predictions=predictions, raw=dict(predictions))


def make_runs(ds, az_tuned_right, en_tuned_right, az_base_right=None,
              en_base_right=None):
    """Baza və köklənmiş modelin nə qədər bildiyi.

    Baza defolt olaraq hər şeyi bilir, yəni köklənmiş model yalnız İTİRƏ
    bilər. Artıq zərərin iki yanlış oxunuşunu yoxlamaq üçün bazanı da zəif
    etmək lazımdır: model qazana da bilməlidir.
    """
    ids = sorted(ds)
    pair = PAIRS[0]
    n = len(ids)
    az_base_right = n if az_base_right is None else az_base_right
    en_base_right = n if en_base_right is None else en_base_right
    runs = {}
    runs[(pair.base, "az")] = run(
        pair.base, "az",
        {i: (ds[i]["answer"] if k < az_base_right else "yanlış")
         for k, i in enumerate(ids)},
    )
    runs[(pair.base, "en")] = run(
        pair.base, "en",
        {i: (ds[i]["answer_en"] if k < en_base_right else "wrong")
         for k, i in enumerate(ids)},
    )
    runs[(pair.tuned, "az")] = run(
        pair.tuned,
        "az",
        {i: (ds[i]["answer"] if k < az_tuned_right else "yanlış") for k, i in enumerate(ids)},
    )
    runs[(pair.tuned, "en")] = run(
        pair.tuned,
        "en",
        {i: (ds[i]["answer_en"] if k < en_tuned_right else "wrong") for k, i in enumerate(ids)},
    )
    return runs


def test_extra_damage_is_positive_when_azerbaijani_suffers_more():
    """AZ daha çox itirirsə, artıq zərər müsbət olmalıdır."""
    ds = dataset()
    report = build_report(ds, make_runs(ds, az_tuned_right=10, en_tuned_right=35))
    assert "azərbaycanca ƏLAVƏ zərər" in report


def test_negative_excess_is_not_called_protection_when_azerbaijani_also_fell():
    """EN daha çox itirsə də, AZ düşübsə bu, QORUNMA DEYİL.

    Bu, `Türk 1`-in real davranışıdır: azərbaycanca 10.9 bənd itirir və
    artıq zərər yalnız ingiliscənin 26.9 bənd çökməsinə görə mənfidir. Onu
    "qorunub" adlandırmaq məqalənin özünün xəbərdarlıq etdiyi yanlış
    oxunuşdur, ona görə hesabat indi hər iki dilin nə etdiyini deyir.

    Burada azərbaycanca 40-dan 35-ə düşür, yəni itki var.
    """
    ds = dataset()
    report = build_report(ds, make_runs(ds, az_tuned_right=35, en_tuned_right=10))
    assert "azərbaycanca da düşüb" in report
    assert "nisbətən QORUNUB" not in report


def test_negative_excess_is_protection_only_when_azerbaijani_holds():
    """Azərbaycanca DÜŞMÜRSƏ, mənfi artıq zərər həqiqətən qorunmadır.

    `Latın 3` belədir: azərbaycanca 1.1 bənd QALXIR, ingiliscə düşür.
    """
    ds = dataset()
    runs = make_runs(ds, az_base_right=30, az_tuned_right=34,
                     en_base_right=40, en_tuned_right=10)
    report = build_report(ds, runs)
    assert "nisbətən QORUNUB" in report


def test_positive_excess_is_not_damage_when_both_languages_improved():
    """Hər iki dil qalxıbsa, müsbət artıq zərər ZƏRƏR DEYİL.

    `Latın 5` (fransız) belədir: azərbaycanca 6.5%-dən 10.7%-ə qalxır,
    ingiliscə 28.6%-dən 38.8%-ə. Fərq metriki müsbət çıxır, çünki ingiliscə
    daha çox qazanıb, amma itirilən heç nə yoxdur.
    """
    ds = dataset()
    runs = make_runs(ds, az_base_right=5, az_tuned_right=10,
                     en_base_right=5, en_tuned_right=35)
    report = build_report(ds, runs)
    assert "ingiliscə daha çox" in report
    assert "ƏLAVƏ zərər" not in report


def test_equal_loss_is_reported_as_indistinguishable():
    ds = dataset()
    report = build_report(ds, make_runs(ds, az_tuned_right=20, en_tuned_right=20))
    assert "sıfırdan ayırd edilmir" in report


def test_missing_pair_is_skipped_not_faked():
    """Qaçışı olmayan cüt cədvəldə uydurulmamalıdır."""
    ds = dataset()
    report = build_report(ds, make_runs(ds, 10, 35))
    assert PAIRS[0].label in report
    assert PAIRS[2].label not in report.split("## Oxunuş")[0]


def test_report_states_its_own_limitation():
    """Hər istiqamətdə bir-iki cüt var; mətn bunu gizlətməməlidir."""
    ds = dataset()
    report = build_report(ds, make_runs(ds, 10, 35))
    assert "MƏHDUDİYYƏT" in report


def test_confirmatory_family_covers_only_the_declared_pairs():
    """Ailə hipotezin öz ölçüsündə olmalıdır: cüt x zəncir x dil.

    `analyze.py` cədvəlləri gördüyü hər model cütünü sınayır; 14 model əlavə
    olunanda ailə 474 testə çatdı və əsas hipotezin Holm p qiyməti 0.018-dən
    0.047-yə sürüşdü. Genişlik üçün əlavə edilmiş və hipotezi ümumiyyətlə
    sınamayan testlər onu cəzalandırmamalıdır.
    """
    from src.fine_tune_pairs import confirmatory_table
    from src.metrics import MODES

    ds = dataset()
    runs = make_runs(ds, az_tuned_right=10, en_tuned_right=35)
    # Ailəyə qarışmamalı olan əlavə model.
    ids = sorted(ds)
    runs[("kənar", "az")] = run("kənar", "az", {i: "yanlış" for i in ids})
    runs[("kənar", "en")] = run("kənar", "en", {i: "wrong" for i in ids})

    table = confirmatory_table(ds, runs)
    rows = [l for l in table.splitlines() if l.startswith("| Qazax") or l.startswith("| Türk")]
    assert len(rows) == len(MODES) * 2, table
    assert "kənar" not in table
    assert f"Ailə {len(MODES) * 2} testdir" in table


def test_confirmatory_table_explains_why_it_exists():
    """Dar ailə şübhə doğurur; mətn səbəbi yazmalıdır."""
    from src.fine_tune_pairs import build_report

    ds = dataset()
    report = build_report(ds, make_runs(ds, 10, 35))
    assert "474" in report
    assert "əvvəlcədən elan" in report or "elan edilmiş" in report


# --------------------------------------------------------------------------
# Qapılar: cüt HƏR HANSI qapıdan keçmirsə cədvələ girmir
# --------------------------------------------------------------------------


def long_question_dataset(n=40):
    """Sual təkrarı qaydası 12 simvoldan qısa mətnə baxmır (təsadüfi
    üst-üstə düşmə riskinə görə), ona görə burada real uzunluqda sual
    lazımdır."""
    ds = dataset(n)
    for i, row in ds.items():
        row["question_az"] = f"{i} nömrəli sualın azərbaycanca tam mətni nədir?"
        row["question_en"] = f"What is the full English text of question {i}?"
    return ds


def test_a_pair_failing_any_gate_is_excluded_not_tabulated():
    """Yalnız çıxarış qapısına baxmaq AZDIR.

    `Racka-4B` çıxarış qapısından KEÇİR (12.0%), amma azərbaycanca sualların
    68.4%-ini geri yazır. Tək qapıya baxsaydıq onu ölçmə sayardıq. Bu test
    həmin regressiyanı kilidləyir.
    """
    from src.fine_tune_pairs import _gate_failure

    ds = long_question_dataset()
    pair = PAIRS[0]
    # Baza sağlamdır, köklənmiş model isə sualı geri yazır.
    healthy = {i: ds[i]["answer"] for i in ds}
    echoing = {i: ds[i]["question_az"] for i in ds}
    runs = {
        (pair.base, "az"): run(pair.base, "az", healthy),
        (pair.base, "en"): run(pair.base, "en", healthy),
        (pair.tuned, "az"): run(pair.tuned, "az", echoing),
        (pair.tuned, "en"): run(pair.tuned, "en", healthy),
    }
    reason = _gate_failure(runs, pair, ds)
    assert reason is not None, "sual təkrarı tutulmalıdır"
    assert "sual təkrarı" in reason
    assert pair.tuned in reason


def test_a_healthy_pair_passes_every_gate():
    from src.fine_tune_pairs import _gate_failure

    ds = dataset()
    pair = PAIRS[0]
    healthy = {i: ds[i]["answer"] for i in ds}
    runs = {
        (m, l): run(m, l, healthy)
        for m in (pair.base, pair.tuned)
        for l in ("az", "en")
    }
    assert _gate_failure(runs, pair, ds) is None


def test_excluded_pairs_are_named_in_the_report():
    """Silinmir, "ölçmə deyil" kimi göstərilir."""
    ds = long_question_dataset()
    pair = PAIRS[0]
    healthy = {i: ds[i]["answer"] for i in ds}
    echoing = {i: ds[i]["question_az"] for i in ds}
    runs = {
        (pair.base, "az"): run(pair.base, "az", healthy),
        (pair.base, "en"): run(pair.base, "en", healthy),
        (pair.tuned, "az"): run(pair.tuned, "az", echoing),
        (pair.tuned, "en"): run(pair.tuned, "en", healthy),
    }
    text = build_report(ds, runs)
    assert "Qapıdan keçməyən cütlər" in text
    assert pair.label in text


def test_every_pair_has_english_names():
    """MƏQALƏ İNGİLİSCƏDİR: şəkil və göndəriş adları burada saxlanılır.

    Ayrı tərcümə cədvəli olsaydı, yeni cüt əlavə ediləndə səssizcə
    köhnələrdi və şəkildə azərbaycanca ad qalardı.
    """
    for pair in PAIRS:
        assert pair.label_en, pair.label
        assert pair.target_en, pair.label
        assert pair.script_en, pair.label


def test_english_names_are_not_azerbaijani():
    """Regressiya: şəkillərdə azərbaycanca etiketlər çıxmışdı."""
    azerbaijani = {"qazax", "türk", "rus", "ukrayna", "norveç", "macar", "gürcü"}
    for pair in PAIRS:
        assert pair.target_en.lower() not in azerbaijani, pair.label
        assert pair.script_en in {"Cyrillic", "Latin", "Mkhedruli", "mixed"}, pair.label
