"""language_confusion.py üçün testlər.

Bu testlər İSTEHSAL funksiyalarını çağırır. Qaydanı test daxilində yenidən
yazmaq olmaz: onda modul geri qaytarılsa belə test keçərdi.
"""

from __future__ import annotations

from src.language_confusion import (
    AZ_ALPHABET,
    TR_ALPHABET,
    WRONG_LANGUAGE,
    build_report,
    out_of_script,
    turkish_is_subset,
    word_level_detects,
)


def label(record_id, answer, etiket=WRONG_LANGUAGE):
    return {
        "model": "test",
        "id": record_id,
        "sual": "sual?",
        "qızıl cavab": "qızıl",
        "modelin cavabı": answer,
        "etiket": etiket,
        "qeyd": "",
    }


def test_turkish_alphabet_is_a_subset_of_azerbaijani():
    """İddianın daşıyıcı hissəsi: detektorun susması konstruksiyadandır."""
    assert turkish_is_subset()
    assert AZ_ALPHABET - TR_ALPHABET == {"ə", "x", "q"}


def test_every_turkish_letter_is_invisible_to_the_detector():
    """Tək bir nümunə deyil, bütün əlifba: qayda ümumidir."""
    for letter in sorted(TR_ALPHABET):
        assert not word_level_detects(letter)
        assert not word_level_detects(letter.upper())


def test_the_paper_example_is_not_detected():
    """`yapon dili` -> `Japonca`: mətndə göstərilən nümunə."""
    assert not word_level_detects("Japonca")
    assert out_of_script("Japonca") == []


def test_english_intrusion_is_detected():
    """`w` nə türk, nə azərbaycan əlifbasındadır, ona görə tutulur."""
    assert word_level_detects("Washington")
    assert out_of_script("Washington") == ["W"]


def test_azerbaijani_specific_letters_never_fire():
    """`ə`, `x`, `q` düzgün cavabdadır; detektor onları xəta saymamalıdır."""
    assert not word_level_detects("Aşqabad")
    assert not word_level_detects("ərəb dili")


def test_report_counts_caught_and_missed():
    rows = [
        label("a-1", "Japonca"),
        label("a-2", "İngilizce"),
        label("a-3", "Washington"),
        label("a-4", "1938", etiket="faktual"),
    ]
    report = build_report(rows)
    assert "| İnsan etiketli xəta | 4 |" in report
    assert f"| Bunlardan `{WRONG_LANGUAGE}` | 3 |" in report
    assert "| Söz səviyyəli detektor tutur | 1 |" in report
    assert "| Detektor buraxır | 2 |" in report
    assert "**67%-ni buraxır.**" in report


def test_report_states_the_subset_fact():
    """Rəqəm deyil, səbəb: hesabatda alt-çoxluq faktı görünməlidir."""
    assert "**BƏLİ**" in build_report([label("a-1", "Japonca")])
