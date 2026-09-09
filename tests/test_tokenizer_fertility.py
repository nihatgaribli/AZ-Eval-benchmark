"""tokenizer_fertility.py üçün testlər.

Testlər model YÜKLƏMİR: `measure` şəbəkədən asılıdır və testin işi şəbəkəni
yoxlamaq deyil. Hesablama və hesabat məntiqi süni rəqəmlərlə yoxlanılır.

BU VƏD BİR DƏFƏ POZULMUŞDU. `build_table` cüt bölməsini qurarkən əsl
tokenizatorları çəkirdi, ona görə testlər yalnız modellər keşdə olduğu üçün
keçirdi: altı test dörd dəqiqə çəkirdi, `transformers` quraşdırılmamış təmiz
mühitdə isə beşi çökürdü. İndi ölçmə funksiyası inyeksiya edilir və aşağıdakı
saxta ölçü işlədilir, yəni vəd kodla təmin olunur.
"""

from __future__ import annotations

from src.tokenizer_fertility import Fertility, build_table


def fake_measure(base: str, tuned: str) -> tuple[int, int] | None:
    """Bir cütü nəzarətli, birini nəzarətsiz göstərən saxta ölçü.

    Hər iki halın mətni yoxlanıla bilsin deyə ikisi də lazımdır: nəzarət
    qurulan cütlər izah paraqrafını, qurulmayanlar xəbərdarlığı doğurur.
    """
    return (0, 3) if "Qolda" in tuned else (16000, 0)


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
    table = build_table(rows, measure=fake_measure)
    assert table.index("best") < table.index("middle") < table.index("worst")


def test_table_names_the_extremes():
    """Gözlənilən dəyər hesablanır, sərt kodlanmır.

    Sərt kodlansaydı, test yuvarlaqlaşdırmanın son rəqəmini yoxlayardı, halbuki
    yoxlanmalı olan şey ən yaxşı və ən pis modelin cədvəldə göstərilməsidir.
    """
    rows = [Fertility("a", 4.02, 1.38), Fertility("b", 3.02, 1.42)]
    table = build_table(rows, measure=fake_measure)
    for row in rows:
        assert f"{row.ratio:.2f}x" in table


def test_table_refuses_to_claim_causation():
    """Modul izahedici kontekst verir, səbəb iddiası yox.

    Yüksək məhsuldarlıq aşağı balla birlikdə mövcuddur; onun SƏBƏBİ olduğunu
    bu ölçü göstərmir və mətn bunu açıq deməlidir.
    """
    table = build_table([Fertility("a", 3.0, 1.5)], measure=fake_measure)
    assert "Səbəb-nəticə" in table
    assert "DEYİL" in table


def test_table_states_the_within_pair_control():
    """Cüt daxilində tokenizator eynidir, bu, nəticə üçün nəzarətdir."""
    table = build_table([Fertility("a", 3.0, 1.5)], measure=fake_measure)
    assert "tokenizasiya ilə izah edilə" in table


def test_single_model_does_not_break_the_extremes():
    """Bir model verildikdə ən yaxşı və ən pis eyni sətirdir."""
    table = build_table([Fertility("only", 3.0, 1.5)], measure=fake_measure)
    assert "only" in table
    assert "2.00x" in table


def test_unmeasurable_pairs_say_so_instead_of_going_quiet():
    """Heç bir cüt ölçülməyəndə cədvəl bunu AÇIQ deməlidir.

    Əvvəl izah paraqrafı sadəcə yazılmırdı, ona görə cədvəl sırf `?`
    sətirlərindən ibarət olurdu və nə demək istədiyini demirdi. Oxucu bunu
    "nəzarət qurulmayıb" kimi deyil, boş nəticə kimi oxuya bilərdi.
    """
    table = build_table([Fertility("a", 3.0, 1.5)], measure=lambda base, tuned: None)
    assert "HEÇ BİR CÜT ÖLÇÜLMƏDİ" in table
    assert "ölçülmədi" in table
    # Ölçmə olmayanda nəzarət iddiası da olmamalıdır.
    assert "tokenizasiya ilə izah edilə" not in table
