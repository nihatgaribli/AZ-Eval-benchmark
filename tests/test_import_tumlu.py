"""import_tumlu.py üçün testlər.

Bu modul XARİCİ dataseti içəri buraxır, ona görə testlərin əsas işi mənbənin
ölçülmüş qüsurlarının içəri sızmadığını təsdiqləməkdir.
"""

from __future__ import annotations

import json
from collections import Counter

import pytest

from src.import_tumlu import (
    LETTERS,
    Item,
    audit_report,
    inspect,
    to_short_answer,
)


def row(question, choices, answer, subject="Maths", split="test"):
    return {
        "question": question,
        "choices": list(choices),
        "answer": answer,
        "subject": subject,
        "_split": split,
    }


GOOD = row(
    "Bir avtomobil 2 saatda 100 km yol getmişdir. Sürəti nə qədərdir?",
    ["50 km/saat", "40 km/saat", "60 km/saat", "25 km/saat"],
    "A",
)


def codes(item: Item) -> set[str]:
    return {issue.code for issue in item.issues}


def many(count: int):
    """Fərqli mətnli təmiz sətirlər.

    Eyni sual təkrarlansa, `duplicate_question` yoxlaması onu haqlı olaraq
    tutar; buradakı məqsəd isə mövqe balansını yoxlamaqdır.
    """
    return [
        row(
            f"Bir avtomobil {n} saatda 100 km yol getmişdir. Sürəti nə qədərdir?",
            ["50 km/saat", "40 km/saat", "60 km/saat", "25 km/saat"],
            "A",
        )
        for n in range(2, count + 2)
    ]


def test_clean_row_has_no_issues():
    (item,) = inspect([GOOD])
    assert item.issues == []
    assert item.usable
    assert item.answer_text == "50 km/saat"


def test_comma_split_is_detected():
    """`['-0,', '5', ...]` mənbədəki onluq vergülün parçalanmasıdır.

    Azərbaycan dilində onluq ayırıcı vergüldür və toplayan skript variantları
    ondan bölüb. Belə sətir qısa cavaba çevrilsə, cavab `-0,` olardı.
    """
    (item,) = inspect(
        [row("Vektorlar perpendikulyardırsa, x neçədir? Hesablayın.",
             ["-0,", "5", "-1", "0,"], "A")]
    )
    assert "comma_split" in codes(item)


def test_broken_decimal_in_question_is_detected():
    (item,) = inspect(
        [row("Tili 0, 8 m olan kubun səthinin sahəsini hesablayın",
             ["1", "2", "3", "4"], "A")]
    )
    assert "broken_decimal" in codes(item)


def test_duplicate_choices_are_detected():
    (item,) = inspect(
        [row("Bu sual kifayət qədər uzundur ki, qısalıq bayrağı qalxmasın?",
             ["1", "2", "2", "4"], "A")]
    )
    assert "duplicate_choice" in codes(item)


def test_too_short_question_is_detected():
    """`Kənar vahid hansıdır?` kontekstsiz anlaşılmır."""
    (item,) = inspect([row("Kənar vahid hansıdır?", ["a", "b", "c", "d"], "A")])
    assert "too_short" in codes(item)


def test_meta_answer_is_detected():
    """`Heç biri` variantlara istinad edir, variantsız mənasız qalır."""
    (item,) = inspect(
        [row("Hansı sadə mexanizm işdə qazanc verir və niyə belədir?",
             ["Linq", "Mail müstəvi", "Hidravlik pres", "Heç biri"], "D")]
    )
    assert "meta_answer" in codes(item)


def test_formula_answer_is_detected():
    """`q=it` doğrudur, amma model `I=q/t` yaza bilər.

    İkisi eyni fizikadır və sətir müqayisəsi onları ayırd edə bilmir, ona görə
    belə sətir qısa cavab dəstinə buraxılmır.
    """
    (item,) = inspect(
        [row("Cərəyan şiddətini hansı düstur ifadə edir, yazın?",
             ["a=fs", "q=it", "b=lm", "p=mv"], "B")]
    )
    assert "formula_answer" in codes(item)


def test_enum_answer_is_detected():
    (item,) = inspect(
        [row("Verilmiş düsturlardan hansılar elektrik sahəsini xarakterizə edir?",
             ["1,2,3", "2,3,4", "1,2,3,4", "2,4"], "C")]
    )
    assert "enum_answer" in codes(item)


def test_flawed_rows_never_reach_the_output():
    source = [
        GOOD,
        row("Tili 0, 8 m olan kubun səthinin sahəsini hesablayın",
            ["1", "2", "3", "4"], "A"),
        row("Kənar vahid hansıdır?", ["a", "b", "c", "d"], "A"),
    ]
    items = inspect(source)
    out = to_short_answer([i for i in items if i.usable], start_id=1)
    assert len(out) == 1
    assert out[0]["question_az"] == GOOD["question"]


def test_answer_positions_are_uniform_by_construction():
    """Mənbədə cavabların 42%-i D idi. Çıxışda paylanma bərabər olmalıdır.

    Sadəcə qarışdırmaq bunu ZƏMANƏT ETMİR, ona görə doğru cavab növbə ilə
    mövqelərə qoyulur.
    """
    items = inspect(many(40))
    out = to_short_answer(items, start_id=1)
    counts = Counter(r["answer_letter"] for r in out)
    assert set(counts) == set(LETTERS)
    assert max(counts.values()) - min(counts.values()) <= 1


def test_answer_stays_among_the_choices():
    items = inspect(many(12))
    for r in to_short_answer(items, start_id=1):
        assert r["answer"] in r["choices"]
        assert r["choices"][LETTERS.index(r["answer_letter"])] == r["answer"]
        assert len(r["choices"]) == 4
        assert len(set(r["choices"])) == 4


def test_glued_unit_gets_a_spaced_alias():
    """`0.25kN` cavabına model `0.25 kN` yazır; normalizasiya boşluq əlavə etmir."""
    items = inspect(
        [row("Yayın sərtliyi nə qədərdir, hesablayıb yazın?",
             ["0.25kN", "1kN", "2kN", "3kN"], "A")]
    )
    (out,) = to_short_answer(items, start_id=1)
    assert "0.25 kN" in out["answer_aliases"]


def test_output_has_no_english_side():
    """İngilis sahəsi QƏSDƏN yoxdur.

    Onu qurmaq tərcümə deməkdir və README-dəki "no LLM was used to author,
    translate, or answer any dataset item" zəmanətini pozardı. Bu fayl
    `build_dataset`-ə verilmir; ayrı dəstdir və ayrı suala cavab verir.
    """
    (out,) = to_short_answer(inspect([GOOD]), start_id=1)
    assert "question_en" not in out
    assert "answer_en" not in out


def test_output_carries_attribution():
    """CC BY 4.0 atribusiya tələb edir, ona görə sitat hər sətirdədir."""
    (out,) = to_short_answer(inspect([GOOD]), start_id=1)
    assert "TUMLU" in out["citation"]
    assert "CC BY 4.0" in out["source"]
    assert out["provenance"] == "tumlu-import"
    assert out["verified_by"] == "pending"


def test_audit_report_states_the_position_bias():
    source = [row(r["question"], r["choices"], "D") for r in many(10)]
    report = audit_report(inspect(source))
    assert "chi2" in report
    assert "25.0%" in report


def test_unit_slash_is_not_a_formula():
    """`km/saat` vahiddir, `mgh/2` ifadədir.

    Əvvəlki qayda hər kəsr xəttini düstur sayırdı və `23km/saat` kimi tam
    ölçülə bilən cavabları da atırdı. Ayırd etmə əlaməti kəsr xəttinin iki
    tərəfidir: hərf/hərf vahiddir, rəqəm iştirak edirsə ifadədir.
    """
    unit = inspect(
        [row("Velosipedçi 2 saatda 46 km getmişdir. Sürəti nə qədərdir?",
             ["23km/saat", "5km/saat", "14km/saat", "26km/saat"], "A")]
    )[0]
    assert "formula_answer" not in codes(unit)

    expression = inspect(
        [row("Cismin potensial enerjisinin yarısı neçəyə bərabərdir, yazın?",
             ["mgh/2", "mgh", "2mgh", "mgh/4"], "A")]
    )[0]
    assert "formula_answer" in codes(expression)


def test_glued_unit_alias_works_mid_string():
    """`23km/saat` -> `23 km/saat`: yapışıqlıq sətrin sonunda deyil."""
    (out,) = to_short_answer(
        inspect([row("Velosipedçi 2 saatda 46 km getmişdir. Sürəti nə qədərdir?",
                     ["23km/saat", "5km/saat", "14km/saat", "26km/saat"], "A")]),
        start_id=1,
    )
    assert out["answer_aliases"] == ["23 km/saat"]


def test_question_referencing_the_options_is_detected():
    """Sual variantlara istinad edirsə, variantsız CAVABSIZ qalır.

    "Aşağıdakılardan hansı saf maddədir?" -> "Oksigen". Saf maddə minlərlədir.
    Çoxvariantlı testdə sual qüsursuzdur; qısa cavabda ölçülən şey bilik yox,
    təxmindir.
    """
    for text in (
        "Aşağıdakılardan hansı saf maddədir və niyə belə hesab olunur?",
        "Biri skalyar kəmiyyətdir, hansıdır və səbəbini izah edin:",
        "Azərbaycan suda bu ölkə ilə həmsərhəd deyil",
        "Hansı sırada yalnız bərk halda olan qeyri-metallar verilmişdir?",
        "Aromatik karbohidrogen olmayan maddəni seçin, o deyil",
    ):
        (item,) = inspect([row(text, ["a", "b", "c", "d"], "A")])
        assert "list_reference" in codes(item), text


def test_ordinary_question_is_not_flagged_as_list_reference():
    """Qayda geniş tutulub, amma normal sualı tutmamalıdır."""
    for text in (
        "Türkiyənin milli pul vahidi hansıdır və nə vaxt qəbul edilib?",
        "Dizenteriya amöbü hansı xəstəliyi əmələ gətirə bilər?",
        "Həqiqi meyvələr hansı meyvələrə deyilir, izah edin?",
    ):
        (item,) = inspect([row(text, ["a", "b", "c", "d"], "A")])
        assert "list_reference" not in codes(item), text


def test_roman_numeral_enumeration_is_detected():
    """`II,III,IV` sual mətnindəki bəndlərə istinad edir."""
    (item,) = inspect(
        [row("Metan molekulu haqqında deyilənlərdən hansılar doğrudur, seçin?",
             ["I, II", "II,III,IV", "I, IV", "III"], "B")]
    )
    assert "enum_answer" in codes(item)


def test_answer_inside_the_question_is_detected():
    """Cavab sualın içindədirsə, model onu bilmədən köçürə bilər."""
    (item,) = inspect(
        [row("Qəznəvi dövlətinin paytaxtı Qəznə şəhəri olmuşdurmu, hansıdır?",
             ["Qəznə", "Bağdad", "Təbriz", "Şiraz"], "A")]
    )
    assert "answer_in_question" in codes(item)


def test_repeated_question_is_flagged_once():
    """İkinci nüsxə işarələnir, birincisi qalır."""
    text = "Hansı söz ahəng qanununa tabe deyil, cavabı yazın?"
    first, second = inspect([row(text, ["a", "b", "c", "d"], "A")] * 2)
    assert "duplicate_question" not in codes(first)
    assert "duplicate_question" in codes(second)
