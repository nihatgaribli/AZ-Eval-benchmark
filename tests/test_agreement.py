"""Annotatorlararası razılıq aləti üçün testlər.

ƏN VACİB TEST BURADA `test_the_sample_hides_the_first_decision`-dır. İkinci
annotator birincinin qərarını görsəydi, razılıq süni şəkildə yuxarı çıxardı
və bütün ölçü mənasını itirərdi.
"""

from __future__ import annotations

import json

import pytest

from src.agreement import (
    LABELS,
    build_report,
    cohen_kappa,
    interpret,
    stratified_sample,
    write_sample,
)


def record(record_id, provenance="manual", category="world"):
    return {
        "id": record_id,
        "question_az": f"{record_id} sualı?",
        "question_en": f"{record_id} question?",
        "answer": f"cavab-{record_id}",
        "answer_en": f"answer-{record_id}",
        "category": category,
        "provenance": provenance,
        "verified_by": "human",
        "notes": f"template=secret_{record_id}",
        "source": "https://example.invalid/gizli",
    }


def dataset(n=60):
    origins = ("manual", "wikidata-template", "computed-template")
    return {
        f"az-{i:03d}": record(f"az-{i:03d}", origins[i % len(origins)])
        for i in range(n)
    }


def test_the_sample_hides_the_first_decision(tmp_path):
    """Fayl birinci annotatorun qərarını və ipucu sahələrini SAXLAMAMALIDIR.

    `verified_by` birbaşa qərardır. `notes` şablon adını, `source` isə mənbə
    linkini saxlayır; hər ikisi ikinci annotatora "bu sətir haradan gəlib"
    deyir və qərarını əyə bilər.
    """
    ds = dataset()
    ids = sorted(ds)[:10]
    path = tmp_path / "sample.jsonl"
    write_sample(ds, ids, path)

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 10
    for row in rows:
        assert "verified_by" not in row
        assert "notes" not in row
        assert "source" not in row
        assert row["label"] == ""
        assert row["question_az"]


def test_the_sample_is_stratified_by_provenance():
    """Təsadüfi seçim `manual` payını azalda bilər, halbuki risk oradadır."""
    ds = dataset(90)
    ids = stratified_sample(ds, 30, seed=0)
    origins = {ds[i]["provenance"] for i in ids}
    assert origins == {"manual", "wikidata-template", "computed-template"}


def test_sampling_is_reproducible():
    ds = dataset()
    assert stratified_sample(ds, 20, seed=7) == stratified_sample(ds, 20, seed=7)


def test_kappa_is_one_for_perfect_agreement_with_varied_labels():
    first = ["düzgün", "səhv", "düzgün", "səhv"]
    assert cohen_kappa(first, list(first)) == pytest.approx(1.0)


def test_kappa_is_zero_when_agreement_is_only_chance():
    """Yarısında razılaşıb, yarısında yox: təsadüfdən yaxşı deyil."""
    first = ["düzgün", "düzgün", "səhv", "səhv"]
    second = ["düzgün", "səhv", "düzgün", "səhv"]
    assert cohen_kappa(first, second) == pytest.approx(0.0)


def test_kappa_is_undefined_when_one_label_is_used_everywhere():
    """Hamısına `düzgün` deyilibsə, kappa qurula BİLMİR.

    Bu, mükəmməl razılıq DEYİL. Xam faiz 100% göstərərdi və yanıldardı;
    kappa isə dürüst şəkildə "təyin olunmur" deyir.
    """
    labels = ["düzgün"] * 5
    kappa = cohen_kappa(labels, list(labels))
    assert kappa != kappa  # NaN
    assert "təyin olunmur" in interpret(kappa)


def test_kappa_can_be_negative():
    first = ["düzgün", "düzgün", "səhv", "səhv"]
    second = ["səhv", "səhv", "düzgün", "düzgün"]
    assert cohen_kappa(first, second) < 0
    assert "təsadüfdən PİS" in interpret(cohen_kappa(first, second))


def test_mismatched_lengths_are_refused():
    with pytest.raises(ValueError):
        cohen_kappa(["düzgün"], ["düzgün", "səhv"])


def test_report_lists_rejected_rows_and_does_not_delete_them():
    """Rədd edilən sətir avtomatik silinməməlidir, əl ilə baxılmalıdır."""
    ds = dataset(30)
    ids = sorted(ds)[:6]
    answers = {
        i: {"id": i, "label": "düzgün" if k else "səhv", "comment": "cavab yanlışdır"}
        for k, i in enumerate(ids)
    }
    text = build_report(ds, answers)
    assert "Rədd edilən" in text
    assert ids[0] in text
    assert "AVTOMATİK silinmir" in text


def test_report_states_the_weakness_of_the_measure():
    """Birinci annotatorun etiketi həmişə `düzgün`-dür; bu, açıq yazılmalıdır.

    Gizlədilsəydi, oxucu kappanı iki müstəqil qərar paylanması kimi oxuyardı.
    """
    ds = dataset(30)
    ids = sorted(ds)[:5]
    answers = {i: {"id": i, "label": "düzgün", "comment": ""} for i in ids}
    text = build_report(ds, answers)
    assert "HƏMİŞƏ `düzgün`" in text
    assert "gizlədilmir" in text


def test_report_breaks_the_result_down_by_provenance():
    """Risk mənşəyə görə fərqlidir: hesablanan sətirdə səhv ehtimalı sıfıra yaxındır."""
    ds = dataset(30)
    ids = sorted(ds)[:9]
    answers = {i: {"id": i, "label": "düzgün", "comment": ""} for i in ids}
    text = build_report(ds, answers)
    assert "Mənşəyə görə" in text
    assert "manual" in text


def test_unfilled_rows_are_ignored():
    """Boş `label` etiket sayılmır, yoxsa doldurulmamış fayl nəticə verərdi."""
    ds = dataset(30)
    ids = sorted(ds)[:5]
    answers = {i: {"id": i, "label": "", "comment": ""} for i in ids}
    assert "hələ heç nə etiketləməyib" in build_report(ds, answers)


def test_every_declared_label_appears_in_the_report():
    ds = dataset(30)
    ids = sorted(ds)[:4]
    answers = {i: {"id": i, "label": "düzgün", "comment": ""} for i in ids}
    text = build_report(ds, answers)
    for label in LABELS:
        assert label in text


def test_csv_round_trip(tmp_path):
    """CSV yazılıb geri oxunmalıdır: ikinci annotator Excel işlədəcək.

    JSONL redaktəsi texniki adam tələb edir, Windows terminalı isə azərbaycan
    hərflərində problem çıxarır. CSV hər ikisini həll edir, ona görə yol
    işləməlidir.
    """
    import csv as _csv

    from src.agreement import load_answers, write_csv

    ds = dataset(30)
    ids = sorted(ds)[:5]
    path = tmp_path / "sample.csv"
    write_csv(ds, ids, path)

    # Annotator "qərar" sütununu doldurur.
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(_csv.DictReader(handle))
    assert [r["id"] for r in rows] == ids
    assert all(r["qərar"] == "" for r in rows)

    for index, row in enumerate(rows):
        row["qərar"] = "səhv" if index == 0 else "düzgün"
        row["qeyd"] = "yoxlanmalıdır" if index == 0 else ""
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = _csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    answers = load_answers(path)
    assert len(answers) == 5
    assert answers[ids[0]]["label"] == "səhv"
    assert answers[ids[0]]["comment"] == "yoxlanmalıdır"

    text = build_report(ds, answers)
    assert ids[0] in text


def test_csv_sample_also_hides_the_first_decision(tmp_path):
    """CSV yolunda da birincinin qərarı və ipucu sahələri OLMAMALIDIR."""
    import csv as _csv

    from src.agreement import write_csv

    ds = dataset(30)
    path = tmp_path / "sample.csv"
    write_csv(ds, sorted(ds)[:4], path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        header = next(_csv.reader(handle))
    for forbidden in ("verified_by", "notes", "source", "provenance"):
        assert forbidden not in header


def test_excel_formula_injection_is_blocked(tmp_path):
    """Tire ilə başlayan cavab Excel-də `#NAME?` olur və ölçünü korlayır.

    ÖLÇÜLDÜ: birinci ixracda `-y` və `-ki` cavabları Excel-də `#NAME?` kimi
    göründü, ikinci annotator onları haqlı olaraq səhv saydı və iki sətir
    dataset qüsuru kimi hesablandı. Qüsur isə İXRACDA idi.

    Azərbaycan dilində şəkilçi cavabları məhz tire ilə başlayır, yəni bu,
    nadir kənar hal deyil, düz mərkəzə dəyir.
    """
    import csv as _csv

    from src.agreement import excel_safe, write_csv

    assert excel_safe("-ki").startswith("\t")
    assert excel_safe("=SUM(1)").startswith("\t")
    assert excel_safe("Paris") == "Paris"

    ds = {"az-1": dict(record("az-1"), answer="-ki", question_az="şəkilçi?")}
    path = tmp_path / "s.csv"
    write_csv(ds, ["az-1"], path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(_csv.DictReader(handle))
    assert rows[0]["cavab"] != "-ki"
    assert "-ki" in rows[0]["cavab"]
