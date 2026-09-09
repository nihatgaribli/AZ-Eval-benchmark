"""audit_keys.py üçün testlər."""

from __future__ import annotations

from src.audit_keys import (
    chance_agreement,
    find_suspects,
    permutation_null,
    report,
)


def item(record_id, key_letter, choices=("A cavabı", "B cavabı", "C cavabı", "D cavabı")):
    return {
        "id": record_id,
        "question_az": f"{record_id} sualı nədir?",
        "answer": choices["ABCD".index(key_letter)],
        "choices": list(choices),
        "answer_letter": key_letter,
        "subject": "Maths",
    }


def test_agreement_against_the_key_is_flagged():
    """İki model B deyir, açar A göstərir: açar şübhəlidir."""
    items = [item("q1", "A")]
    picks = {"m1": {"q1": "B"}, "m2": {"q1": "B"}}
    (suspect,) = find_suspects(items, picks)
    assert suspect["key_letter"] == "A"
    assert suspect["models_letter"] == "B"
    assert suspect["models_answer"] == "B cavabı"
    assert suspect["n_models"] == 2


def test_agreement_with_the_key_is_not_flagged():
    items = [item("q1", "A")]
    picks = {"m1": {"q1": "A"}, "m2": {"q1": "A"}}
    assert find_suspects(items, picks) == []


def test_disagreement_is_not_flagged():
    """Modellər ayrılırsa, heç bir iddia qurulmur."""
    items = [item("q1", "A")]
    picks = {"m1": {"q1": "B"}, "m2": {"q1": "C"}}
    assert find_suspects(items, picks) == []


def test_a_single_model_is_not_agreement():
    """Bir modelin fikri razılıq deyil.

    Olmasaydı, tək qaçışdan sonra siyahı modelin bütün səhvləri ilə dolardı və
    dataset onun səhvinə uyğunlaşdırılardı.
    """
    items = [item("q1", "A")]
    picks = {"m1": {"q1": "B"}}
    assert find_suspects(items, picks, min_models=2) == []
    assert len(find_suspects(items, picks, min_models=1)) == 1


def test_missing_answers_do_not_count_as_votes():
    items = [item("q1", "A"), item("q2", "A")]
    picks = {"m1": {"q1": "B", "q2": "B"}, "m2": {"q1": "B"}}
    suspects = find_suspects(items, picks)
    assert [s["id"] for s in suspects] == ["q1"]


def test_chance_agreement_falls_sharply_with_more_models():
    """Metodun gücü model sayından asılıdır.

    İki modellə gözlənilən təsadüfi razılıq böyükdür və siqnalı boğur; dörd
    modellə isə kiçilir. Rəqəm buna görə hesabatda verilir.
    """
    two = chance_agreement(2, 521)
    four = chance_agreement(4, 521)
    assert two > 90
    assert four < 10
    assert four < two / 10


def test_permutation_null_accounts_for_letter_bias():
    """Modelin hərf meyli sıfır fərziyyəsinə DAXİL olmalıdır.

    Hər iki model həmişə `D` deyirsə, onlar hər sətirdə birləşir və bu,
    açar haqqında heç nə demir. Kobud düstur bunu görmür, permutasiya görür.
    """
    items = [item(f"q{n}", "A") for n in range(40)]
    picks = {
        "m1": {f"q{n}": "D" for n in range(40)},
        "m2": {f"q{n}": "D" for n in range(40)},
    }
    mean, high = permutation_null(items, picks, n_permutations=50)
    # Hamısı D olduğu üçün qarışdırma heç nəyi dəyişmir: razılıq həmişə tamdır.
    assert mean == 40
    assert high == 40
    # Kobud düstur isə cəmi ~7.5 gözləyir və siqnal varmış kimi görünərdi.
    assert chance_agreement(2, 40) < 10


def test_report_names_the_independence_limit():
    """Hesabat metodun ən zəif fərziyyəsini gizlətməməlidir."""
    items = [item("q1", "A")]
    picks = {"m1": {"q1": "B"}, "m2": {"q1": "B"}}
    text = report(items, picks, find_suspects(items, picks))
    assert "müstəqil" in text or "ailəsindəndir" in text
    assert "hökm deyil" in text
