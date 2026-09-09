"""echo_gate.py üçün testlər.

Nümunə cavabları TESTDƏ YAZILMIR: istehsal şablonundan alınır. Əks halda
şablon dəyişəndə test keçər, qapı isə yalan danışardı.
"""

from __future__ import annotations

import pytest

from src.analyze import Run, RunKey
from src.echo_gate import (
    MAX_ECHO,
    build_report,
    degenerate,
    echo_rate,
    echoes_examples,
    prompt_prefix,
)
from src.run_eval import PROMPT_STYLES


def first_example_answer(style: str, language: str) -> str:
    """Şablonun BİRİNCİ nümunə cavabı, istehsal mətnindən oxunur."""
    prefix = prompt_prefix(style, language)
    lines = [line.strip() for line in prefix.splitlines() if line.strip()]
    # Nümunə cavabı sual sətrindən sonrakı sətirdir; etiket varsa atılır.
    for line in lines:
        if ":" in line and not line.endswith("?"):
            candidate = line.split(":", 1)[1].strip()
            if candidate:
                return candidate
    return lines[-1]


def run(raw, language="az", style="default"):
    return Run(
        key=RunKey("test/model", language, style),
        predictions={k: v for k, v in raw.items()},
        raw=dict(raw),
    )


def test_prefix_comes_from_production_template():
    prefix = prompt_prefix("default", "az")
    assert "{question}" not in prefix
    assert prefix in PROMPT_STYLES["default"]["az"]


def test_single_line_answer_is_never_an_echo():
    """Nümunə ilə üst-üstə düşən TƏK sətirli cavab pozuntu deyil."""
    prefix = prompt_prefix("default", "az")
    assert not echoes_examples(first_example_answer("default", "az"), prefix)


def test_the_actual_pathology_is_caught():
    """Nümunə cavabı, sonra əsl cavab: məhz tutulmalı olan hal."""
    prefix = prompt_prefix("default", "az")
    text = first_example_answer("default", "az") + "\n120"
    assert echoes_examples(text, prefix)


def test_normal_multiline_answer_is_not_an_echo():
    prefix = prompt_prefix("default", "az")
    assert not echoes_examples("Bakı\nAzərbaycanın paytaxtı", prefix)


@pytest.mark.parametrize("style", sorted(PROMPT_STYLES))
@pytest.mark.parametrize("language", ["az", "en"])
def test_every_style_and_language_has_a_prefix(style, language):
    assert prompt_prefix(style, language).strip()


def test_rate_and_gate_agree():
    seed = first_example_answer("default", "az")
    raw = {f"a-{i}": (seed + "\n120" if i < 8 else "120") for i in range(10)}
    r = run(raw)
    assert echo_rate(r) == pytest.approx(0.8)
    assert degenerate(r) == pytest.approx(0.8)


def test_clean_run_passes_the_gate():
    r = run({f"a-{i}": "120" for i in range(10)})
    assert echo_rate(r) == 0.0
    assert degenerate(r) is None


def test_gate_threshold_is_not_tripped_just_below():
    seed = first_example_answer("default", "az")
    raw = {f"a-{i}": (seed + "\n120" if i < 2 else "120") for i in range(10)}
    assert echo_rate(run(raw)) == pytest.approx(0.2)
    assert degenerate(run(raw)) is None, "hədd bərabərlikdə keçməlidir"
    assert MAX_ECHO == 0.20


def test_report_names_the_broken_run():
    seed = first_example_answer("default", "az")
    broken = run({f"a-{i}": seed + "\n120" for i in range(10)})
    text = build_report([broken])
    assert "qapıdan keçmir" in text
    assert "100.0%" in text


# --------------------------------------------------------------------------
# İkinci pozuntu: model cavab əvəzinə SUALI geri yazır
# --------------------------------------------------------------------------


from src.echo_gate import (  # noqa: E402
    MAX_QUESTION_ECHO,
    echoes_question,
    question_echo_rate,
)

QUESTION = "Fransanın paytaxtı hansı şəhərdir?"


def dataset(n=10):
    return {f"a-{i}": {"id": f"a-{i}", "question_az": QUESTION, "question_en": "?"} for i in range(n)}


def test_question_echo_is_detected():
    assert echoes_question(QUESTION, QUESTION)


def test_a_real_answer_is_not_a_question_echo():
    assert not echoes_question("Paris", QUESTION)


def test_short_questions_never_trigger():
    """Qısa mətn təsadüfən üst-üstə düşə bilər; hədd qoyulub."""
    assert not echoes_question("O", "O")


def test_answer_that_merely_mentions_the_topic_is_not_an_echo():
    assert not echoes_question("Parisdir", QUESTION)


def test_question_echo_rate_and_gate():
    raw = {f"a-{i}": (QUESTION if i < 3 else "Paris") for i in range(10)}
    r = run(raw)
    assert question_echo_rate(r, dataset()) == pytest.approx(0.3)
    assert MAX_QUESTION_ECHO == 0.20


def test_report_flags_a_question_echoing_run():
    raw = {f"a-{i}": QUESTION for i in range(10)}
    text = build_report([run(raw)], dataset())
    assert "qapıdan keçmir" in text
    assert "100.0%" in text


def test_report_without_dataset_still_works():
    """Dataset verilməsə, sual təkrarı ölçülmür, amma hesabat qurulur."""
    text = build_report([run({f"a-{i}": "Paris" for i in range(4)})])
    assert "Nümunə təkrarı" in text
