"""tokenizer_fertility.py üçün testlər.

Testlər model YÜKLƏMİR: `measure` şəbəkədən asılıdır və testin işi şəbəkəni
yoxlamaq deyil. Hesablama və hesabat məntiqi süni rəqəmlərlə yoxlanılır.
"""

from __future__ import annotations

from src.tokenizer_fertility import Fertility, build_table


def test_ratio_is_az_over_en():
    f = Fertility("m", az_per_word=3.56, en_per_word=1.43)
    assert round(f.ratio, 2) == 2.49


def test_table_sorts_from_best_to_worst():
    """Ən yaxşı tokenizator yuxarıda olmalıdır.

    Sıra rastgələ olsaydı, oxucu hansı modelin dilə daha uyğun olduğunu
    cədvəli gözü ilə süzərək tapmalı olardı.
    """
    rows = [
        Fertility("worst", 4.02, 1.38),
        Fertility("best", 3.02, 1.42),
        Fertility("middle", 3.56, 1.43),
    ]
    table = build_table(rows)
    assert table.index("best") < table.index("middle") < table.index("worst")


def test_table_names_the_extremes():
    """Gözlənilən dəyər hesablanır, sərt kodlanmır.

    Sərt kodlansaydı, test yuvarlaqlaşdırmanın son rəqəmini yoxlayardı, halbuki
    yoxlanmalı olan şey ən yaxşı və ən pis modelin cədvəldə göstərilməsidir.
    """
    rows = [Fertility("a", 4.02, 1.38), Fertility("b", 3.02, 1.42)]
    table = build_table(rows)
    for row in rows:
        assert f"{row.ratio:.2f}x" in table


def test_table_refuses_to_claim_causation():
    """Modul izahedici kontekst verir, səbəb iddiası yox.

    Yüksək məhsuldarlıq aşağı balla birlikdə mövcuddur; onun SƏBƏBİ olduğunu
    bu ölçü göstərmir və mətn bunu açıq deməlidir.
    """
    table = build_table([Fertility("a", 3.0, 1.5)])
    assert "Səbəb-nəticə" in table
    assert "DEYİL" in table


def test_table_states_the_within_pair_control():
    """Cüt daxilində tokenizator eynidir, bu, nəticə üçün nəzarətdir."""
    table = build_table([Fertility("a", 3.0, 1.5)])
    assert "tokenizasiya ilə izah edilə" in table


def test_single_model_does_not_break_the_extremes():
    """Bir model verildikdə ən yaxşı və ən pis eyni sətirdir."""
    table = build_table([Fertility("only", 3.0, 1.5)])
    assert "only" in table
    assert "2.00x" in table
