"""human_baseline.py üçün testlər."""

from __future__ import annotations

import collections
import json

from src.human_baseline import load_answers, score, stratified_sample


def record(record_id, answer, category):
    return {
        "id": record_id,
        "question_az": f"{record_id} sualı?",
        "question_en": f"{record_id} question?",
        "answer": answer,
        "answer_en": answer,
        "answer_aliases": [],
        "category": category,
    }


def dataset():
    rows = {}
    # Böyük təbəqə və çox kiçik təbəqə: nümunənin kiçiyi buraxmadığı yoxlanılır.
    for n in range(100):
        rows[f"big-{n}"] = record(f"big-{n}", f"cavab{n}", "culture")
    for n in range(4):
        rows[f"tiny-{n}"] = record(f"tiny-{n}", f"kicik{n}", "world")
    return rows


def test_small_category_is_never_dropped():
    """Təsadüfi seçim kiçik təbəqəni tamamilə buraxa bilər.

    `world` nəzarət qatıdır və tapıntıların bir hissəsi məhz oradadır; nümunədə
    olmasa, insan bazası həmin qatı ölçmür.
    """
    ds = dataset()
    ids = stratified_sample(ds, 20, seed=0)
    categories = collections.Counter(ds[i]["category"] for i in ids)
    assert categories["world"] >= 1
    assert categories["culture"] >= 1


def test_sample_is_deterministic():
    ds = dataset()
    assert stratified_sample(ds, 20, seed=0) == stratified_sample(ds, 20, seed=0)
    assert stratified_sample(ds, 20, seed=1) != stratified_sample(ds, 20, seed=0)


def test_sample_never_exceeds_the_requested_size():
    ds = dataset()
    assert len(stratified_sample(ds, 20, seed=0)) <= 20


def test_correct_answer_scores_and_blank_does_not():
    """Boş cavab SƏHV sayılır, çünki model də cavabsız sətirdə bal almır."""
    ds = dataset()
    answers = {"big-0": "cavab0", "big-1": "", "big-2": "yanlış"}
    report = score(ds, answers)
    assert "33.3%" in report
    assert "Boş buraxılan (bilmirəm): 1" in report


def test_scoring_uses_the_same_extraction_as_models():
    """İnsan `Cavab: X` yazsa da model kimi emal olunmalıdır.

    Fərqli yol seçilsəydi, insan və model balları müqayisə edilə bilməzdi.
    """
    ds = dataset()
    assert "100.0%" in score(ds, {"big-0": "Cavab: cavab0"})
    assert "100.0%" in score(ds, {"big-0": "**cavab0**"})


def test_report_breaks_down_by_category():
    ds = dataset()
    report = score(ds, {"big-0": "cavab0", "tiny-0": "kicik0"})
    assert "culture" in report and "world" in report


def test_empty_answer_file_is_handled(tmp_path):
    assert load_answers(tmp_path / "yoxdur.jsonl") == {}


def test_answers_round_trip(tmp_path):
    path = tmp_path / "answers.jsonl"
    path.write_text(
        json.dumps({"id": "a", "answer": "Bakı"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    assert load_answers(path) == {"a": "Bakı"}
