"""Hesabatın oxunuşu RƏQƏMDƏN çıxarılmalıdır, sabit mətn olmamalıdır.

NİYƏ AYRI TEST. Bu modul uzun müddət sabit abzas yazırdı: "insan bazası
TAVAN DEYİL, ən yaxşı model insanı üstələyir". Həmin cümlə BİR ölçmə üçün
doğru idi (datasetin müəllifi, 59% boş, 26.5%). Dataseti görməmiş ikinci
adam ölçüləndə rəqəm çevrildi (64.0% qarşı 36.0%), mətn isə əksini yazmağa
davam edirdi.

Sabit nəticə mətni yalnız onu doğuran ölçmə üçün doğrudur.
"""

from __future__ import annotations

from src.human_baseline import reading_guide


def test_says_the_human_is_above_the_models_when_that_is_true():
    text = "\n".join(reading_guide(human=0.70, best_model=0.36, total=50, blank=7))
    assert "modellərin hamısından yuxarıdır" in text
    assert "70.0%" in text and "36.0%" in text
    assert "TAVAN QURMUR" not in text


def test_says_the_human_sets_no_ceiling_when_the_model_is_higher():
    text = "\n".join(reading_guide(human=0.286, best_model=0.367, total=49, blank=29))
    assert "TAVAN QURMUR" in text
    assert "modellərin hamısından yuxarıdır" not in text


def test_the_blank_rate_is_always_reported():
    """Boş cavab səhv sayılır, ona görə payı gizlədilə bilməz."""
    text = "\n".join(reading_guide(human=0.70, best_model=0.36, total=50, blank=7))
    assert "7 sual" in text and "14%" in text


def test_the_annotator_bias_caveat_is_always_present():
    """Cavablayanın dəstlə əlaqəsi hər iki halda yazılmalıdır.

    Müəllif cavablayıbsa meyl onun xeyrinədir; görməmiş adam cavablayıbsa
    ölçü təmizdir. Oxucu hansı halda olduğunu bilməlidir.
    """
    for human, best in ((0.70, 0.36), (0.286, 0.367)):
        text = "\n".join(reading_guide(human=human, best_model=best, total=50, blank=5))
        assert "müəllifi" in text
