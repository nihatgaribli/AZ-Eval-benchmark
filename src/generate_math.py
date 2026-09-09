"""Universal riyaziyyat sualları: cavabı hesablanan, yadda saxlanmayan.

    python -m src.generate_math --count 120

NİYƏ MƏHZ BU KATEQORİYA. `mathematics` təbəqəsini iki yerə bölüb ölçdük:

    həqiqi riyaziyyat (8 sual)     EN 62%   AZ 12%   fərq 50 bənd
    Azərbaycan riyaziyyat tarixi   EN 0-15% AZ 0-5%  fərq ~0

Hər üç modeldə eyni mənzərə. Yəni datasetdəki ƏN BÖYÜK dil effekti cəmi səkkiz
suala söykənir, qalan 20 sual isə (akademik harada doğulub) dili yox, cəhaləti
ölçür və nəticəni seyrəldir. Bu modul həmin səkkizliyi böyüdür.

NİYƏ HESABLANIR, YAZILMIR. Cavabı alqoritm çıxarır: sadə ədədlər ələklə,
bucaqlar düsturla, ƏBOB Evklid alqoritmi ilə. Bunun üç nəticəsi var:

  1. Doğruluq QURULUŞCA zəmanətlidir. Əl ilə yazılmış faktda səhv ola bilər və
     yalnız yoxlayan adam onu tutur; hesablanmış faktda səhv üçün yer yoxdur.
  2. Heç bir dil modeli faktı yazmır. README-dəki "no LLM was used to author,
     translate, or answer any dataset item" zəmanəti pozulmur.
  3. Mənbə sitatı tələb olunmur, çünki iddia xarici mənbəyə yox, düstura
     söykənir. `notes` sahəsinə düstur yazılır ki, yoxlana bilsin.

CAVAB SUALIN İÇİNDƏ GÖRÜNMÜR. Bu, təsadüfi deyil: `teorem -> kimin adını
daşıyır` tipli Wikidata şablonu sınandı və atıldı, çünki "Pifaqor teoremi kimin
adını daşıyır?" sualının cavabı sualın özündədir. Buradakı ailələrin heç
birində belə sızma yoxdur.

RƏQƏMLİ CAVAB `aliases_for`-dan KEÇMİR. Həmin funksiya bütün rəqəmləri İL sayır
və "180" üçün "180-ci il" alternativi yaradır. İl sualları üçün bu doğrudur,
kəmiyyət sualları üçün yanlışdır: model "180-ci il" desə, üçbucaq sualı düz
sayılardı. Burada alternativlər ölçü vahidinə görə qurulur.

Nəticə `data/raw/` altına namizəd kimi yazılır və `review.py` axını ilə əl
yoxlamasından keçir; yalnız ondan sonra `build_dataset` onu datasetə buraxır.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.harvest_wikidata import next_free_id
from src.morphology import _ordinal_suffix

#: Sualın dörd sintaktik variantı. Wikidata şablonlarındakı ilə eyni prinsip:
#: eyni fakt fərqli cümlə quruluşlarında soruşulur, yoxsa ölçdüyümüz şey
#: modelin bilikləri yox, bir cümlə qəlibini tanıması olur.
@dataclass(frozen=True)
class Variant:
    az: str
    en: str


@dataclass(frozen=True)
class Family:
    """Bir sual ailəsi: parametr -> (sual, cavab).

    `unit_az` boş deyilsə, cavab kəmiyyətdir və alternativlərə vahidli formalar
    əlavə olunur ("180", "180 dərəcə", "180 dərəcədir").
    """

    name: str
    variants: tuple[Variant, ...]
    answer: Callable[..., int]
    formula: str
    unit_az: str = ""
    unit_en: str = ""
    difficulty: str = "medium"


def _sieve(limit: int) -> list[int]:
    """Eratosfen ələyi. Sadə ədədlər siyahı kimi yadda saxlanmır, hesablanır."""
    flags = bytearray([1]) * (limit + 1)
    flags[0:2] = b"\x00\x00"
    for n in range(2, int(limit**0.5) + 1):
        if flags[n]:
            flags[n * n :: n] = bytearray(len(flags[n * n :: n]))
    return [i for i, ok in enumerate(flags) if ok]


_PRIMES = _sieve(20000)


def _nth_prime(n: int) -> int:
    return _PRIMES[n - 1]


def _next_prime(n: int) -> int:
    return next(p for p in _PRIMES if p > n)


def _divisor_count(n: int) -> int:
    total = 0
    for d in range(1, int(n**0.5) + 1):
        if n % d == 0:
            total += 2 if d != n // d else 1
    return total


def _distinct_prime_factors(n: int) -> int:
    """FƏRQLİ sadə vuruqların sayı: 12 = 2*2*3 üçün cavab 2-dir, 3 deyil."""
    count = 0
    remaining = n
    for prime in _PRIMES:
        if prime * prime > remaining:
            break
        if remaining % prime == 0:
            count += 1
            while remaining % prime == 0:
                remaining //= prime
    return count + (1 if remaining > 1 else 0)


FAMILIES: tuple[Family, ...] = (
    Family(
        name="polygon_angle_sum",
        variants=(
            Variant(
                "{n}-bucağın daxili bucaqlarının cəmi neçə dərəcədir?",
                "What is the sum of the interior angles of {article} {n}-gon?",
            ),
            Variant(
                "{n} tərəfi olan çoxbucaqlının daxili bucaqları cəmi nə qədərdir?",
                "What do the interior angles of a polygon with {n} sides add up to?",
            ),
            Variant(
                "Daxili bucaqlarının cəmini tap: {n}-bucaq.",
                "Find the sum of the interior angles of {article} {n}-gon.",
            ),
            Variant(
                "{n}-bucaqlının bütün daxili bucaqları toplananda neçə dərəcə alınır?",
                "Adding all interior angles of {article} {n}-gon gives how many degrees?",
            ),
        ),
        answer=lambda n: (n - 2) * 180,
        formula="(n-2)*180",
        unit_az="dərəcə",
        unit_en="degrees",
    ),
    Family(
        name="polygon_diagonals",
        variants=(
            Variant(
                "{n}-bucağın neçə diaqonalı var?",
                "How many diagonals does {article} {n}-gon have?",
            ),
            Variant(
                "{n} tərəfi olan çoxbucaqlıda neçə diaqonal çəkmək olar?",
                "How many diagonals can be drawn in a polygon with {n} sides?",
            ),
            Variant(
                "Diaqonallarının sayını tap: {n}-bucaq.",
                "Find the number of diagonals of {article} {n}-gon.",
            ),
            Variant(
                "{n}-bucaqlının diaqonallarının sayı neçədir?",
                "What is the number of diagonals of {article} {n}-gon?",
            ),
        ),
        answer=lambda n: n * (n - 3) // 2,
        formula="n*(n-3)/2",
    ),
    Family(
        name="nth_prime",
        variants=(
            Variant(
                "{n}-{ord} sadə ədəd hansıdır?",
                "What is the {n}th prime number?",
            ),
            Variant(
                "Sadə ədədlər sırasında {n}-{ord} ədəd nədir?",
                "Which number is {n}th in the sequence of primes?",
            ),
            Variant(
                "{n}-{ord} sadə ədədi yaz.",
                "Write the {n}th prime number.",
            ),
            Variant(
                "Kiçikdən böyüyə sıralanmış sadə ədədlərin {n}-{ord}si neçədir?",
                "In primes ordered from smallest, what is the {n}th one?",
            ),
        ),
        answer=_nth_prime,
        formula="sadə ədədlər ələyi, n-ci element",
    ),
    Family(
        name="next_prime",
        variants=(
            Variant(
                "{n}-dən böyük ən kiçik sadə ədəd hansıdır?",
                "What is the smallest prime number greater than {n}?",
            ),
            Variant(
                "{n} ədədindən sonra gələn ilk sadə ədəd nədir?",
                "What is the first prime number after {n}?",
            ),
            Variant(
                "{n}-dən sonrakı sadə ədədi tap.",
                "Find the prime number that comes after {n}.",
            ),
            Variant(
                "{n}-dən böyük sadə ədədlərin ən kiçiyi neçədir?",
                "Among primes greater than {n}, which is the smallest?",
            ),
        ),
        answer=_next_prime,
        formula="n-dən böyük ilk sadə ədəd",
    ),
    Family(
        name="divisor_count",
        variants=(
            Variant(
                "{n} ədədinin neçə böləni var?",
                "How many divisors does {n} have?",
            ),
            Variant(
                "{n}-in bölənlərinin sayı neçədir?",
                "What is the number of divisors of {n}?",
            ),
            Variant(
                "Bölənlərinin sayını tap: {n}.",
                "Find how many divisors {n} has.",
            ),
            Variant(
                "{n} ədədi neçə müxtəlif ədədə tam bölünür?",
                "By how many different numbers is {n} exactly divisible?",
            ),
        ),
        answer=_divisor_count,
        formula="bölənlərin sayı",
        difficulty="hard",
    ),
    Family(
        name="sum_first_n",
        variants=(
            Variant(
                "İlk {n} natural ədədin cəmi neçədir?",
                "What is the sum of the first {n} natural numbers?",
            ),
            Variant(
                "1-dən {n}-ə qədər olan ədədlərin cəmi nə qədərdir?",
                "What is the sum of the numbers from 1 to {n}?",
            ),
            Variant(
                "Cəmi tap: 1 + 2 + ... + {n}.",
                "Find the sum: 1 + 2 + ... + {n}.",
            ),
            Variant(
                "Birdən {n}-ə kimi bütün natural ədədləri toplasaq, neçə alınar?",
                "Adding all natural numbers from one to {n} gives what?",
            ),
        ),
        answer=lambda n: n * (n + 1) // 2,
        formula="n*(n+1)/2",
    ),
    Family(
        name="gcd",
        variants=(
            Variant(
                "{a} və {b} ədədlərinin ən böyük ortaq böləni neçədir?",
                "What is the greatest common divisor of {a} and {b}?",
            ),
            Variant(
                "{a} ilə {b}-nin ƏBOB-u nədir?",
                "What is the GCD of {a} and {b}?",
            ),
            Variant(
                "Ən böyük ortaq bölənini tap: {a}, {b}.",
                "Find the greatest common divisor of {a} and {b}.",
            ),
            Variant(
                "{a} və {b} hansı ən böyük ədədə tam bölünür?",
                "What is the largest number that divides both {a} and {b}?",
            ),
        ),
        answer=lambda a, b: math.gcd(a, b),
        formula="Evklid alqoritmi",
    ),
    Family(
        name="lcm",
        variants=(
            Variant(
                "{a} və {b} ədədlərinin ən kiçik ortaq bölünəni neçədir?",
                "What is the least common multiple of {a} and {b}?",
            ),
            Variant(
                "{a} ilə {b}-nin ƏKOB-u nədir?",
                "What is the LCM of {a} and {b}?",
            ),
            Variant(
                "Ən kiçik ortaq bölünənini tap: {a}, {b}.",
                "Find the least common multiple of {a} and {b}.",
            ),
            Variant(
                "Həm {a}-ə, həm {b}-ə bölünən ən kiçik ədəd hansıdır?",
                "What is the smallest number divisible by both {a} and {b}?",
            ),
        ),
        answer=lambda a, b: a * b // math.gcd(a, b),
        formula="a*b/ƏBOB(a,b)",
    ),
    Family(
        name="factorial",
        variants=(
            Variant(
                "{n} faktorial neçəyə bərabərdir?",
                "What is {n} factorial?",
            ),
            Variant(
                "{n}! ifadəsinin qiyməti nədir?",
                "What is the value of {n}!?",
            ),
            Variant(
                "Faktorialı hesabla: {n}.",
                "Compute the factorial of {n}.",
            ),
            Variant(
                "1-dən {n}-ə qədər bütün ədədlərin hasili neçədir?",
                "What is the product of all numbers from 1 to {n}?",
            ),
        ),
        answer=lambda n: math.factorial(n),
        formula="n!",
    ),
    Family(
        name="perfect_square_root",
        variants=(
            Variant(
                "{n} ədədinin kvadrat kökü neçədir?",
                "What is the square root of {n}?",
            ),
            Variant(
                "Kvadratı {n} olan müsbət ədəd hansıdır?",
                "Which positive number has {n} as its square?",
            ),
            Variant(
                "Kvadrat kökünü tap: {n}.",
                "Find the square root of {n}.",
            ),
            Variant(
                "Hansı ədədi özünə vursaq {n} alınar?",
                "Which number multiplied by itself gives {n}?",
            ),
        ),
        answer=lambda n: math.isqrt(n),
        formula="sqrt(n), n tam kvadrat",
    ),
    #: AŞAĞIDAKILAR İKİNCİ DALĞADIR (2026-09-08). Universal nəzarət təbəqəsini
    #: böyütmək üçün əlavə olundu. Hamısında cavab TAM ƏDƏDDİR və alqoritmlə
    #: hesablanır, yəni birinci dalğa ilə eyni zəmanətləri daşıyır.
    #:
    #: İFADƏ QURULUŞU. Azərbaycan dilində rəqəmə birbaşa yapışan şəkilçi səs
    #: uyumuna görə dəyişir: "7-yə", "8-ə", "9-a". Şablon bunu bilmir və
    #: yanlış forma sualı pozar. Ona görə ifadələr rəqəmdən sonra SABİT söz
    #: gətirir ("{b} ədədinə", "{n} ədədinin"), şəkilçi isə həmin sözə düşür.
    Family(
        name="remainder",
        variants=(
            Variant(
                "{a} ədədini {b} ədədinə böldükdə qalıq neçə olur?",
                "What is the remainder when {a} is divided by {b}?",
            ),
            Variant(
                "{a} sayının {b} sayına bölünməsindən alınan qalıq nədir?",
                "What remainder does {a} leave when divided by {b}?",
            ),
            Variant(
                "Qalığı hesabla: {a} ədədinin {b} ədədinə bölünməsi.",
                "Compute the remainder of {a} divided by {b}.",
            ),
            Variant(
                "{a} ədədi {b} ədədinə bölünəndə nə qədər qalıq qalır?",
                "When {a} is divided by {b}, how much is left over?",
            ),
        ),
        answer=lambda a, b: a % b,
        formula="a mod b",
    ),
    Family(
        name="power",
        variants=(
            Variant(
                "{a} ədədinin {n}-{ord} qüvvəti neçədir?",
                "What is {a} to the power of {n}?",
            ),
            Variant(
                "Əsası {a}, göstəricisi {n} olan qüvvət neçəyə bərabərdir?",
                "What does a power with base {a} and exponent {n} equal?",
            ),
            Variant(
                "Qüvvəti hesabla: əsas {a}, göstərici {n}.",
                "Compute the power: base {a}, exponent {n}.",
            ),
            Variant(
                "{a} ədədinin {n}-{ord} dərəcəsini tap.",
                "Find {a} raised to the {n}th degree.",
            ),
        ),
        answer=lambda a, n: a**n,
        formula="a^n",
    ),
    Family(
        name="digit_sum",
        variants=(
            Variant(
                "{n} ədədinin rəqəmləri cəmi neçədir?",
                "What is the sum of the digits of {n}?",
            ),
            Variant(
                "{n} sayının rəqəmlərini toplasaq nə alınar?",
                "What do you get when you add up the digits of {n}?",
            ),
            Variant(
                "Rəqəmlərinin cəmini tap: {n}.",
                "Find the digit sum of {n}.",
            ),
            Variant(
                "{n} ədədindəki rəqəmlərin cəmi nə qədərdir?",
                "How much do the digits in {n} add up to?",
            ),
        ),
        answer=lambda n: sum(int(d) for d in str(n)),
        formula="rəqəmlərin cəmi",
    ),
    Family(
        name="distinct_prime_factors",
        variants=(
            Variant(
                "{n} ədədinin neçə fərqli sadə böləni var?",
                "How many distinct prime factors does {n} have?",
            ),
            Variant(
                "{n} sayının fərqli sadə vuruqlarının sayı neçədir?",
                "What is the number of distinct prime divisors of {n}?",
            ),
            Variant(
                "Fərqli sadə bölənlərin sayını tap: {n}.",
                "Find how many different primes divide {n}.",
            ),
            Variant(
                "{n} ədədi neçə müxtəlif sadə ədədə bölünür?",
                "By how many different prime numbers is {n} divisible?",
            ),
        ),
        answer=lambda n: _distinct_prime_factors(n),
        formula="fərqli sadə vuruqların sayı",
    ),
    Family(
        name="triangle_third_angle",
        variants=(
            Variant(
                "Üçbucağın iki bucağı {a} və {b} dərəcədirsə, üçüncü bucaq "
                "neçə dərəcədir?",
                "If two angles of a triangle are {a} and {b} degrees, what is "
                "the third angle?",
            ),
            Variant(
                "Bir üçbucaqda bucaqlardan ikisi {a} və {b} dərəcədir. "
                "Qalan bucaq nə qədərdir?",
                "In a triangle, two of the angles are {a} and {b} degrees. "
                "How large is the remaining angle?",
            ),
            #: FİQUR ADI MÜTLƏQ OLMALIDIR. İlk variant belə idi:
            #:     "Üçüncü bucağı tap: 47 dərəcə və 63 dərəcə."
            #: İkinci annotator onu haqlı olaraq rədd etdi: iki bucaq verilib,
            #: amma fiqur deyilmir, yəni "üçüncü bucaq" müəyyən edilmir. Cavab
            #: yalnız ÜÇBUCAQ nəzərdə tutulduqda birmənalıdır.
            #:
            #: Qüsur hər iki dildə idi və üç suala təsir edirdi. Bu, tək sətir
            #: səhvi deyil, ŞABLON səhvidir: bir variant bütün ailəni pozur.
            Variant(
                "Üçbucağın üçüncü bucağını tap: {a} dərəcə və {b} dərəcə.",
                "Find the third angle of a triangle given {a} degrees and "
                "{b} degrees.",
            ),
            Variant(
                "İki bucağı {a} və {b} dərəcə olan üçbucağın digər bucağı "
                "neçə dərəcədir?",
                "A triangle has angles of {a} and {b} degrees; what is its "
                "other angle?",
            ),
        ),
        answer=lambda a, b: 180 - a - b,
        formula="180-a-b",
        unit_az="dərəcə",
        unit_en="degrees",
    ),
    Family(
        name="percent_of",
        variants=(
            Variant(
                "{n} ədədinin {p} faizi neçədir?",
                "What is {p} percent of {n}?",
            ),
            Variant(
                "{n} sayının {p} faizi nə qədər edir?",
                "How much is {p}% of {n}?",
            ),
            Variant(
                "Faizi hesabla: {n} ədədinin {p} faizi.",
                "Compute {p} percent of {n}.",
            ),
            Variant(
                "{n} ədədinin {p} faizi hansı ədəddir?",
                "Which number is {p} percent of {n}?",
            ),
        ),
        answer=lambda n, p: n * p // 100,
        formula="n*p/100",
    ),
    Family(
        name="arithmetic_term",
        variants=(
            Variant(
                "İlk həddi {a}, fərqi {d} olan arifmetik silsilənin "
                "{n}-{ord} həddi neçədir?",
                "What is the {n}th term of an arithmetic sequence with first "
                "term {a} and common difference {d}?",
            ),
            Variant(
                "Arifmetik silsilədə birinci hədd {a}, fərq isə {d} ədədidir. "
                "{n}-{ord} hədd nədir?",
                "In an arithmetic sequence the first term is {a} and the "
                "difference is {d}. What is term number {n}?",
            ),
            Variant(
                "Həddi tap: ilk hədd {a}, fərq {d}, nömrə {n}.",
                "Find the term: first term {a}, difference {d}, index {n}.",
            ),
            Variant(
                "Birinci həddi {a}, fərqi {d} olan silsilədə {n}-{ord} hədd "
                "hansı ədəddir?",
                "Which number is term {n} of a sequence starting at {a} with "
                "step {d}?",
            ),
        ),
        answer=lambda a, d, n: a + (n - 1) * d,
        formula="a+(n-1)*d",
    ),
    Family(
        name="hours_to_seconds",
        variants=(
            Variant(
                "{h} saat neçə saniyədir?",
                "How many seconds are in {h} hours?",
            ),
            Variant(
                "{h} saatda neçə saniyə var?",
                "How many seconds does {h} hours contain?",
            ),
            Variant(
                "Saniyəyə çevir: {h} saat.",
                "Convert {h} hours into seconds.",
            ),
            Variant(
                "{h} saatlıq müddət neçə saniyə edir?",
                "A period of {h} hours equals how many seconds?",
            ),
        ),
        answer=lambda h: h * 3600,
        formula="h*3600",
        unit_az="saniyə",
        unit_en="seconds",
    ),
    Family(
        name="sum_range",
        variants=(
            Variant(
                "{a} ilə {b} arasındakı bütün tam ədədlərin cəmi neçədir "
                "(hər ikisi daxil olmaqla)?",
                "What is the sum of all integers from {a} to {b}, inclusive?",
            ),
            Variant(
                "{a} ədədindən {b} ədədinə qədər bütün tam ədədləri toplasaq, "
                "nə alınar (uc nöqtələr daxildir)?",
                "Adding every integer from {a} through {b}, including both "
                "ends, gives what?",
            ),
            Variant(
                "Cəmi tap: {a} ilə {b} arasındakı tam ədədlər, uclar daxil.",
                "Find the total of the integers between {a} and {b}, ends "
                "included.",
            ),
            Variant(
                "{a} ilə {b} arasındakı tam ədədlərin cəmi hansı ədəddir "
                "(hər ikisi sayılır)?",
                "Which number is the sum of the integers from {a} to {b}, "
                "counting both?",
            ),
        ),
        answer=lambda a, b: (a + b) * (b - a + 1) // 2,
        formula="(a+b)*(b-a+1)/2",
    ),
    Family(
        name="binary_to_decimal",
        variants=(
            Variant(
                "İkilik say sistemində yazılmış {bits} ədədi onluq sistemdə "
                "neçəyə bərabərdir?",
                "The number {bits} is written in binary; what is it in "
                "decimal?",
            ),
            Variant(
                "{bits} ikilik ədədinin onluq qarşılığı nədir?",
                "What is the decimal value of the binary number {bits}?",
            ),
            Variant(
                "Onluq sistemə çevir: ikilik {bits}.",
                "Convert the binary number {bits} to decimal.",
            ),
            Variant(
                "İkilik yazılışı {bits} olan ədəd onluq sistemdə hansıdır?",
                "Which decimal number has the binary representation {bits}?",
            ),
        ),
        answer=lambda bits: int(str(bits), 2),
        formula="ikilikdən onluğa",
    ),
)


def _english_article(number: int) -> str:
    """"an 8-gon", "an 11-gon", amma "a 15-gon".

    Artikl yazılışdan yox, OXUNUŞDAN asılıdır: səkkiz "eight" kimi saitlə
    başlayır, on bir "eleven" kimi. Səhv artikl ingilis sualını pozar və
    AZ/EN müqayisəsində ingilis tərəfi süni şəkildə çətinləşdirərdi.
    """
    text = str(number)
    return "an" if text[0] == "8" or text[:2] in {"11", "18"} else "a"


def _quantity_aliases(value: int, unit_az: str) -> list[str]:
    """Kəmiyyət cavabı üçün alternativlər.

    `morphology.aliases_for` BURADA ÇAĞIRILMIR: o, rəqəmi il sayır və "180-ci
    il" kimi mənasız forma verir. Kəmiyyətdə qəbul edilən şey rəqəmin özü və
    vahidli yazılışdır.
    """
    if not unit_az:
        return []
    return [f"{value} {unit_az}", f"{value} {unit_az}dir"]


def _parameters(family: Family, rng: random.Random) -> tuple[dict[str, int], ...]:
    """Ailə üçün parametr hovuzu.

    Trivial hallar QƏSDƏN kənardadır: üçbucaq (n=3) və kvadrat (n=4) hər
    dərslikdə var, model onları yadda saxlaya bilər. Hovuz elə seçilir ki,
    cavab hesablanmadan bilinməsin.
    """
    if family.name in {"polygon_angle_sum", "polygon_diagonals"}:
        return tuple({"n": n} for n in range(5, 21))
    if family.name == "nth_prime":
        return tuple({"n": n} for n in range(4, 26))
    if family.name == "next_prime":
        return tuple({"n": n} for n in (14, 24, 32, 38, 48, 62, 68, 80, 90, 100, 114, 128))
    if family.name == "divisor_count":
        return tuple({"n": n} for n in (36, 48, 60, 72, 84, 96, 100, 120, 144, 180, 196, 210))
    if family.name == "sum_first_n":
        return tuple({"n": n} for n in range(10, 60, 5))
    if family.name in {"gcd", "lcm"}:
        pairs = [(12, 18), (24, 36), (15, 25), (40, 60), (14, 21), (45, 75),
                 (16, 28), (30, 42), (27, 36), (33, 55), (26, 39), (32, 48)]
        return tuple({"a": a, "b": b} for a, b in pairs)
    if family.name == "factorial":
        return tuple({"n": n} for n in range(5, 11))
    if family.name == "perfect_square_root":
        return tuple({"n": k * k} for k in range(11, 31))

    # İkinci dalğa. Hovuzlar ƏL İLƏ seçilib, təsadüfi yaradılmayıb: cavabın
    # tam ədəd çıxması, mənfi olmaması və trivial olmaması hər ailədə fərqli
    # şərtdir və avtomatik generasiya onların hamısını tuta bilməzdi.
    if family.name == "remainder":
        pairs = [(100, 7), (247, 9), (365, 11), (512, 13), (729, 17), (853, 19),
                 (1000, 23), (444, 7), (628, 15), (777, 29), (999, 31), (555, 14)]
        return tuple({"a": a, "b": b} for a, b in pairs)
    if family.name == "power":
        pairs = [(2, 10), (3, 5), (5, 4), (7, 3), (2, 12), (4, 5),
                 (6, 4), (3, 7), (9, 3), (11, 3), (2, 15), (5, 5)]
        return tuple({"a": a, "n": n} for a, n in pairs)
    if family.name == "digit_sum":
        return tuple(
            {"n": n}
            for n in (4728, 9315, 6042, 8879, 12345, 70706,
                      55555, 91827, 30604, 46913, 88041, 27356)
        )
    if family.name == "distinct_prime_factors":
        return tuple(
            {"n": n}
            # Cavab kiçik rəqəmdir (2-5) və ədədin öz rəqəmləri arasında
            # görünsə, sətir "cavab sualdadır" süzgəcinə düşür. 360 -> 3,
            # 924 -> 4, 1430 -> 4, 546 -> 4 məhz belə itirdi. Hovuz onların
            # yerinə rəqəmi üst-üstə düşməyən ədədlərlə dolduruldu.
            for n in (66, 210, 1155, 190, 630, 2310,
                      1001, 858, 2730, 792, 1122, 1729)
        )
    if family.name == "triangle_third_angle":
        # Cəmi 180-dən kiçik olmalıdır, yoxsa üçüncü bucaq mənfi çıxar.
        pairs = [(40, 75), (55, 60), (32, 88), (47, 63), (25, 110), (38, 52),
                 (72, 66), (29, 81), (105, 41), (58, 77), (36, 94), (61, 49)]
        return tuple({"a": a, "b": b} for a, b in pairs)
    if family.name == "percent_of":
        # n*p 100-ə tam bölünməlidir, yoxsa cavab kəsr olar.
        pairs = [(240, 15), (180, 20), (350, 40), (120, 25), (500, 12), (400, 35),
                 (250, 16), (600, 45), (800, 5), (150, 60), (900, 30), (450, 80)]
        return tuple({"n": n, "p": p} for n, p in pairs)
    if family.name == "arithmetic_term":
        triples = [(5, 3, 20), (7, 4, 15), (2, 9, 12), (11, 6, 18), (100, 5, 11),
                   (13, 8, 10), (4, 12, 16), (25, 3, 22), (9, 11, 13), (6, 7, 25),
                   (50, 4, 17), (17, 5, 19)]
        return tuple({"a": a, "d": d, "n": n} for a, d, n in triples)
    if family.name == "hours_to_seconds":
        return tuple({"h": h} for h in (2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 20, 24))
    if family.name == "sum_range":
        pairs = [(10, 20), (5, 25), (12, 30), (7, 17), (21, 40), (1, 50),
                 (15, 35), (8, 22), (33, 44), (11, 29), (16, 48), (26, 39)]
        return tuple({"a": a, "b": b} for a, b in pairs)
    if family.name == "binary_to_decimal":
        # Parametr İKİLİK yazılışdır, onluq dəyər deyil: sual onu olduğu kimi
        # göstərir, cavab isə `int(str(bits), 2)` ilə hesablanır.
        return tuple(
            {"bits": b}
            for b in (1011, 11010, 100111, 1101101, 10000, 111111,
                      1010101, 110011, 10011010, 1111000, 101101, 11100011)
        )
    raise ValueError(f"parametr hovuzu təyin olunmayıb: {family.name}")


def generate(
    count: int,
    start_id: int,
    seed: int = 0,
    families: Sequence[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """Namizəd sətirlərini verir.

    Ailələr NÖVBƏ İLƏ gəzilir, ardıcıl yox: qaçış yarımçıq kəsilsə də dataset
    bir ailəyə sürüşmüş qalmır. Eyni səbəbdən parametrlər qarışdırılır, amma
    sabit seed ilə, yəni nəticə təkrarlanır.

    `families` verilibsə, yalnız adı sadalanan ailələr işlədilir. Bu, İKİNCİ
    DALĞA üçün lazımdır: birinci dalğanın 120 sualı artıq datasetdədir və
    onları yenidən istehsal etmək təkrar sətirlər yaradardı.
    """
    rng = random.Random(seed)
    chosen = FAMILIES
    if families is not None:
        wanted = set(families)
        unknown = wanted - {f.name for f in FAMILIES}
        if unknown:
            raise ValueError(f"tanınmayan ailə: {sorted(unknown)}")
        chosen = tuple(f for f in FAMILIES if f.name in wanted)

    pools = []
    for family in chosen:
        params = list(_parameters(family, rng))
        rng.shuffle(params)
        pools.append((family, params))

    produced = 0
    round_index = 0
    while produced < count:
        progressed = False
        for family, params in pools:
            if round_index >= len(params) or produced >= count:
                continue
            values = params[round_index]
            variant = family.variants[round_index % len(family.variants)]
            answer = family.answer(**values)
            wording = dict(values)
            if "n" in values:
                wording["ord"] = _ordinal_suffix(str(values["n"]))
                wording["article"] = _english_article(values["n"])
            question_az = variant.az.format(**wording)

            # Cavab sualın içində görünməməlidir. Parametr təsadüfən cavaba
            # bərabər ola bilər (məsələn ƏBOB(a,b) = a), belə sətir atılır.
            if str(answer) in question_az.replace(" ", ""):
                continue

            yield {
                "id": f"az-{start_id + produced}",
                "question_az": question_az,
                "question_en": variant.en.format(**wording),
                "answer": str(answer),
                "answer_en": (
                    f"{answer} {family.unit_en}" if family.unit_en else str(answer)
                ),
                "answer_aliases": _quantity_aliases(answer, family.unit_az),
                "category": "mathematics",
                "source": f"hesablanıb: {family.formula}",
                "difficulty": family.difficulty,
                "provenance": "computed-template",
                "verified_by": "pending",
                "notes": f"ailə={family.name}, parametr={values}, düstur={family.formula}",
            }
            produced += 1
            progressed = True
        round_index += 1
        if not progressed:
            break


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="generate_math",
        description="Cavabı hesablanan universal riyaziyyat sualları",
    )
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--out", type=Path, default=Path("data/raw/math_computed.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--start-id", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--families",
        nargs="+",
        default=None,
        help="yalnız bu ailələr (ikinci dalğa üçün); verilməsə hamısı",
    )
    args = parser.parse_args(argv)

    if args.out.exists():
        raise SystemExit(
            f"{args.out} artıq var. Əl yoxlamasından keçmiş faylın üstündən "
            "yazmaq olmaz; başqa ad ver və ya faylı özün sil."
        )

    start_id = (
        args.start_id
        if args.start_id is not None
        else next_free_id(args.raw_dir, args.dataset)
    )
    rows = list(generate(args.count, start_id, args.seed, args.families))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_family: dict[str, int] = {}
    for row in rows:
        family = row["notes"].split(",")[0].removeprefix("ailə=")
        by_family[family] = by_family.get(family, 0) + 1

    print(f"{len(rows)} namizəd -> {args.out}  (az-{start_id} ilə başlayır)")
    for name, total in sorted(by_family.items()):
        print(f"  {total:3}  {name}")
    print("\nNövbəti addım: python -m src.review --input " + str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
