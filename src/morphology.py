"""Azərbaycan morfologiyası — hallanmış formaların GENERASİYASI.

Niyə ayrıca modul: `metrics.strip_suffixes` tərs istiqamətdə işləyir (formadan
kökə) və lüğətsiz həll olunmayan qeyri-müəyyənliklərə ilişir — "Naxçıvanın"
sözündəki `n` kökə, yoxsa şəkilçiyə aiddir? Bunu bilmək üçün kökü tanımaq lazımdır.

Generasiya isə tərsidir: kök ARTIQ məlumdur (datasetdəki `answer` sahəsi), ona
görə sait ahəngi və bağlayıcı samit qaydaları birmənalı tətbiq olunur. Yəni:

    analiz  ("Bakıda" -> "Bakı")   : qeyri-müəyyən, evristik, xəta verir
    sintez  ("Bakı" -> "Bakıda")   : müəyyən, qaydaya tabe, dəqiq

Ona görə əsas strategiya budur: datasetdə `answer_aliases` sahəsini bu modul ilə
avtomatik doldur, qiymətləndirmədə isə `STRICT` rejimə güvən. Morfoloji evristika
yalnız ikinci dərəcəli rəqəm kimi qalır.

QƏSDƏN ARTIQ GENERASİYA: şübhəli hallarda hər iki variant qaytarılır (məs. həm
"otağa", həm "otaqa"). Alias siyahısı yalnız BAL VERİR — modelin cavabı hər hansı
variantla üst-üstə düşsə, sayılır. Az generasiya doğru cavabı itirir, artıq
generasiya isə praktiki olaraq zərərsizdir, çünki bütün variantlar eyni kökün
formalarıdır və başqa bir doğru cavabla toqquşmur.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "BACK_VOWELS",
    "FRONT_VOWELS",
    "last_vowel",
    "harmony2",
    "harmony4",
    "soften_final",
    "az_capitalize",
    "Inflections",
    "inflect",
    "genitive",
    "locative",
    "year_aliases",
    "aliases_for",
]


BACK_VOWELS = "aıou"
FRONT_VOWELS = "eəiöü"
VOWELS = BACK_VOWELS + FRONT_VOWELS

#: Dörd variantlı ahəng: son sait -> şəkilçi saiti.
_HARMONY4 = {
    "a": "ı", "ı": "ı",
    "e": "i", "ə": "i", "i": "i",
    "o": "u", "u": "u",
    "ö": "ü", "ü": "ü",
}

#: Sait ilə başlayan şəkilçidən əvvəl kökün son samitinin yumşalması.
_SOFTENING = {"q": "ğ", "k": "y"}


def last_vowel(word: str) -> str | None:
    """Sözün son saiti (ahəng qaydalarının söykəndiyi hərf)."""
    for ch in reversed(word.lower()):
        if ch in VOWELS:
            return ch
    return None


def harmony2(word: str) -> str:
    """İki variantlı ahəng: `a` və ya `ə` (-da/-də, -dan/-dən, -lar/-lər)."""
    vowel = last_vowel(word)
    if vowel is None:
        return "ə"  # saitsiz söz (abbreviatura) — incə variant daha təbiidir
    return "a" if vowel in BACK_VOWELS else "ə"


def harmony4(word: str) -> str:
    """Dörd variantlı ahəng: `ı`, `i`, `u`, `ü` (-ın/-in/-un/-ün)."""
    vowel = last_vowel(word)
    if vowel is None:
        return "i"
    return _HARMONY4[vowel]


def _is_vowel_final(word: str) -> bool:
    return bool(word) and word[-1].lower() in VOWELS


def _syllable_count(word: str) -> int:
    return sum(1 for ch in word.lower() if ch in VOWELS)


def soften_final(word: str) -> str:
    """Sait ilə başlayan şəkilçidən əvvəl son samiti yumşaldır: q->ğ, k->y.

    Yalnız çoxhecalı sözlərdə: "otaq" -> "otağ(a)", amma təkhecalı "ox" -> "oxa"
    dəyişmir. Təkhecalı sözlərdə yumşalma baş vermir.
    """
    if not word or _syllable_count(word) < 2:
        return word
    replacement = _SOFTENING.get(word[-1].lower())
    if replacement is None:
        return word
    # Böyük hərfli kökdə də düzgün işləsin.
    if word[-1].isupper():
        replacement = replacement.upper()
    return word[:-1] + replacement


@dataclass(frozen=True)
class Inflections:
    """Bir kökün hal paradiqması."""

    nominative: str
    genitive: tuple[str, ...]
    dative: tuple[str, ...]
    accusative: tuple[str, ...]
    locative: tuple[str, ...]
    ablative: tuple[str, ...]
    plural: tuple[str, ...]
    possessive3: tuple[str, ...]
    copula: tuple[str, ...]

    def all_forms(self) -> list[str]:
        """Bütün formalar, təkrarsız, adlıq hal birinci."""
        seen = {self.nominative: None}
        for group in (
            self.copula, self.locative, self.ablative, self.dative,
            self.genitive, self.accusative, self.possessive3, self.plural,
        ):
            for form in group:
                seen.setdefault(form, None)
        return list(seen)


def inflect(base: str) -> Inflections:
    """Bir sözün hal paradiqmasını qurur.

    Bağlayıcı samitlər saitlə bitən köklərdə işə düşür:
    Bakı -> Bakı**n**ın, Bakı**y**a, Bakı**n**ı, Bakı**s**ı
    Naxçıvan -> Naxçıvanın, Naxçıvana, Naxçıvanı
    """
    a = harmony2(base)         # a | ə
    i = harmony4(base)         # ı | i | u | ü
    vowel_final = _is_vowel_final(base)
    softened = soften_final(base)

    if vowel_final:
        genitive = (f"{base}n{i}n",)
        dative = (f"{base}y{a}",)
        accusative = (f"{base}n{i}",)
        possessive3 = (f"{base}s{i}",)
        # Saitlə bitən söz artıq mənsubiyyət şəkilçisi daşıya bilər
        # ("Xəzər dəniz**i**"), o halda hal şəkilçisindən əvvəl `n` gəlir:
        # "dənizi" -> "dənizi**n**də". Hansı olduğunu bilmədiyimiz üçün hər
        # ikisini veririk — artıq generasiya qəsdəndir.
        locative = (f"{base}d{a}", f"{base}nd{a}")
        ablative = (f"{base}d{a}n", f"{base}nd{a}n")
    else:
        # Sait ilə başlayan şəkilçilər yumşaldılmış kökə qoşulur (otaq -> otağa),
        # amma orfoqrafiya xüsusi adlarda çox vaxt yumşaltmır — hər ikisi verilir.
        genitive = tuple(dict.fromkeys([f"{softened}{i}n", f"{base}{i}n"]))
        dative = tuple(dict.fromkeys([f"{softened}{a}", f"{base}{a}"]))
        accusative = tuple(dict.fromkeys([f"{softened}{i}", f"{base}{i}"]))
        possessive3 = accusative  # C-final köklərdə eyni forma
        locative = (f"{base}d{a}",)
        ablative = (f"{base}d{a}n",)

    plural = (f"{base}l{a}r",)

    # Xəbərlik şəkilçisi: "Paris" -> "Parisdir", "Moskva" -> "Moskvadır".
    # Modellər tapşırığa baxmayaraq cümlə ilə cavab verəndə cavab məhz bu
    # formada çıxır ("Türkiyənin paytaxtının adı Ankaradır"), ona görə alias
    # siyahısına daxil edilir.
    copula = (f"{base}d{i}r",)

    return Inflections(
        nominative=base,
        genitive=genitive,
        dative=dative,
        accusative=accusative,
        locative=locative,
        ablative=ablative,
        plural=plural,
        possessive3=possessive3,
        copula=copula,
    )


def genitive(phrase: str) -> str:
    """Söz birləşməsini yiyəlik hala salır: "Fransa" -> "Fransanın".

    Yalnız SON söz hallanır — Azərbaycan dilində birləşmə məhz belə işlənir:
    "Amerika Birləşmiş Ştatları" -> "Amerika Birləşmiş Ştatlarının".

    Şablon suallarını təbiiləşdirmək üçündür: "Fransa ölkəsinin paytaxtı"
    qrammatikdir, amma yöndəmsizdir; "Fransanın paytaxtı" doğma səslənir.
    """
    phrase = phrase.strip()
    if not phrase:
        return phrase
    words = phrase.split()
    forms = inflect(words[-1]).genitive
    # Samit yumşalması (q->ğ, k->y) XÜSUSİ ADLARDA tətbiq olunmur:
    # "Stadnik" -> "Stadnikin", "Malik" -> "Malikin", "İraq" -> "İraqın".
    # `inflect` hər iki variantı verir, birincisi yumşaldılmışdır — böyük
    # hərflə başlayan sözdə sonuncunu (yumşaldılmamışı) seçirik.
    #
    # Bilinən istisna: "Birləşmiş Krallıq" kimi tərkibində ümumi isim olan
    # adlar ("Krallığın" daha təbiidir). Say etibarilə xüsusi adlar üstündür,
    # ona görə qayda onların xeyrinə qurulub; istisnalar əl yoxlamasında
    # düzəldilir.
    words[-1] = forms[-1] if words[-1][:1].isupper() else forms[0]
    return " ".join(words)


def locative(phrase: str) -> str:
    """Söz birləşməsini yerlik hala salır: "Fransa" -> "Fransada".

    Bağlayıcı `n` problemi: saitlə bitən söz mənsubiyyət şəkilçisi daşıyırsa,
    hal şəkilçisindən əvvəl `n` gəlir — "Ştatları" -> "Ştatları**n**da", amma
    "Fransa" -> "Fransada". Hansının doğru olduğunu bilmək üçün sözün
    mənsubiyyət daşıyıb-daşımadığını müəyyən etmək lazımdır.

    Evristika: çoxsözlü birləşmə `ı/i/u/ü` saiti ilə bitirsə, bu, demək olar
    həmişə III şəxs mənsubiyyət şəkilçisidir ("Amerika Birləşmiş Ştatları",
    "Xəzər dənizi", "Birləşmiş Ərəb Əmirlikləri"). Təksözlü adlarda isə belə
    deyil ("Bakı", "Şəki").
    """
    phrase = phrase.strip()
    if not phrase:
        return phrase
    words = phrase.split()
    forms = inflect(words[-1]).locative
    possessive_compound = len(words) > 1 and words[-1][-1].lower() in "ıiuü"
    words[-1] = forms[1] if possessive_compound and len(forms) > 1 else forms[0]
    return " ".join(words)


def az_capitalize(text: str) -> str:
    """Cümlənin ilk hərfini Azərbaycan qaydası ilə böyüdür.

    Python-un `str.capitalize()` metodu burada səhv edir: "ispan" -> "Ispan",
    halbuki Azərbaycan dilində nöqtəli `i` böyüyəndə nöqtəli `İ` olur.
    Həmçinin `capitalize()` sözün qalanını kiçildir və "ABŞ" kimi yazılışları
    korlayır — burada yalnız ilk hərfə toxunulur.

    İlk SİMVOL yox, ilk HƏRF böyüdülür: cümlə durğu işarəsi ilə başlaya bilər
    («Odlar Yurdu» əsərinin müəllifi kimdir?) və o halda böyüdüləcək hərf
    dırnağın arxasındadır.
    """
    if not text:
        return text
    for index, char in enumerate(text):
        if char.isalpha():
            upper = {"i": "İ", "ı": "I"}.get(char, char.upper())
            return text[:index] + upper + text[index + 1 :]
    return text


# --------------------------------------------------------------------------
# Rəqəmlər və illər
# --------------------------------------------------------------------------

#: Rəqəmin oxunuşuna görə sıra sayı şəkilçisinin qısaldılmış yazılışı.
#: "1918" -> "səkkiz**inci**" -> yazıda "1918-**ci**".
_DIGIT_ORDINAL = {
    "0": "cı",   # sıfırıncı
    "1": "ci",   # birinci
    "2": "ci",   # ikinci
    "3": "cü",   # üçüncü
    "4": "cü",   # dördüncü
    "5": "ci",   # beşinci
    "6": "cı",   # altıncı
    "7": "ci",   # yeddinci
    "8": "ci",   # səkkizinci
    "9": "cu",   # doqquzuncu
}

#: Son rəqəm sıfırdırsa, oxunuş onluq/yüzlük mərtəbəyə keçir.
_TENS_ORDINAL = {
    "1": "cu",   # onuncu
    "2": "ci",   # iyirminci
    "3": "cu",   # otuzuncu
    "4": "cı",   # qırxıncı
    "5": "ci",   # əllinci
    "6": "cı",   # altmışıncı
    "7": "ci",   # yetmişinci
    "8": "ci",   # səksəninci
    "9": "cı",   # doxsanıncı
}


def _ordinal_suffix(number: str) -> str:
    """Rəqəmin sıra sayı şəkilçisi: 1918 -> "ci", 1920 -> "ci", 1900 -> "cü"."""
    digits = number.lstrip("0") or "0"

    if digits[-1] != "0":
        return _DIGIT_ORDINAL[digits[-1]]
    if len(digits) >= 2 and digits[-2] != "0":
        return _TENS_ORDINAL[digits[-2]]      # 1920 -> iyirminci -> "ci"
    if len(digits) >= 3 and digits[-3] != "0":
        return "cü"                            # yüzüncü
    return "ci"                                # mininci


def year_aliases(number: str) -> list[str]:
    """İl üçün Azərbaycan dilində qəbul edilən yazılışlar.

    Model "1918" da yaza bilər, "1918-ci il" də, "1918-ci ildə" də — üçü də
    doğrudur. STRICT rejimdə bunların heç biri digəri ilə uyğunlaşmır, ona görə
    alias kimi hamısı verilir.
    """
    suffix = _ordinal_suffix(number)
    stem = f"{number}-{suffix} il"
    return [
        number,
        stem,
        f"{stem}də" if harmony2("il") == "ə" else f"{stem}da",
        f"{stem}in",
    ]


# --------------------------------------------------------------------------
# Əsas giriş nöqtəsi
# --------------------------------------------------------------------------

MAX_ALIASES = 24


def aliases_for(answer: str, max_aliases: int = MAX_ALIASES) -> list[str]:
    """Bir cavab üçün qəbul ediləcək formalar (cavabın özü siyahıya daxil deyil).

    Çoxsözlü cavabda yalnız SON söz hallanır — Azərbaycan dilində söz birləşməsi
    məhz belə hallanır ("Xəzər dənizi" -> "Xəzər dənizində", "Xəzərdə dənizi" yox).
    """
    answer = answer.strip()
    if not answer:
        return []

    if answer.isdigit():
        forms = year_aliases(answer)
    else:
        words = answer.split()
        head, tail = words[:-1], words[-1]
        prefix = " ".join(head) + " " if head else ""
        forms = [prefix + form for form in inflect(tail).all_forms()]

    seen = {answer: None}
    result: list[str] = []
    for form in forms:
        if form in seen:
            continue
        seen[form] = None
        result.append(form)
        if len(result) >= max_aliases:
            break
    return result
