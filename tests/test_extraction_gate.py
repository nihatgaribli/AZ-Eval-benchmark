"""extraction_gate.py üçün testlər."""

from __future__ import annotations

import pytest

from src.analyze import Run, RunKey
from src.extraction_gate import (
    MAX_RECOVERABLE,
    answer_present,
    build_report,
    degenerate,
    recoverable_rate,
)


def dataset(n=10):
    return {
        f"a-{i}": {
            "id": f"a-{i}",
            "question_az": f"{i} sualı?",
            "question_en": f"question {i}?",
            "answer": "Paris",
            "answer_en": "Paris",
            "answer_aliases": [],
            "category": "world",
        }
        for i in range(n)
    }


def run(raw, language="en"):
    return Run(key=RunKey("test/model", language), predictions=dict(raw), raw=dict(raw))


def test_answer_present_ignores_punctuation_and_case():
    assert answer_present("The capital of France is Paris.", "Paris")
    assert answer_present("paris", "Paris")
    assert not answer_present("Berlin", "Paris")


def test_empty_gold_is_never_present():
    """Boş qızıl cavab hər mətndə 'tapılmamalıdır'."""
    assert not answer_present("anything", "")


def test_a_sentence_answer_counts_as_recoverable():
    """Bu, gürcü cütündə görünən pozuntudur."""
    raw = {f"a-{i}": "The capital of France is Paris." for i in range(10)}
    share, wrong = recoverable_rate(run(raw), dataset())
    assert wrong == 10, "hamısı exact-match ilə səhv sayılmalıdır"
    assert share == pytest.approx(1.0)
    assert degenerate(run(raw), dataset()) == pytest.approx(1.0)


def test_a_plainly_wrong_answer_is_not_recoverable():
    raw = {f"a-{i}": "Berlin" for i in range(10)}
    share, wrong = recoverable_rate(run(raw), dataset())
    assert wrong == 10
    assert share == 0.0
    assert degenerate(run(raw), dataset()) is None


def test_correct_answers_leave_nothing_to_recover():
    raw = {f"a-{i}": "Paris" for i in range(10)}
    share, wrong = recoverable_rate(run(raw), dataset())
    assert wrong == 0
    assert share == 0.0


def test_threshold_sits_in_the_measured_gap():
    """15% deyil 30%: paylanmada yeganə boşluq 42.4% ilə 16.4% arasındadır."""
    assert MAX_RECOVERABLE == 0.30


def test_gate_is_not_tripped_by_a_moderate_rate():
    raw = {f"a-{i}": ("The capital is Paris." if i < 2 else "Berlin") for i in range(10)}
    share, _ = recoverable_rate(run(raw), dataset())
    assert share == pytest.approx(0.2)
    assert degenerate(run(raw), dataset()) is None, "0.2 hədddən aşağıdır"


def test_report_names_the_broken_run():
    raw = {f"a-{i}": "The capital of France is Paris." for i in range(10)}
    text = build_report([run(raw)], dataset())
    assert "qapıdan keçmir" in text
    assert "100.0%" in text


def test_report_says_length_is_not_the_measure():
    text = build_report([run({f"a-{i}": "Berlin" for i in range(4)})], dataset())
    assert "Uzun cavab özü pozuntu deyil" in text
