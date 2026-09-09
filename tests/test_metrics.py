"""metrics.py üçün testlər."""

from __future__ import annotations

import pytest

from src.metrics import (
    LENIENT,
    MODES,
    TRANSLIT,
    MORPH,
    STRICT,
    az_lower,
    bootstrap_ci,
    compare_paired,
    exact_match,
    fold_diacritics,
    format_ci,
    holm_correction,
    normalize,
    paired_permutation_test,
    score_example,
    strip_suffixes,
    token_f1,
    tokenize,
    transliterate_cyrillic,
)


# --------------------------------------------------------------------------
# Normalizasiya
# --------------------------------------------------------------------------


def test_az_lower_handles_dotted_and_dotless_i():
    # Python-un .lower() metodu burada səhv edir: 'I' -> 'i' və
    # 'İ' -> 'i' + U+0307. Azərbaycan qaydası əksinədir.
    assert az_lower("IĞDIR") == "ığdır"
    assert az_lower("İSMAYILLI") == "ismayıllı"
    assert "̇" not in az_lower("İ")


def test_fold_diacritics_covers_all_az_specific_letters():
    assert fold_diacritics("əğıöşüç") == "egiosuc"
    assert fold_diacritics("Şəki") == "Seki"


def test_normalize_strips_punctuation_and_collapses_whitespace():
    assert normalize("  Bakı,   Azərbaycan!  ") == "bakı azərbaycan"


def test_normalize_strict_keeps_diacritics_and_suffixes():
    assert normalize("Bakıda", STRICT) == "bakıda"


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("şəhərlərdə", "şəhər"),    # cəm + yerlik (iki addım)
        ("qarabağın", "qarabağ"),   # yiyəlik hal
        ("naxçıvan", "naxçıvan"),   # `n` ilə bitən kök toxunulmaz qalır
        ("bakıda", "bak"),          # kök həddindən artıq kəsilir — bax aşağı
    ],
)
def test_strip_suffixes_removes_case_endings(token, expected):
    assert strip_suffixes(token) == expected


@pytest.mark.parametrize("token", ["elm", "ay", "su", "ev"])
def test_strip_suffixes_protects_stems_under_three_letters(token):
    # Kəsmədən sonra üç hərfdən az qalırsa, kəsmə ləğv olunur.
    assert strip_suffixes(token) == token


def test_strip_suffixes_is_idempotent():
    # Sabit nöqtəyə çatmalıdır, yoxsa normalizasiya tətbiq sayından asılı olur.
    for token in ["şəhərlərdə", "bakıda", "gəncədən", "naxçıvandan"]:
        once = strip_suffixes(token)
        assert strip_suffixes(once) == once


# --- morfoloji batareya: hesabatda veriləcək örtük rəqəmi -----------------

#: Model cavabı (hallanmış) və etalon (adlıq hal) — MORPH bunları eyni saymalıdır.
INFLECTION_PAIRS = [
    ("Bakıda", "Bakı"), ("Bakıdan", "Bakı"), ("Bakıya", "Bakı"),
    ("Bakının", "Bakı"), ("Bakını", "Bakı"),
    ("Naxçıvanda", "Naxçıvan"), ("Naxçıvandan", "Naxçıvan"),
    ("Naxçıvana", "Naxçıvan"), ("Naxçıvanın", "Naxçıvan"),
    ("Gəncədə", "Gəncə"), ("Gəncədən", "Gəncə"), ("Gəncəyə", "Gəncə"),
    ("şəhərlərdə", "şəhər"), ("şəhərlər", "şəhər"), ("şəhərin", "şəhər"),
    ("şəhərdən", "şəhər"),
    ("Xəzər dənizində", "Xəzər dənizi"), ("Nizami Gəncəvinin", "Nizami Gəncəvi"),
    ("qadının", "qadın"), ("kitablarda", "kitab"), ("universitetdə", "universitet"),
    ("Türkiyəyə", "Türkiyə"), ("Astanada", "Astana"), ("Qarabağın", "Qarabağ"),
    ("qapısı", "qapı"), ("paytaxtı", "paytaxt"), ("Sumqayıtdan", "Sumqayıt"),
    ("Şəkidə", "Şəki"),
]


@pytest.mark.parametrize(("inflected", "base"), INFLECTION_PAIRS)
def test_morphology_battery(inflected, base):
    assert exact_match(inflected, base, MORPH) == 1.0
    assert exact_match(inflected, base, LENIENT) == 1.0


@pytest.mark.parametrize(
    ("inflected", "base"),
    [
        # Saitlə bitən kökün yiyəlik halı: "gəncənin" -> "in" kəsilir -> "gəncən",
        # sonra çılpaq `n` kəsilmir. `nin` variantını siyahıya qaytarmaq bunu
        # düzəldər, amma əvəzində `n` ilə bitən BÜTÜN kökləri sındırar
        # ("Naxçıvanın" -> "naxçıv"). Ticarət `n`-final köklərin xeyrinə edilib,
        # çünki onlar AZ-də daha çoxdur (Azərbaycan, Qazaxıstan, insan, qadın).
        ("Gəncənin", "Gəncə"),
        # `s`/`y` ilə bitən köklər: aralıq forma ("avtobus"+"u" -> "avtobus")
        # şəkilçi olmadığı üçün açılma yolu yoxdur.
        ("avtobusu", "avtobus"),
        ("saraya", "saray"),
        # İki hərfli köklər üç hərf həddinə ilişir.
        ("evindən", "ev"),
    ],
)
def test_known_stripping_limitations(inflected, base):
    """Evristikanın sənədləşdirilmiş uğursuzluqları — hesabatda göstərilməlidir.

    Bu test uğursuzluqları TƏSDİQ edir, gizlətmir. Evristika yaxşılaşdırılıb
    bu hallar düzələrsə, test qırmızı olacaq — bu, xəbərdarlıqdır ki, batareya
    örtüyü rəqəmi (məqalədə veriləcək) yenilənməlidir.
    """
    assert exact_match(inflected, base, MORPH) == 0.0


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("Bakı", "Gəncə"), ("Bakı", "Sumqayıt"), ("Şəki", "Şəkər"),
        ("dəniz", "dənizçi"), ("Nizami", "Nəsimi"), ("1918", "1920"),
        ("Kür", "Araz"), ("su", "duz"), ("Naxçıvan", "Naftalan"),
    ],
)
def test_distinct_answers_do_not_collide_even_in_lenient_mode(a, b):
    # Ən güzəştli rejimdə belə fərqli cavablar birləşməməlidir — birləşsəydi,
    # metrika modelə olmayan bal verərdi.
    assert exact_match(a, b, LENIENT) == 0.0


def test_tokenize_returns_empty_list_for_blank_input():
    assert tokenize("   ") == []
    assert tokenize("...") == []


# --------------------------------------------------------------------------
# Rejimlərin iç-içə keçməsi — RQ3-ün diaqnostikası buna söykənir
# --------------------------------------------------------------------------


def test_morph_mode_recovers_inflected_answer():
    # Model "Bakıda" cavab verib, etalon "Bakı" — faktual olaraq doğrudur.
    assert exact_match("Bakıda", "Bakı", STRICT) == 0.0
    assert exact_match("Bakıda", "Bakı", MORPH) == 1.0


def test_lenient_mode_recovers_diacritic_loss():
    # Model diakritiksiz yazıb — faktual olaraq doğrudur.
    assert exact_match("Gence", "Gəncə", MORPH) == 0.0
    assert exact_match("Gence", "Gəncə", LENIENT) == 1.0


@pytest.mark.parametrize(
    ("pred", "gold"),
    [
        ("Gəncəyə", "Gəncə"),
        ("şəhərlərdə", "şəhər"),
        ("Qarabağın", "Qarabağ"),
        ("Bakıda", "Bakı"),
    ],
)
def test_lenient_never_scores_below_morph(pred, gold):
    # LENIENT = MORPH + diakritik qatlama, yəni ciddi şəkildə daha güzəştli
    # olmalıdır. Qatlama şəkilçi siyahısına tətbiq olunmasa bu pozulur.
    assert exact_match(pred, gold, LENIENT) >= exact_match(pred, gold, MORPH)
    assert token_f1(pred, gold, LENIENT) >= token_f1(pred, gold, MORPH)


@pytest.mark.parametrize(
    ("pred", "gold"),
    [("Bakıda", "Bakı"), ("Naxçıvana", "Naxçıvan"), ("Gence", "Gəncə")],
)
def test_morph_never_scores_below_strict(pred, gold):
    assert exact_match(pred, gold, MORPH) >= exact_match(pred, gold, STRICT)


# --------------------------------------------------------------------------
# EM və F1
# --------------------------------------------------------------------------


def test_exact_match_ignores_case_and_punctuation():
    assert exact_match("bakı.", "Bakı") == 1.0


def test_exact_match_distinguishes_different_answers():
    assert exact_match("Bakı", "Gəncə") == 0.0


def test_token_f1_partial_overlap():
    # 3 tokendən 2-si üst-üstə düşür: P = 2/3, R = 2/3, F1 = 2/3.
    score = token_f1("Nizami Gəncəvi şair", "Nizami Gəncəvi yazıçı")
    assert score == pytest.approx(2 / 3)


def test_token_f1_no_overlap_is_zero():
    assert token_f1("Bakı", "Gəncə") == 0.0


def test_token_f1_counts_repeated_tokens_as_multiset():
    # "bir" iki dəfə keçir, amma etalonda bir dəfə — ikinci uyğunluq sayılmamalıdır.
    score = token_f1("bir bir", "bir")
    assert score == pytest.approx(2 * 0.5 * 1.0 / 1.5)


def test_token_f1_empty_prediction_scores_zero():
    assert token_f1("", "Bakı") == 0.0


def test_token_f1_both_empty_scores_one():
    assert token_f1("", "") == 1.0


def test_score_example_takes_best_alias():
    result = score_example("Bakıda", ["Gəncə", "Bakı"], MORPH)
    assert result == {"em": 1.0, "f1": 1.0}


def test_score_example_rejects_empty_gold_list():
    with pytest.raises(ValueError):
        score_example("Bakı", [])


# --------------------------------------------------------------------------
# Bootstrap CI
# --------------------------------------------------------------------------


def test_bootstrap_ci_mean_matches_sample_mean():
    scores = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    result = bootstrap_ci(scores, n_resamples=1000, seed=0)
    assert result.mean == pytest.approx(0.625)
    assert result.n == 8
    assert result.n_resamples == 1000


def test_bootstrap_ci_brackets_the_mean():
    scores = [1.0] * 60 + [0.0] * 40
    result = bootstrap_ci(scores, n_resamples=1000, seed=0)
    assert result.low <= result.mean <= result.high


def test_bootstrap_ci_is_reproducible_with_same_seed():
    # Məqalədəki interval təkrar işlədiləndə eyni çıxmalıdır.
    scores = [1.0, 0.0] * 25
    a = bootstrap_ci(scores, seed=7)
    b = bootstrap_ci(scores, seed=7)
    assert (a.mean, a.low, a.high) == (b.mean, b.low, b.high)


def test_bootstrap_ci_narrows_as_sample_grows():
    small = bootstrap_ci([1.0, 0.0] * 15, seed=0)
    large = bootstrap_ci([1.0, 0.0] * 300, seed=0)
    assert large.half_width < small.half_width


def test_bootstrap_ci_degenerate_when_all_scores_equal():
    result = bootstrap_ci([1.0] * 20, seed=0)
    assert (result.low, result.mean, result.high) == (1.0, 1.0, 1.0)


def test_bootstrap_ci_wider_interval_for_higher_confidence():
    scores = [1.0, 0.0] * 50
    narrow = bootstrap_ci(scores, confidence=0.80, seed=0)
    wide = bootstrap_ci(scores, confidence=0.99, seed=0)
    assert wide.half_width > narrow.half_width


def test_bootstrap_ci_rejects_empty_input():
    with pytest.raises(ValueError):
        bootstrap_ci([])


def test_bootstrap_ci_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        bootstrap_ci([1.0, 0.0], confidence=1.5)


def test_as_percent_scales_all_bounds():
    result = bootstrap_ci([1.0, 0.0] * 20, seed=0).as_percent()
    assert result.mean == pytest.approx(50.0)
    assert 0 <= result.low <= 100


# --------------------------------------------------------------------------
# Cütləşdirilmiş müqayisə
# --------------------------------------------------------------------------


def test_paired_test_finds_no_difference_for_identical_systems():
    scores = [1.0, 0.0, 1.0, 1.0, 0.0] * 10
    result = compare_paired(scores, scores, n_permutations=2000, seed=0)
    assert result.diff == 0.0
    assert result.p_value == pytest.approx(1.0)
    assert not result.significant


def test_paired_test_detects_large_consistent_gap():
    # EN həmişə doğru, AZ həmişə səhv — maksimal fərq.
    en = [1.0] * 60
    az = [0.0] * 60
    result = compare_paired(en, az, n_permutations=2000, seed=0)
    assert result.diff == pytest.approx(1.0)
    assert result.p_value < 0.01
    assert result.significant


def test_paired_test_ignores_tiny_noisy_gap():
    # 60 nümunədən yalnız birində fərq — statistik mənalı olmamalıdır.
    en = [1.0] * 30 + [0.0] * 30
    az = [1.0] * 29 + [0.0] * 31
    result = compare_paired(en, az, n_permutations=2000, seed=0)
    assert result.p_value > 0.05
    assert not result.significant


def test_permutation_p_value_never_reaches_zero():
    # (hit + 1) / (n + 1) düsturu — sonlu permutasiya sayı sıfır p verə bilməz.
    p = paired_permutation_test([1.0] * 50, [0.0] * 50, n_resamples=100, seed=0)
    assert p > 0
    assert p == pytest.approx(1 / 101)


def test_paired_test_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="eyni sayda"):
        compare_paired([1.0, 0.0], [1.0])


def test_paired_result_reports_both_means():
    result = compare_paired([1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], seed=0)
    assert result.mean_a == pytest.approx(0.5)
    assert result.mean_b == pytest.approx(0.25)
    assert result.diff == pytest.approx(0.25)


# --------------------------------------------------------------------------
# Formatlaşdırma
# --------------------------------------------------------------------------


def test_format_ci_matches_brief_format():
    result = bootstrap_ci([1.0] * 20, seed=0)
    assert format_ci(result) == "100.0% ± 0.0"


def test_format_ci_shows_full_interval_when_asymmetric():
    # Yuxarı hədd 100%-ə dirənir, aşağı hədd sərbəstdir -> interval asimmetrikdir.
    scores = [1.0] * 97 + [0.0] * 3
    text = format_ci(bootstrap_ci(scores, seed=0))
    assert text.startswith("97.0% ± ")
    assert "[" in text  # asimmetrik interval ± işarəsinin arxasında gizlədilmir


# --------------------------------------------------------------------------
# Kirildən latına transliterasiya — RQ2-nin əsas tapıntısı
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cyrillic", "gold"),
    [("Анкара", "Ankara"), ("Токио", "Tokio"), ("Берлин", "Berlin"), ("Пекин", "Pekin")],
)
def test_transliteration_recovers_correct_cyrillic_answers(cyrillic, gold):
    """Qazax dilinə köklənmiş model doğru cavabı kirillə yazır.

    Transliterasiya olmadan bal modelin biliyini yox, orfoqrafiyasını ölçür.
    """
    assert exact_match(cyrillic, gold, LENIENT) == 0.0
    assert exact_match(cyrillic, gold, TRANSLIT) == 1.0


def test_kazakh_specific_letters_are_transliterated():
    # "Мәскеу" rus "Москва" deyil, QAZAX formasıdır — qazax təliminin izi.
    assert transliterate_cyrillic("мәскеу") == "məskeu"
    assert transliterate_cyrillic("қазақ") == "qazaq"


def test_transliteration_leaves_latin_text_alone():
    assert transliterate_cyrillic("Bakı şəhəri") == "Bakı şəhəri"


def test_translit_is_the_most_lenient_mode():
    # Rejim zənciri iç-içə keçməlidir: hər növbəti əvvəlkindən güzəştlidir.
    for pred, gold in [("Анкара", "Ankara"), ("Bakıda", "Bakı"), ("Gence", "Gəncə")]:
        assert exact_match(pred, gold, TRANSLIT) >= exact_match(pred, gold, LENIENT)


def test_transliteration_does_not_credit_wrong_answers():
    for wrong in ["Москва", "Астана", "Лондон"]:
        assert exact_match(wrong, "Bakı", TRANSLIT) == 0.0


# --------------------------------------------------------------------------
# Çoxsaylı müqayisə düzəlişi
# --------------------------------------------------------------------------


def test_holm_leaves_a_single_test_unchanged():
    assert holm_correction([0.03]) == [0.03]


def test_holm_preserves_input_order():
    """Sıralama daxildə aparılır, nəticə GİRİŞ sırası ilə qaytarılmalıdır.

    n=3 üçün əmsallar sıralanmış p-lərə görədir: ən kiçik x3, ortadakı x2,
    ən böyük x1. Yəni [0.5, 0.001, 0.2] -> [0.5, 0.003, 0.4].
    """
    assert holm_correction([0.5, 0.001, 0.2]) == pytest.approx([0.5, 0.003, 0.4])


def test_holm_is_monotonic():
    adjusted = sorted(holm_correction([0.001, 0.01, 0.02, 0.04, 0.5]))
    assert adjusted == sorted(adjusted)


def test_holm_caps_values_at_one():
    assert all(p <= 1.0 for p in holm_correction([0.6, 0.7, 0.8, 0.9]))


def test_holm_is_less_conservative_than_bonferroni():
    raw = [0.001, 0.01, 0.03, 0.04]
    holm = holm_correction(raw)
    bonferroni = [min(1.0, len(raw) * p) for p in raw]
    assert all(h <= b for h, b in zip(holm, bonferroni))
    assert holm[-1] < bonferroni[-1]   # ən böyüklərdə fərq görünür


def test_holm_can_reverse_a_marginal_result():
    # Xam p = 0.046 bir cədvəldə 12 testlə birlikdə sağ qalmır.
    raw = [0.0002, 0.046] + [0.5] * 10
    assert raw[1] < 0.05
    assert holm_correction(raw)[1] > 0.05


def test_holm_on_empty_input():
    assert holm_correction([]) == []


# --------------------------------------------------------------------------
# Vahid simvolları: dərəcə işarəsi və alt indekslər
# --------------------------------------------------------------------------


def test_degree_symbol_spacing_does_not_break_match():
    """`100 °C` ilə `100°C` eyni cavabdır.

    `°` Unicode-da `So` kateqoriyasındadır, `P` deyil. Yalnız `P`
    təmizlənsəydi, tokenlər `['100','°c']` ilə `['100°c']` kimi
    ayrılar və doğru cavab səhv sayılardı.
    """
    for mode in MODES:
        assert exact_match("100 °C", "100°C", mode) == 1.0
        assert exact_match("0 °C", "0°C", mode) == 1.0


def test_subscripts_fold_to_ascii_digits():
    """NFKC `N₂` -> `N2`. Modellər formulları hər iki cür yazır."""
    for mode in MODES:
        assert exact_match("N2", "N₂", mode) == 1.0
        assert exact_match("H2O", "H₂O", mode) == 1.0


def test_symbol_folding_does_not_merge_distinct_answers():
    """Simvol qatlanması FƏRQLİ cavabları eyniləşdirməməlidir."""
    assert exact_match("100 °C", "0 °C", LENIENT) == 0.0
    assert exact_match("N2", "O2", LENIENT) == 0.0


def test_azerbaijani_letters_survive_nfkc():
    """NFKC azərbaycan hərflərinə toxunmamalıdır.

    Xüsusən `İ` (nöqtəli böyük I) parçalanıb `I` + birləşən nöqtəyə
    çevrilsəydi, nöqtəsiz `I` ilə qarışardı — bu isə datasetdə artıq bir dəfə
    səhvə səbəb olub.
    """
    for char in "əğıİöşüÇŞƏĞÖÜI":
        assert normalize(char, STRICT) == az_lower(char)
