"""morphology.py üçün testlər — hallanmış formaların generasiyası."""

from __future__ import annotations

import pytest

from src.metrics import MORPH, STRICT, exact_match
from src.morphology import (
    aliases_for,
    az_capitalize,
    genitive,
    harmony2,
    harmony4,
    inflect,
    last_vowel,
    locative,
    soften_final,
    year_aliases,
)


# --------------------------------------------------------------------------
# Sait ahəngi
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("word", "expected"),
    [("Bakı", "ı"), ("Gəncə", "ə"), ("ordu", "u"), ("göl", "ö"), ("şəhər", "ə")],
)
def test_last_vowel(word, expected):
    assert last_vowel(word) == expected


@pytest.mark.parametrize(
    ("word", "expected"),
    [("Bakı", "a"), ("Naxçıvan", "a"), ("Gəncə", "ə"), ("şəhər", "ə"), ("ordu", "a")],
)
def test_harmony2_picks_a_or_e(word, expected):
    assert harmony2(word) == expected


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("Bakı", "ı"),      # a, ı -> ı
        ("Naxçıvan", "ı"),
        ("Gəncə", "i"),     # e, ə, i -> i
        ("şəhər", "i"),
        ("ordu", "u"),      # o, u -> u
        ("göl", "ü"),       # ö, ü -> ü
        ("üzüm", "ü"),
    ],
)
def test_harmony4_picks_correct_vowel(word, expected):
    assert harmony4(word) == expected


def test_harmony_falls_back_for_vowelless_input():
    # Abbreviaturalar (BMT, MDB) saitsiz yazıla bilər — çökməməlidir.
    assert harmony2("BMT") in {"a", "ə"}
    assert harmony4("BMT") in {"ı", "i", "u", "ü"}


# --------------------------------------------------------------------------
# Samit yumşalması
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("word", "expected"),
    [("otaq", "otağ"), ("çörək", "çörəy"), ("papaq", "papağ")],
)
def test_soften_final_applies_to_polysyllabic_words(word, expected):
    assert soften_final(word) == expected


@pytest.mark.parametrize("word", ["ox", "top", "ay", "qız"])
def test_soften_final_leaves_other_endings_alone(word):
    assert soften_final(word) == word


def test_soften_final_skips_monosyllables():
    # Təkhecalı sözlərdə yumşalma baş vermir.
    assert soften_final("ok") == "ok"


# --------------------------------------------------------------------------
# Hal paradiqması
# --------------------------------------------------------------------------


def test_vowel_final_stem_takes_buffer_consonants():
    forms = inflect("Bakı")
    assert forms.genitive == ("Bakının",)
    assert forms.dative == ("Bakıya",)
    assert forms.accusative == ("Bakını",)
    assert forms.possessive3 == ("Bakısı",)
    assert forms.locative[0] == "Bakıda"
    assert forms.ablative[0] == "Bakıdan"
    assert forms.plural == ("Bakılar",)


def test_consonant_final_stem_takes_bare_suffixes():
    forms = inflect("Naxçıvan")
    assert forms.genitive[0] == "Naxçıvanın"
    assert forms.dative[0] == "Naxçıvana"
    assert forms.accusative[0] == "Naxçıvanı"
    assert forms.locative == ("Naxçıvanda",)
    assert forms.ablative == ("Naxçıvandan",)


def test_front_vowel_stem_uses_front_suffixes():
    forms = inflect("Gəncə")
    assert forms.genitive == ("Gəncənin",)
    assert forms.dative == ("Gəncəyə",)
    assert forms.accusative == ("Gəncəni",)
    assert forms.locative[0] == "Gəncədə"
    assert forms.ablative[0] == "Gəncədən"


def test_rounded_vowel_stems():
    assert inflect("ordu").genitive == ("ordunun",)
    assert inflect("göl").genitive[0] == "gölün"
    assert inflect("göl").dative[0] == "gölə"


def test_softening_produces_both_variants():
    # "otağa" düzgün formadır, amma xüsusi adlarda orfoqrafiya çox vaxt
    # yumşaltmır — hər ikisi qəbul edilən variant kimi verilir.
    dative = inflect("otaq").dative
    assert "otağa" in dative
    assert "otaqa" in dative


def test_vowel_final_stem_also_offers_buffer_n_locative():
    # "Xəzər dənizi" kimi mənsubiyyət şəkilçili birləşmələr üçün lazımdır.
    assert "dənizində" in inflect("dənizi").locative


def test_all_forms_starts_with_nominative_and_has_no_duplicates():
    forms = inflect("şəhər").all_forms()
    assert forms[0] == "şəhər"
    assert len(forms) == len(set(forms))


# --------------------------------------------------------------------------
# Şablon sualları üçün: yiyəlik hal və böyük hərf
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("phrase", "expected"),
    [
        ("Fransa", "Fransanın"),
        ("Türkiyə", "Türkiyənin"),
        ("Çin", "Çinin"),
        ("Rusiya", "Rusiyanın"),
        ("Hindistan", "Hindistanın"),
        ("Yaponiya", "Yaponiyanın"),
        ("Meksika", "Meksikanın"),
        ("Amerika Birləşmiş Ştatları", "Amerika Birləşmiş Ştatlarının"),
    ],
)
def test_genitive_of_country_names(phrase, expected):
    assert genitive(phrase) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Stadnik", "Stadnikin"),
        ("Malik", "Malikin"),
        ("İraq", "İraqın"),
        ("Mozambik", "Mozambikin"),
    ],
)
def test_genitive_does_not_soften_proper_nouns(name, expected):
    # Samit yumşalması (q->ğ, k->y) ümumi isimlərə aiddir; xüsusi adlar öz
    # formasını saxlayır. Əks halda "Stadnik" -> "Stadniyin" kimi uydurma
    # formalar sualın mətninə düşür.
    assert genitive(name) == expected


@pytest.mark.parametrize(
    ("noun", "expected"),
    [("otaq", "otağın"), ("çörək", "çörəyin"), ("papaq", "papağın")],
)
def test_genitive_softens_common_nouns(noun, expected):
    assert genitive(noun) == expected


def test_genitive_inflects_only_the_last_word():
    assert genitive("Böyük Britaniya").startswith("Böyük ")


def test_genitive_of_blank_is_blank():
    assert genitive("   ") == ""


@pytest.mark.parametrize(
    ("phrase", "expected"),
    [
        ("Fransa", "Fransada"),
        ("Çin", "Çində"),
        ("Türkiyə", "Türkiyədə"),
        ("Almaniya", "Almaniyada"),
        ("Yeni Zelandiya", "Yeni Zelandiyada"),
        # Mənsubiyyət şəkilçili birləşmələr bağlayıcı `n` alır.
        ("Amerika Birləşmiş Ştatları", "Amerika Birləşmiş Ştatlarında"),
        ("Birləşmiş Ərəb Əmirlikləri", "Birləşmiş Ərəb Əmirliklərində"),
        ("Xəzər dənizi", "Xəzər dənizində"),
    ],
)
def test_locative_of_place_names(phrase, expected):
    assert locative(phrase) == expected


def test_locative_of_blank_is_blank():
    assert locative("   ") == ""


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ispan dili", "İspan dili"),   # i -> İ, nöqtəli qalır
        ("isveç dili", "İsveç dili"),
        ("ırmaq", "Irmaq"),             # ı -> I, nöqtəsiz qalır
        ("qızıl", "Qızıl"),
        ("Karbon", "Karbon"),           # onsuz da böyükdür
    ],
)
def test_az_capitalize_respects_dotted_and_dotless_i(text, expected):
    assert az_capitalize(text) == expected


def test_az_capitalize_differs_from_python_capitalize():
    # Python `str.capitalize()` "ispan" -> "Ispan" verir (səhv) və sözün
    # qalanını kiçildərək "ABŞ" kimi yazılışları korlayır.
    assert az_capitalize("ispan") != "ispan".capitalize()
    assert az_capitalize("ABŞ dolları") == "ABŞ dolları"


def test_az_capitalize_handles_empty_string():
    assert az_capitalize("") == ""


# --------------------------------------------------------------------------
# İllər
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("year", "expected"),
    [
        ("1918", "1918-ci il"),    # səkkizinci
        ("1920", "1920-ci il"),    # iyirminci
        ("1991", "1991-ci il"),    # birinci
        ("1993", "1993-cü il"),    # üçüncü
        ("2020", "2020-ci il"),    # iyirminci
        ("1900", "1900-cü il"),    # yüzüncü
        ("2000", "2000-ci il"),    # mininci
        ("1936", "1936-cı il"),    # altıncı
        ("1969", "1969-cu il"),    # doqquzuncu
        ("1940", "1940-cı il"),    # qırxıncı
    ],
)
def test_year_ordinal_suffix(year, expected):
    assert expected in year_aliases(year)


def test_year_aliases_include_bare_number_and_locative():
    forms = year_aliases("1918")
    assert "1918" in forms
    assert "1918-ci ildə" in forms


# --------------------------------------------------------------------------
# aliases_for — datasetə yazılan sahə
# --------------------------------------------------------------------------


def test_aliases_exclude_the_answer_itself():
    assert "Bakı" not in aliases_for("Bakı")


def test_aliases_cover_the_common_cases():
    aliases = aliases_for("Bakı")
    for form in ["Bakıda", "Bakıya", "Bakıdan", "Bakının", "Bakını"]:
        assert form in aliases


def test_multiword_answer_inflects_only_the_last_word():
    aliases = aliases_for("Xəzər dənizi")
    assert "Xəzər dənizində" in aliases
    assert not any(a.startswith("Xəzərdə") for a in aliases)


def test_aliases_for_year_answer():
    aliases = aliases_for("1918")
    assert "1918-ci il" in aliases


def test_aliases_are_capped():
    assert len(aliases_for("Bakı", max_aliases=3)) == 3


def test_aliases_for_blank_answer_is_empty():
    assert aliases_for("   ") == []


# --------------------------------------------------------------------------
# Metriklərlə birlikdə — əsas iddia
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("model_output", "gold"),
    [
        ("Bakıda", "Bakı"), ("Bakıya", "Bakı"), ("Bakının", "Bakı"),
        ("Naxçıvanda", "Naxçıvan"), ("Naxçıvana", "Naxçıvan"),
        ("Gəncədən", "Gəncə"), ("Gəncəyə", "Gəncə"),
        ("Gəncənin", "Gəncə"),          # `strip_suffixes` bunu tuta bilmirdi
        ("Xəzər dənizində", "Xəzər dənizi"),
        ("1918-ci ildə", "1918"),       # şəkilçi kəsmə ilə ümumiyyətlə mümkün deyil
        ("otağa", "otaq"),
    ],
)
def test_generated_aliases_credit_inflected_answers_in_strict_mode(model_output, gold):
    """Əsas iddia: alias generasiyası STRICT rejimdə də hallanmanı tutur.

    Bu, morfoloji evristikadan üstündür — həm `Gəncənin`, həm `1918-ci ildə`
    kimi evristikanın bacarmadığı halları tutur, həm də ən sərt (yəni ən
    müdafiə olunan) normalizasiya rejimində işləyir.
    """
    golds = [gold, *aliases_for(gold)]
    assert max(exact_match(model_output, g, STRICT) for g in golds) == 1.0


def test_aliases_do_not_credit_wrong_answers():
    golds = ["Bakı", *aliases_for("Bakı")]
    for wrong in ["Gəncə", "Sumqayıt", "Naxçıvan", "Şəki"]:
        assert max(exact_match(wrong, g, MORPH) for g in golds) == 0.0


# --------------------------------------------------------------------------
# Xəbərlik şəkilçisi — modellər cümlə ilə cavab verəndə lazım olur
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("base", "expected"),
    [
        ("Paris", "Parisdir"),
        ("Ankara", "Ankaradır"),
        ("Moskva", "Moskvadır"),
        ("Bakı", "Bakıdır"),
        ("Tokio", "Tokiodur"),
        ("Gəncə", "Gəncədir"),
    ],
)
def test_copula_form_follows_vowel_harmony(base, expected):
    assert inflect(base).copula == (expected,)


@pytest.mark.parametrize(
    ("model_output", "gold"),
    [
        ("Parisdir", "Paris"),
        ("Ankaradır", "Ankara"),
        ("Moskvadır", "Moskva"),
    ],
)
def test_copula_answers_are_credited_via_aliases(model_output, gold):
    """Model "Fransanın paytaxtı Parisdir" yazanda cavab bu formadadır.

    Empirik olaraq Qwen3-1.7B səkkiz sualdan beşində məhz belə cavab verdi.
    Alias olmadan bunların hamısı sıfır bal alırdı.
    """
    from src.metrics import STRICT, exact_match

    golds = [gold, *aliases_for(gold)]
    assert max(exact_match(model_output, g, STRICT) for g in golds) == 1.0


def test_az_capitalize_skips_leading_punctuation():
    # «Odlar Yurdu» əsərinin müəllifi kimdir? — böyüdüləcək hərf dırnağın
    # arxasındadır.
    assert az_capitalize("«odlar yurdu» əsəri") == "«Odlar yurdu» əsəri"
    assert az_capitalize('"ispan dili" haqqında') == '"İspan dili" haqqında'


def test_az_capitalize_leaves_text_without_letters_alone():
    assert az_capitalize("1918") == "1918"
