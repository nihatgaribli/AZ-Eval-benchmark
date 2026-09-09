"""Cüt daxilində tokenizator nəzarəti həqiqətən qurulurmu?

NİYƏ AYRI TEST. Layihə uzun müddət "fine-tune tokenizatoru dəyişmir" ümumi
qaydasını yazırdı və ondan "cüt daxilindəki fərq tokenizasiya ilə izah edilə
bilməz" nəticəsini çıxarırdı. Qayda YANLIŞ çıxdı: dörd cütdən ikisində lüğətə
minlərlə söz əlavə edilib. İddia artıq iddia deyil, ÖLÇÜLÜR.
"""

from __future__ import annotations

from src.tokenizer_fertility import is_control_token


def test_control_tokens_are_recognised():
    for token in ("<|audio_start|>", "<|endoftext|>", "[PAD]", "[CLS]"):
        assert is_control_token(token), token


def test_ordinary_word_pieces_are_not_control_tokens():
    """Adi parçalar nişan sayılsaydı, lüğət genişlənməsi gizlənərdi."""
    for token in (" Almaty", "Kazakh", "-15", ",5", "!..", "KZT"):
        assert not is_control_token(token), token


def test_a_bare_angle_bracket_is_not_a_control_token():
    """`<` özü lüğətdə olur və mətn parçasıdır.

    Yalnız başlanğıca baxsaydıq, onu nişan sayardıq və əlavə söz sayı
    olduğundan az görünərdi.
    """
    assert not is_control_token("<")
    assert not is_control_token("<>")
    assert not is_control_token("[")


def test_the_distinction_changes_the_verdict():
    """Üç xüsusi token ilə 16 000 sözü eyni saymaq ölçünü korlayardı.

    `Qolda-AVL-5B` bazasına yalnız audio nişanları əlavə edib və bir dənə də
    söz əlavə etməyib, yəni onun MƏTN tokenizasiyası bazası ilə eynidir.
    Ayrım olmasaydı, həmin cüt də "nəzarət qurulmur" sayılardı və layihənin
    ƏSAS cütü səhvən kənara atılardı.
    """
    qolda_extra = ["<|audio_start|>", "<|audio_pad|>", "<|audio_end|>"]
    kazakh_extra = [" Almaty", " Kazakh", " KZT", "<|extra|>"]

    assert all(is_control_token(t) for t in qolda_extra)
    assert sum(not is_control_token(t) for t in kazakh_extra) == 3
