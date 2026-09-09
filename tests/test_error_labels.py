"""Xəta taksonomiyasının insan yarısı üçün testlər."""

from __future__ import annotations

import csv

from src.error_labels import LABELS, build_report, pick_unlabelled, write_sample


def row(record_id, auto="", category="world"):
    return {
        "id": record_id,
        "category": category,
        "question": f"{record_id} sualı?",
        "gold": f"qızıl-{record_id}",
        "prediction": f"cavab-{record_id}",
        "error_type_auto": auto,
        "error_type": "",
    }


def test_only_the_machine_residue_is_sampled():
    """Maşın artıq etiket veribsə, insanın onu təkrarlaması vaxt itkisidir.

    İnsanın əlavə dəyəri məhz zəncirin kömək etmədiyi sətirlərdədir.
    """
    rows = [row("a"), row("b", auto="yazı sistemi"), row("c"), row("d", auto="diakritika")]
    picked = pick_unlabelled(rows, 10, seed=0)
    assert {r["id"] for r in picked} == {"a", "c"}


def test_sampling_is_stratified_by_category():
    """Təbəqələndirmə olmasaydı, nümunə ən böyük kateqoriyaya sürüşərdi."""
    rows = [row(f"h{i}", category="history") for i in range(40)]
    rows += [row(f"w{i}", category="world") for i in range(4)]
    picked = pick_unlabelled(rows, 10, seed=0)
    assert {r["category"] for r in picked} == {"history", "world"}


def test_sampling_is_reproducible():
    rows = [row(f"r{i}") for i in range(30)]
    assert pick_unlabelled(rows, 8, seed=3) == pick_unlabelled(rows, 8, seed=3)


def test_empty_residue_yields_nothing():
    """Maşın hər şeyi etiketləyibsə, insana iş qalmır."""
    rows = [row("a", auto="morfologiya"), row("b", auto="yazı sistemi")]
    assert pick_unlabelled(rows, 5, seed=0) == []


def test_sample_file_carries_what_the_annotator_needs(tmp_path):
    """Sual, qızıl cavab və modelin cavabı olmalıdır; onsuz qərar verilə bilməz."""
    tables = tmp_path / "tables"
    tables.mkdir()
    path = tables / "errors__m1.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row("x")))
        writer.writeheader()
        writer.writerows([row(f"x{i}") for i in range(5)])

    out = tmp_path / "labels.csv"
    count = write_sample(["m1"], tables, out, size=5)
    assert count == 5

    with out.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["sual"]
    assert rows[0]["qızıl cavab"]
    assert rows[0]["modelin cavabı"]
    assert rows[0]["etiket"] == ""


def test_report_compares_models_side_by_side():
    """İki model müqayisə edilmirsə, 'iki rejim fərqlidir' iddiası qurulmur."""
    rows = [
        {"model": "orfoqrafik", "id": "a", "etiket": "başqa dil", "qeyd": ""},
        {"model": "orfoqrafik", "id": "b", "etiket": "başqa dil", "qeyd": ""},
        {"model": "bacarıq", "id": "c", "etiket": "faktual", "qeyd": ""},
        {"model": "bacarıq", "id": "d", "etiket": "faktual", "qeyd": ""},
    ]
    text = build_report(rows)
    assert "orfoqrafik" in text and "bacarıq" in text
    assert "başqa dil" in text


def test_unlabelled_rows_are_ignored():
    assert "Hələ heç nə" in build_report([{"model": "m", "id": "a", "etiket": ""}])


def test_gold_errors_are_surfaced_as_a_dataset_audit():
    """`qızıl səhv` taksonomiyaya aid deyil, DATASETƏ aiddir.

    Etiketləyən adam qızıl cavabın yanlış olduğunu görürsə, bu, xəta növü
    yox, dataset qüsurudur və ayrıca göstərilməlidir.
    """
    rows = [
        {"model": "m", "id": "az-1", "sual": "test?", "qızıl cavab": "yanlış",
         "etiket": "qızıl səhv", "qeyd": "əslində başqadır"},
        {"model": "m", "id": "az-2", "sual": "t?", "qızıl cavab": "x",
         "etiket": "faktual", "qeyd": ""},
    ]
    text = build_report(rows)
    assert "DATASET AUDİTİ" in text
    assert "az-1" in text
    assert "əslində başqadır" in text


def test_every_label_appears_in_the_report():
    rows = [{"model": "m", "id": "a", "etiket": "faktual", "qeyd": ""}]
    text = build_report(rows)
    for label in LABELS:
        assert label in text


def test_an_invalid_label_is_not_counted():
    """Yazı səhvi olan etiket sayılmamalıdır, yoxsa nəticə səssizcə pozulardı."""
    rows = [
        {"model": "m", "id": "a", "etiket": "faktual", "qeyd": ""},
        {"model": "m", "id": "b", "etiket": "fakual", "qeyd": ""},  # yazı səhvi
    ]
    text = build_report(rows)
    assert "Etiketlənən sətir: 1." in text
