"""generate_math.py üçün testlər.

Bu modulun bütün dəyəri bir iddiaya söykənir: cavab hesablanır, ona görə
səhv ola bilməz. Test məhz həmin iddianı yoxlayır və bunu MÜSTƏQİL yolla edir,
yəni modulun öz düsturunu təkrar çağırmaqla yox.
"""

from __future__ import annotations

import json
import math

import pytest

from src.build_dataset import CATEGORIES, PROVENANCE_STATES, VERIFICATION_STATES
from src.generate_math import (
    FAMILIES,
    _english_article,
    _next_prime,
    _nth_prime,
    _quantity_aliases,
    _sieve,
    generate,
)
from src.morphology import aliases_for


def rows(count: int = 120):
    return list(generate(count, start_id=1, seed=0))


def test_sieve_matches_known_primes():
    """Ələk müstəqil siyahı ilə tutuşdurulur."""
    assert _sieve(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def test_nth_prime_and_next_prime():
    assert [_nth_prime(i) for i in range(1, 9)] == [2, 3, 5, 7, 11, 13, 17, 19]
    assert _next_prime(14) == 17
    assert _next_prime(100) == 101


def test_every_answer_recomputes_from_the_notes():
    """Hər sətrin cavabı `notes`-dakı parametrdən yenidən çıxarılır.

    Burada QƏSDƏN ikinci implementasiya işlədilir (`math` modulu, sadə döngə),
    çünki modulun öz funksiyasını çağırmaq eyni səhvi iki dəfə təkrarlamaqdan
    başqa bir şey olmazdı.
    """
    checks = {
        "polygon_angle_sum": lambda v: (v["n"] - 2) * 180,
        "polygon_diagonals": lambda v: v["n"] * (v["n"] - 3) // 2,
        "sum_first_n": lambda v: sum(range(1, v["n"] + 1)),
        "factorial": lambda v: math.factorial(v["n"]),
        "perfect_square_root": lambda v: math.isqrt(v["n"]),
        "gcd": lambda v: math.gcd(v["a"], v["b"]),
        "lcm": lambda v: v["a"] * v["b"] // math.gcd(v["a"], v["b"]),
        "divisor_count": lambda v: sum(
            1 for d in range(1, v["n"] + 1) if v["n"] % d == 0
        ),
        "nth_prime": lambda v: _sieve(10000)[v["n"] - 1],
        "next_prime": lambda v: next(p for p in _sieve(10000) if p > v["n"]),
        # İkinci dalğa. Hər biri modulda işlədilməyən YOLLA hesablanır:
        # `%` əvəzinə çıxma, qapalı düstur əvəzinə döngə, `int(x, 2)` əvəzinə
        # bit-bit toplama. Eyni ifadəni təkrarlamaq yoxlama sayılmazdı.
        "remainder": lambda v: v["a"] - (v["a"] // v["b"]) * v["b"],
        "power": lambda v: math.prod([v["a"]] * v["n"]),
        "digit_sum": lambda v: _digit_sum_by_division(v["n"]),
        "distinct_prime_factors": lambda v: len(
            {p for p in _sieve(3000) if v["n"] % p == 0}
        ),
        "triangle_third_angle": lambda v: 180 - sum([v["a"], v["b"]]),
        "percent_of": lambda v: round(v["n"] * v["p"] / 100),
        "arithmetic_term": lambda v: _walk_sequence(v["a"], v["d"], v["n"]),
        "hours_to_seconds": lambda v: v["h"] * 60 * 60,
        "sum_range": lambda v: sum(range(v["a"], v["b"] + 1)),
        "binary_to_decimal": lambda v: _bits_to_int(str(v["bits"])),
    }
    for row in rows():
        family = row["notes"].split(",")[0].removeprefix("ailə=")
        values = eval(row["notes"].split("parametr=")[1].split(", düstur=")[0])
        assert int(row["answer"]) == checks[family](values), row["id"]


def _digit_sum_by_division(n: int) -> int:
    """Rəqəmləri sətrə çevirmədən, bölmə ilə toplayır."""
    total = 0
    while n:
        total += n % 10
        n //= 10
    return total


def _walk_sequence(first: int, step: int, index: int) -> int:
    """Qapalı düstur yox, addım-addım gəzir."""
    value = first
    for _ in range(index - 1):
        value += step
    return value


def _bits_to_int(bits: str) -> int:
    """`int(bits, 2)` işlətmədən, bit-bit."""
    value = 0
    for character in bits:
        value = value * 2 + int(character)
    return value


def test_answer_never_appears_in_the_question():
    """Cavab sualın içində görünməməlidir.

    `teorem -> kimin adını daşıyır` şablonu məhz buna görə atılmışdı:
    "Pifaqor teoremi kimin adını daşıyır?" sualı cavabı özü verir.
    """
    for row in rows():
        assert row["answer"] not in row["question_az"].replace(" ", ""), row["id"]
        assert row["answer"] not in row["question_en"].replace(" ", ""), row["id"]


def test_quantity_aliases_are_not_year_forms():
    """Kəmiyyət cavabı İL kimi hallanmamalıdır.

    `morphology.aliases_for("180")` "180-ci il" verir, çünki bütün rəqəmləri il
    sayır. İl sualında bu doğrudur, üçbucaq sualında yanlışdır: model "180-ci
    il" cavabını versə, sual düz sayılardı.
    """
    assert any("il" in form.split() for form in aliases_for("180"))
    for form in _quantity_aliases(180, "dərəcə"):
        assert "-ci il" not in form
        assert "-cı il" not in form
    assert _quantity_aliases(20, "") == []


def test_generated_rows_carry_no_year_aliases():
    for row in rows():
        for form in row["answer_aliases"]:
            assert "-ci il" not in form and "-cı il" not in form, row["id"]


def test_ordinal_suffix_follows_the_number():
    """6 -> altıncı -> "6-cı", 7 -> yeddinci -> "7-ci"."""
    questions = " ".join(r["question_az"] for r in rows())
    assert "6-ci " not in questions
    if "6-" in questions:
        assert "6-cı" in questions


def test_english_article_follows_pronunciation():
    assert _english_article(8) == "an"
    assert _english_article(11) == "an"
    assert _english_article(18) == "an"
    assert _english_article(15) == "a"
    assert _english_article(5) == "a"


def test_rows_pass_the_schema_contract():
    for row in rows():
        assert row["category"] in CATEGORIES
        assert row["provenance"] in PROVENANCE_STATES
        assert row["verified_by"] in VERIFICATION_STATES
        assert row["verified_by"] != "human", "əl yoxlaması atlana bilməz"
        assert row["question_az"] and row["question_en"]
        assert row["answer"] and row["answer_en"]


def test_ids_are_unique_and_sequential():
    produced = rows(60)
    ids = [r["id"] for r in produced]
    assert len(set(ids)) == len(ids)
    assert ids[0] == "az-1"


def test_generation_is_deterministic():
    """Sabit seed eyni dəsti verir, yoxsa nəticə təkrar istehsal edilə bilməz."""
    assert json.dumps(rows(40)) == json.dumps(rows(40))


def test_every_family_is_reachable():
    """Ailələr növbə ilə gəzilir, biri kölgədə qalmamalıdır."""
    families = {r["notes"].split(",")[0].removeprefix("ailə=") for r in rows()}
    assert families == {f.name for f in FAMILIES}


def test_trivial_polygons_are_excluded():
    """Üçbucaq və kvadrat ÇOXBUCAQLI ailələrinin hovuzunda olmamalıdır.

    Süzgəc AİLƏ ADINA görədir, sualdakı "bucaq" sözünə görə yox. Söz süzgəci
    `triangle_third_angle` ailəsini də tuturdu, halbuki orada üçbucaq olması
    problem deyil: cavab verilən iki bucaqdan asılıdır, fiqurun özündən yox,
    yəni əzbərlənə bilməz. Qayda çoxbucaqlı düsturlarına aiddir.
    """
    polygon_families = {"polygon_angle_sum", "polygon_diagonals"}
    seen = 0
    for row in rows():
        family = row["notes"].split(",")[0].removeprefix("ailə=")
        if family in polygon_families:
            values = eval(row["notes"].split("parametr=")[1].split(", düstur=")[0])
            assert values["n"] >= 5, row["id"]
            seen += 1
    assert seen > 0, "çoxbucaqlı sətri tapılmadı, test heç nə yoxlamayıb"


@pytest.mark.parametrize("family", FAMILIES, ids=lambda f: f.name)
def test_each_family_has_four_variants(family):
    """Dörd sintaktik variant Wikidata şablonları ilə eyni qaydadır.

    Tək variant olsaydı, ölçdüyümüz şey biliyin özü yox, modelin bir cümlə
    qəlibini tanıması olardı.
    """
    assert len(family.variants) == 4
    assert len({v.az for v in family.variants}) == 4
    assert len({v.en for v in family.variants}) == 4
