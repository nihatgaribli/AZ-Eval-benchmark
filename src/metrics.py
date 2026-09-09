"""Qiymətləndirmə metrikləri: normalizasiya, exact match, token F1, bootstrap CI.

Dizayn qərarı — niyə bir yox, üç normalizasiya rejimi var:

Azərbaycan dili aqlütinativdir. "Bakı" və "Bakıda" exact match-də 0 alır, halbuki
model sualı düzgün cavablandırıb. Eyni şəkilde model "Gence" yazsa (diakritiksiz),
faktual olaraq haqlıdır amma string kimi səhvdir. Bu iki hadisəni bir metrikaya
qatsaq, RQ1-in rəqəmi "model nə qədər bilir" yox, "model nə qədər səliqəli yazır"
olur.

Ona görə hər metrika üç rejimdə hesablanır və üçü də hesabatda verilir:

    STRICT   — yalnız kiçik hərf + durğu işarəsi + boşluq normalizasiyası
    MORPH    — STRICT + hal/mənsubiyyət/cəm şəkilçilərinin evristik kəsilməsi
    LENIENT  — MORPH + diakritiklərin qatlanması (ə->e, ğ->g, ...)
    TRANSLIT — LENIENT + kirildən latına transliterasiya

    STRICT  -> MORPH    = xətanın nə qədəri morfologiyadandır
    MORPH   -> LENIENT  = xətanın nə qədəri diakritikadandır
    LENIENT -> TRANSLIT = xətanın nə qədəri YAZI SİSTEMİNDƏNDİR

Üç fərq RQ3-ün (xətalar harada cəmlənir) birbaşa kəmiyyət cavabıdır.

Sonuncu rejim empirik zərurətdən doğdu: qazax dilinə köklənmiş `Qolda-AVL-5B`
azərbaycan suallarının 85%-inə KİRİL əlifbası ilə cavab verir ("Париж",
"Мәскеу") — cavab məzmunca doğru, yazılışı yanlışdır. Transliterasiya olmadan
onun balı biliyi yox, orfoqrafiyanı ölçür.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace

import numpy as np

__all__ = [
    "NormalizationConfig",
    "STRICT",
    "MORPH",
    "LENIENT",
    "TRANSLIT",
    "MODES",
    "az_lower",
    "fold_diacritics",
    "transliterate_cyrillic",
    "strip_suffixes",
    "normalize",
    "tokenize",
    "exact_match",
    "token_f1",
    "score_example",
    "BootstrapResult",
    "bootstrap_ci",
    "PairedResult",
    "paired_bootstrap_diff",
    "paired_permutation_test",
    "compare_paired",
    "holm_correction",
    "format_ci",
]


# --------------------------------------------------------------------------
# Normalizasiya
# --------------------------------------------------------------------------

# Azərbaycan diakritikləri -> ASCII qarşılıqları (yalnız LENIENT rejimdə).
_DIACRITIC_MAP = str.maketrans(
    {
        "ə": "e",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "ç": "c",
        "Ə": "E",
        "Ğ": "G",
        # Nöqtəli baş `İ` (U+0130) -> `I`. Nöqtəsiz baş `I` onsuz da ASCII `I`
        # ilə eyni koddur, ona görə ayrıca sətir lazım deyil.
        "İ": "I",
        "Ö": "O",
        "Ş": "S",
        "Ü": "U",
        "Ç": "C",
    }
)

# Azərbaycan/türk kiçiltmə qaydası: I -> ı, İ -> i.
# Python-un standart .lower() metodu 'I' -> 'i' (səhv) və
# 'İ' -> 'i' + U+0307 birləşən nöqtə (iki simvol, səhv) verir.
_CASE_FIX = str.maketrans({"I": "ı", "İ": "i"})

_VOWELS = frozenset("aeəıioöuü")

# Şəkilçilər — uzundan qısaya doğru sıralanmalıdır, çünki kəsmə ilk uyğunluqda
# dayanır. Kəsmə iterativdir: şəhər+lər+də -> şəhər (iki addımda).
#
# `n` bağlayıcı samitli variantlar (ndan, ndə, nın, na, nı ...) QƏSDƏN yoxdur.
# Onlar mənsubiyyət + hal birləşməsidir ("evindən" = ev+in+dən) və aradakı forma
# ("evin") özü siyahıdadır, ona görə iterativ kəsmə onları iki addımda açır.
# Siyahıda saxlansaydılar, uzundan-qısaya qayda ucbatından `n` ilə bitən kökün
# öz samiti yeyilirdi: "Naxçıvanın" -> "naxçıva" -> "naxçıv", halbuki etalon
# "Naxçıvan" olduğu kimi qalırdı — yəni normalizasiya DOĞRU cavabı itirirdi.
#
# `sı/si/su/sü` və `ya/yə` isə saxlanılır, çünki onların aralıq forması ("qapıs",
# "bakıy") şəkilçi deyil — yəni açılma yolu yoxdur. Bunun qiyməti odur ki, `s`
# və ya `y` ilə bitən köklərdə eyni problem qalır ("avtobusu" -> "avtob").
# Bax `tests/test_metrics.py::test_known_stripping_limitations`.
_SUFFIXES: tuple[str, ...] = (
    # çıxışlıq
    "dan", "dən",
    # cəm
    "lar", "lər",
    # birgəlik
    "ıla", "ilə", "ula", "ülə",
    # yerlik / birgəlik
    "da", "də", "la", "lə",
    # yiyəlik (qısa)
    "ın", "in", "un", "ün",
    # mənsubiyyət III şəxs (saitlə bitən köklərdən sonra)
    "sı", "si", "su", "sü",
    # yönlük (saitlə bitən köklərdən sonra)
    "ya", "yə",
    # yönlük / təsirlik / mənsubiyyət (tək saitli — ən riskli qrup)
    "a", "ə", "ı", "i", "u", "ü",
)


def _fold_suffix_list(suffixes: tuple[str, ...]) -> tuple[str, ...]:
    """Şəkilçi siyahısının diakritiksiz variantı.

    LENIENT rejimində mətn əvvəlcə qatlanır (ə->e, ı->i, ...), ona görə orijinal
    siyahıdakı "ə" artıq mətndə "e" kimi görünür və tutulmur. Nəticədə LENIENT
    MORPH-dan DAHA AZ güzəştli olardı — rejimlərin iç-içə keçmə xassəsi pozulardı.
    Bu funksiya siyahını da eyni qaydada qatlayır; təkrarlar atılır, uzunluğa görə
    sıra (uzundan qısaya) dəyişmir, çünki qatlama simvol sayını saxlayır.
    """
    seen: dict[str, None] = {}
    for suffix in suffixes:
        seen.setdefault(suffix.translate(_DIACRITIC_MAP), None)
    return tuple(seen)


_FOLDED_SUFFIXES: tuple[str, ...] = _fold_suffix_list(_SUFFIXES)

#: Kiril -> Azərbaycan latını. Rus və QAZAX hərflərini əhatə edir.
#:
#: Niyə lazımdır: qazax dilinə köklənmiş model azərbaycan sualına kiril əlifbası
#: ilə cavab verir ("Париж", "Анкара", "Мәскеу"). Cavab MƏZMUNCA doğrudur, amma
#: yazı sistemi yanlışdır. Transliterasiya olmadan bal modelin biliyini yox,
#: orfoqrafiyasını ölçür.
#:
#: Hədəf əlifba Azərbaycan latınıdır (ж->j, ш->ş, ч->ç, х->x, ы->ı), çünki
#: müqayisə məhz azərbaycanca etalonla aparılır.
_CYRILLIC_MAP = {
    # rus
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "ts", "ч": "ç", "ш": "ş", "щ": "şç",
    "ъ": "", "ы": "ı", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    # qazax
    "ә": "ə", "ғ": "ğ", "қ": "q", "ң": "ng", "ө": "ö", "ұ": "u", "ү": "ü",
    "һ": "h", "і": "i",
}

_MAX_SUFFIX_STRIPS = 3
_MIN_STEM_LENGTH = 3


@dataclass(frozen=True)
class NormalizationConfig:
    """Bir normalizasiya rejiminin tam tərifi.

    Hesabatda rejimi söz ilə yox, bu obyektin `name` sahəsi ilə göstər ki,
    hansı rəqəmin hansı qaydada alındığı sonradan mübahisə mövzusu olmasın.
    """

    name: str = "strict"
    lowercase: bool = True
    strip_punctuation: bool = True
    collapse_whitespace: bool = True
    strip_suffixes: bool = False
    fold_diacritics: bool = False
    transliterate: bool = False


STRICT = NormalizationConfig(name="strict")
MORPH = replace(STRICT, name="morph", strip_suffixes=True)
LENIENT = replace(MORPH, name="lenient", fold_diacritics=True)
TRANSLIT = replace(LENIENT, name="translit", transliterate=True)

#: Hesabatda dördü də verilir — bax modul docstring-inə.
MODES: tuple[NormalizationConfig, ...] = (STRICT, MORPH, LENIENT, TRANSLIT)


def az_lower(text: str) -> str:
    """Azərbaycan qaydası ilə kiçik hərfə çevirir (I -> ı, İ -> i)."""
    return text.translate(_CASE_FIX).lower()


def fold_diacritics(text: str) -> str:
    """ə->e, ğ->g, ı->i, ö->o, ş->s, ü->u, ç->c."""
    return text.translate(_DIACRITIC_MAP)


def transliterate_cyrillic(text: str) -> str:
    """Kiril mətnini Azərbaycan latınına çevirir.

    Kiril olmayan simvollara toxunulmur, ona görə latın mətn üzərində
    tətbiq etmək zərərsizdir.
    """
    return "".join(_CYRILLIC_MAP.get(ch, ch) for ch in text)


def _has_vowel(stem: str) -> bool:
    return any(ch in _VOWELS for ch in stem)


def strip_suffixes(
    token: str,
    suffixes: tuple[str, ...] = _SUFFIXES,
    max_strips: int = _MAX_SUFFIX_STRIPS,
) -> str:
    """Hal/mənsubiyyət/cəm şəkilçilərini evristik olaraq kəsir.

    Bu morfoloji analizator DEYİL. Sadə son-uyğunluq qaydasıdır.

    Yeganə mühafizə qaydası: kök üç hərfdən qısalırsa və ya kökdə sait qalmırsa,
    kəsmə ləğv olunur. Hədd BÜTÜN şəkilçilər üçün eynidir — bu, təsadüfi seçim
    deyil. Hədd şəkilçinin uzunluğundan asılı olsaydı, eyni sözün iki forması
    fərqli nöqtədə dayanardı ("bakının" -> "bak", amma "bakı" -> "bakı") və
    normalizasiya doğru cavabı səhv sayardı. Vahid hədd bu asimmetriyanı aradan
    qaldırır: "bakı" da "bak"-a enir, müqayisə isə hər iki tərəfə eyni tətbiq
    olunduğu üçün nəticə düzgün qalır.

    Nəticədə kəsmə həqiqi kökdən artıq kəsə bilir ("Gəncə" -> "gənc"). Bu, əsasən
    FƏRQLİ cavabların eyni sayılması riskidir, doğru cavabın itməsi riski deyil.
    Ona görə MORPH rejimi əsas rəqəm kimi yox, STRICT ilə yanaşı verilir.

    Bilinən məhdudiyyət: iki hərfli köklər qorunmur — "evindən" -> "evin"
    ("ev"-ə düşmür), çünki üç hərf həddi mane olur.
    """
    for _ in range(max_strips):
        for suffix in suffixes:
            if not token.endswith(suffix):
                continue
            stem = token[: -len(suffix)]
            if len(stem) < _MIN_STEM_LENGTH or not _has_vowel(stem):
                continue
            token = stem
            break
        else:
            break
    return token


def _strip_punctuation(text: str) -> str:
    """Durğu işarələrini VƏ simvolları ayırıcıya çevirir.

    Simvollar (`S*` kateqoriyası) da daxildir, çünki əks halda dərəcə işarəsi
    ətrafındakı boşluq fərqi cavabı səhv edir: qızıl `100 °C`, model `100°C` —
    eyni cavabdır, amma `°` `So` kateqoriyasındadır və `P` yoxlamasından keçir,
    nəticədə tokenlər `['100','°c']` ilə `['100°c']` kimi ayrılır.

    `%`, `-`, `#` onsuz da `P*` kateqoriyasındadır; bura `°`, `+`, `=`, `$`
    kimi `S*` işarələrini əlavə edir.
    """
    return "".join(
        " " if unicodedata.category(ch)[0] in "PS" else ch for ch in text
    )


def normalize(text: str, config: NormalizationConfig = STRICT) -> str:
    """Mətni verilmiş rejimə uyğun normallaşdırır."""
    # NFKC (NFC yox): alt/üst indeksləri adi rəqəmə çevirir — `N₂` -> `N2`,
    # `H₂O` -> `H2O`. Modellər kimyəvi formulları hər iki cür yazır, fərq
    # məzmunda deyil. Azərbaycan hərflərinə (ə, ğ, ı, İ, ö, ş, ü) təsiri
    # yoxdur; `İ` NFKC-də də U+0130 olaraq qalır.
    text = unicodedata.normalize("NFKC", text)
    if config.lowercase:
        text = az_lower(text)
    if config.strip_punctuation:
        text = _strip_punctuation(text)
    if config.transliterate:
        # Qatlamadan ƏVVƏL: transliterasiya nəticəsi (ş, ç, ə) sonra eyni
        # qaydayla qatlanmalıdır, yoxsa iki tərəf fərqli formada qalır.
        text = transliterate_cyrillic(text)
    if config.fold_diacritics:
        text = fold_diacritics(text)
    if config.strip_suffixes:
        # Mətn qatlanıbsa, şəkilçi siyahısı da qatlanmış olmalıdır — yoxsa
        # LENIENT rejimi MORPH-un üstü olmaz. Bax `_fold_suffix_list`.
        suffixes = _FOLDED_SUFFIXES if config.fold_diacritics else _SUFFIXES
        text = " ".join(strip_suffixes(tok, suffixes) for tok in text.split())
    if config.collapse_whitespace:
        text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str, config: NormalizationConfig = STRICT) -> list[str]:
    """Normallaşdırıb boşluqla bölür."""
    normalized = normalize(text, config)
    return normalized.split() if normalized else []


# --------------------------------------------------------------------------
# Nümunə səviyyəsində metriklər
# --------------------------------------------------------------------------


def exact_match(pred: str, gold: str, config: NormalizationConfig = STRICT) -> float:
    """1.0 əgər normallaşdırılmış sətirlər eynidirsə, əks halda 0.0."""
    return float(normalize(pred, config) == normalize(gold, config))


def token_f1(pred: str, gold: str, config: NormalizationConfig = STRICT) -> float:
    """SQuAD üslubunda token səviyyəsində F1 (təkrarlanan tokenlər çoxluq kimi)."""
    pred_tokens = tokenize(pred, config)
    gold_tokens = tokenize(gold, config)

    if not pred_tokens or not gold_tokens:
        # İkisi də boşdursa razılaşma sayılır; biri boşdursa yox.
        return float(pred_tokens == gold_tokens)

    overlap = sum((Counter(pred_tokens) & Counter(gold_tokens)).values())
    if overlap == 0:
        return 0.0

    precision = overlap / len(pred_tokens)
    recall = overlap / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def score_example(
    pred: str,
    golds: str | Sequence[str],
    config: NormalizationConfig = STRICT,
) -> dict[str, float]:
    """Bir nümunə üçün EM və F1 — bir neçə qəbul edilən cavab varsa, ən yaxşısı.

    `golds` siyahı ola bilər: datasetdəki `answer` + `answer_aliases`.
    Aqlütinativ dildə alias siyahısı morfoloji evristikadan daha etibarlıdır,
    ona görə dataset qurularkən alias yazmaq üstünlük təşkil edir.
    """
    if isinstance(golds, str):
        golds = [golds]
    if not golds:
        raise ValueError("ən azı bir etalon cavab lazımdır")

    return {
        "em": max(exact_match(pred, gold, config) for gold in golds),
        "f1": max(token_f1(pred, gold, config) for gold in golds),
    }


# --------------------------------------------------------------------------
# Bootstrap etibarlılıq intervalları
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BootstrapResult:
    """Orta qiymət + persentil bootstrap intervalı."""

    mean: float
    low: float
    high: float
    n: int
    n_resamples: int

    @property
    def half_width(self) -> float:
        """`62.4 ± 3.1` formatındakı `3.1` — intervalın yarı eni."""
        return (self.high - self.low) / 2

    def as_percent(self) -> "BootstrapResult":
        return BootstrapResult(
            mean=self.mean * 100,
            low=self.low * 100,
            high=self.high * 100,
            n=self.n,
            n_resamples=self.n_resamples,
        )


def bootstrap_ci(
    scores: Sequence[float],
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapResult:
    """Nümunə səviyyəli balların ortası üçün persentil bootstrap CI.

    `seed` sabit saxlanılır ki, hesabatdakı rəqəm təkrar işlədəndə eyni çıxsın —
    məqalədə verilən intervalın reproduksiya oluna bilməsi tələbdir.
    """
    if not 0 < confidence < 1:
        raise ValueError("confidence 0 ilə 1 arasında olmalıdır")
    if n_resamples < 1:
        raise ValueError("n_resamples müsbət olmalıdır")

    values = np.asarray(scores, dtype=float)
    if values.size == 0:
        raise ValueError("boş bal siyahısı üçün CI hesablanmır")

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(n_resamples, values.size))
    means = values[idx].mean(axis=1)

    alpha = (1 - confidence) / 2
    low, high = np.quantile(means, [alpha, 1 - alpha])

    return BootstrapResult(
        mean=float(values.mean()),
        low=float(low),
        high=float(high),
        n=int(values.size),
        n_resamples=n_resamples,
    )


# --------------------------------------------------------------------------
# Cütləşdirilmiş müqayisə (AZ vs EN, model A vs model B)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PairedResult:
    """İki sistemin eyni nümunələr üzərində müqayisəsi."""

    mean_a: float
    mean_b: float
    diff: float  # mean_a - mean_b
    diff_low: float
    diff_high: float
    p_value: float
    n: int
    n_resamples: int

    @property
    def significant(self) -> bool:
        """CI sıfırı əhatə etmirsə True (95% səviyyəsində)."""
        return not (self.diff_low <= 0 <= self.diff_high)


def _paired_arrays(
    scores_a: Sequence[float], scores_b: Sequence[float]
) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    if a.shape != b.shape:
        raise ValueError(
            f"cütləşdirilmiş müqayisə eyni sayda nümunə tələb edir: {a.size} != {b.size}"
        )
    if a.size == 0:
        raise ValueError("boş bal siyahısı müqayisə edilmir")
    return a, b


def paired_bootstrap_diff(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapResult:
    """Fərqin (a - b) bootstrap CI-si; nümunələr cüt halında yenidən seçilir."""
    a, b = _paired_arrays(scores_a, scores_b)
    return bootstrap_ci(a - b, n_resamples=n_resamples, confidence=confidence, seed=seed)


def paired_permutation_test(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    n_resamples: int = 10_000,
    seed: int = 0,
) -> float:
    """İşarə dəyişdirmə (sign-flip) permutasiya testi — ikitərəfli p qiyməti.

    H0: eyni nümunə üzərində iki sistemin fərqi simmetrikdir (d və -d eyni
    ehtimallıdır). Bu, cütləşdirilmiş t-testdən fərqli olaraq normallıq
    fərziyyəsi tələb etmir — 0/1 dəyərli EM balları üçün doğru seçim budur.

    p qiyməti (hit + 1) / (n + 1) düsturu ilə hesablanır, yəni heç vaxt tam
    sıfır olmur; bu, sonlu permutasiya sayının verə biləcəyi ən kiçik qiymətdir.
    """
    a, b = _paired_arrays(scores_a, scores_b)
    diffs = a - b
    observed = abs(diffs.mean())

    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_resamples, diffs.size))
    permuted = np.abs((signs * diffs).mean(axis=1))

    hits = int((permuted >= observed - 1e-12).sum())
    return (hits + 1) / (n_resamples + 1)


def compare_paired(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    n_resamples: int = 1000,
    n_permutations: int = 10_000,
    confidence: float = 0.95,
    seed: int = 0,
) -> PairedResult:
    """Cütləşdirilmiş müqayisənin tam nəticəsi: fərq + CI + p qiyməti."""
    a, b = _paired_arrays(scores_a, scores_b)
    ci = paired_bootstrap_diff(
        a, b, n_resamples=n_resamples, confidence=confidence, seed=seed
    )
    p_value = paired_permutation_test(a, b, n_resamples=n_permutations, seed=seed)

    return PairedResult(
        mean_a=float(a.mean()),
        mean_b=float(b.mean()),
        diff=ci.mean,
        diff_low=ci.low,
        diff_high=ci.high,
        p_value=p_value,
        n=int(a.size),
        n_resamples=n_resamples,
    )


# --------------------------------------------------------------------------
# Formatlaşdırma
# --------------------------------------------------------------------------


def holm_correction(p_values: Sequence[float]) -> list[float]:
    """Holm–Bonferroni düzəlişi çoxsaylı müqayisələr üçün.

    Niyə lazımdır: bir cədvəldə onlarla cütləşdirilmiş test aparırıq. Təsadüfən
    kiçik p qiyməti almaq ehtimalı test sayı ilə birlikdə artır, ona görə xam
    `p < 0.05` həddi çoxsaylı müqayisələrdə mənasını itirir. Bu, hakimin hazır
    zərbəsidir və rəqəmləri əvvəlcədən düzəltmək həm dürüstdür, həm də güclüdür.

    Holm düzəlişi Bonferroni-dən üstündür: eyni səhv nəzarətini verir, amma
    daha az konservativdir, yəni real effektləri az itirir.

    Alqoritm: p qiymətləri artan sıraya düzülür, i-ci qiymət (n - i) əmsalına
    vurulur, sonra ardıcıllığın monoton olması üçün kumulyativ maksimum alınır
    və nəticə 1-ə qırxılır. Qaytarılan siyahının sırası GİRİŞ sırası ilə eynidir.
    """
    n = len(p_values)
    if n == 0:
        return []

    order = sorted(range(n), key=lambda i: p_values[i])
    adjusted = [0.0] * n
    running_max = 0.0
    for rank, index in enumerate(order):
        value = min(1.0, (n - rank) * p_values[index])
        running_max = max(running_max, value)
        adjusted[index] = running_max
    return adjusted


def format_ci(result: BootstrapResult, as_percent: bool = True, digits: int = 1) -> str:
    """`62.4% ± 3.1` formatı — brief 6-cı bölmənin tələbi.

    Interval asimmetrikdirsə (persentil bootstrap-da adi haldır), tam interval
    mötərizədə əlavə olunur ki, ± işarəsi məlumat gizlətməsin.
    """
    r = result.as_percent() if as_percent else result
    suffix = "%" if as_percent else ""

    lower_gap = r.mean - r.low
    upper_gap = r.high - r.mean
    symmetric = abs(lower_gap - upper_gap) < 0.5 * 10**-digits

    if symmetric:
        return f"{r.mean:.{digits}f}{suffix} ± {r.half_width:.{digits}f}"
    return (
        f"{r.mean:.{digits}f}{suffix} ± {r.half_width:.{digits}f} "
        f"[{r.low:.{digits}f}, {r.high:.{digits}f}]"
    )
