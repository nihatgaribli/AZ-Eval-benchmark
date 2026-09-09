"""Avtomatik xəta təsnifatı üçün testlər.

Təsnifat normalizasiya zəncirindən çıxarılır, ona görə testlər hər həlqənin
ÖZ etiketini verdiyini və zəncirin çatmadığı yerdə maşının SUSDUĞUNU yoxlayır.
Susmaq burada uğursuzluq deyil, tələbdir: mühakimə tələb edən sətri maşının
etiketləməsi ölçünü əyərdi.
"""

from __future__ import annotations

from src.analyze import AUTO_ERROR_TYPES, auto_error_summary, classify_error


def test_empty_prediction_is_labelled_blank():
    assert classify_error("", ["Vaşinqton"], 0.0) == "boş cavab"
    assert classify_error("   ", ["Vaşinqton"], 0.0) == "boş cavab"


def test_suffix_only_difference_is_morphology():
    """MORPH düzəldirsə, səbəb şəkilçidir."""
    assert classify_error("Vaşinqtonun", ["Vaşinqton"], 0.5) == "morfologiya"


def test_diacritic_only_difference_is_diacritics():
    """LENIENT düzəldir, MORPH düzəltmir -> yalnız diakritika."""
    assert classify_error("Vasinqton", ["Vaşinqton"], 0.0) == "diakritika"


def test_cyrillic_that_the_chain_recovers_is_script():
    """TRANSLIT düzəldirsə, xəta yazı sistemindəndir, biliksizlikdən deyil."""
    assert classify_error("Париж", ["Parij"], 0.0) == "yazı sistemi"


def test_cyrillic_that_the_chain_cannot_recover_gets_its_own_bucket():
    """`г` -> `g`, azərbaycanca isə `q`. Zəncir çatmır.

    Belə sətri "faktual səhv" saymaq yanlış olardı: model cavabı bilir, sadəcə
    başqa əlifba ilə yazır. Ayrı səbət olmasaydı, faktual xətaların payı
    süni şəkildə şişərdi.
    """
    assert (
        classify_error("Вашингтон", ["Vaşinqton"], 0.0)
        == "kiril, zəncir bərpa etmir"
    )


def test_latin_wrong_answer_is_left_to_the_human():
    """Zəncir kömək etmirsə və yazı latındırsa, maşın SUSUR."""
    assert classify_error("Nyu-York", ["Vaşinqton"], 0.0) == ""


def test_partial_overlap_is_separated_from_a_plain_miss():
    """Düz varlıq + artıq söz, tamam yanlış cavabla eyni səbətə düşməməlidir."""
    assert (
        classify_error("Vaşinqton şəhəri", ["Vaşinqton"], 0.66)
        == "qismən üst-üstə düşmə"
    )


def test_a_correct_answer_is_not_given_an_error_label():
    """STRICT düzdürsə sətir səhv siyahısında olmamalıdır; etiket verilmir."""
    assert classify_error("Vaşinqton", ["Vaşinqton"], 1.0) == ""


def test_every_returned_label_is_declared():
    """Funksiya `AUTO_ERROR_TYPES`-dan kənar etiket qaytarmamalıdır."""
    samples = [
        ("", ["Bakı"], 0.0),
        ("Bakının", ["Bakı"], 0.5),
        ("Baki", ["Bakı"], 0.0),
        ("Баку", ["Bakı"], 0.0),
        ("Gəncə", ["Bakı"], 0.0),
        ("Bakı şəhəri", ["Bakı"], 0.6),
    ]
    for prediction, gold, f1 in samples:
        assert classify_error(prediction, gold, f1) in AUTO_ERROR_TYPES


def test_summary_reports_the_human_residue():
    """Xülasə boş etiketi GİZLƏTMƏMƏLİDİR: qalan iş görünməlidir."""
    rows = [
        {"error_type_auto": "boş cavab"},
        {"error_type_auto": ""},
        {"error_type_auto": ""},
        {"error_type_auto": "morfologiya"},
    ]
    text = auto_error_summary(rows)
    assert "insan qərarı lazımdır" in text
    assert "50.0%" in text


def test_summary_lists_every_declared_type_even_at_zero():
    """Sıfır olan səbət də göstərilir; yoxsa cədvəl qaçışdan qaçışa dəyişər."""
    text = auto_error_summary([{"error_type_auto": "boş cavab"}])
    for label in AUTO_ERROR_TYPES:
        if label:
            assert label in text


def test_error_files_do_not_collide_across_prompt_styles():
    """Eyni modelin fərqli üslub qaçışları AYRI fayla yazılmalıdır.

    Fayl adına üslub girmədiyi müddətdə `Qolda-AVL-5B`-nin dörd qaçışı
    (default, script, zeroshot, plain) eyni fayla yazırdı və sonuncudan
    başqa hamısı SƏSSİZCƏ itirdi. Üstəlik qalanın hansı üslub olduğu heç
    yerdə yazılmırdı, yəni cədvəl yanlış oxuna bilərdi.
    """
    from src.analyze import RunKey, error_file_name, run_label

    styles = ("default", "script", "zeroshot", "plain")
    keys = [RunKey("issai/Qolda-AVL-5B", "az", style) for style in styles]

    # İSTEHSAL funksiyası çağırılır. Adlandırma məntiqi burada təkrarlansaydı,
    # `analyze.py` geri qaytarılsa belə test keçərdi və qüsuru tutmazdı.
    names = [error_file_name(key) for key in keys]
    assert len(set(names)) == len(styles), names

    # Başlıq da üslubu göstərməlidir, yoxsa hesabatda dörd eyni sətir olur.
    labels = [run_label(key) for key in keys]
    assert len(set(labels)) == len(styles), labels
