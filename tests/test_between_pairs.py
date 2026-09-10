"""between_pairs.py üçün testlər.

Testlər qaçış YÜKLƏMİR: permutasiya məntiqi süni rəqəmlərlə yoxlanılır.
Bu modul cütlər arası iddianı sınayır, ona görə səhv hesablama birbaşa
məqalənin başlıq iddiasına çıxır.
"""

from __future__ import annotations

import math

import pytest

from src.between_pairs import (
    ACCOUNTS,
    diff_in_mean_ranks,
    diff_in_means,
    exact_permutation,
)
from src.fine_tune_pairs import PAIRS


def test_perfect_separation_reaches_the_floor():
    """Tam ayrılmada p mümkün ən kiçik qiyməti almalıdır.

    Beş-dörd bölgüdə 126 düzülüş var və hədd **1**/126-dır, 2/126 deyil:
    müşahidə olunan düzülüş özünü sayır, tamamlayıcı çoxluq isə dörd
    elementlidir və beşlik sadalanmaya girmir. Bərabər bölgüdə hədd 2/total
    olardı. Bu fərq cədvəldə yazılan rəqəmə birbaşa çıxır.
    """
    values = [10.0, 9.0, 8.0, 7.0, 6.0, -1.0, -2.0, -3.0, -4.0]
    in_group = [True] * 5 + [False] * 4
    _, p, total = exact_permutation(values, in_group, diff_in_means)
    assert total == 126
    assert p == pytest.approx(1 / 126)


def test_no_separation_gives_a_large_p():
    """Qruplar iç-içə olanda test heç nə tapmamalıdır.

    Qiymətlər QİYMƏT oxunda növbələşməlidir, indeks oxunda yox: növbəli
    indeks seçimi təsadüfən bütün müsbətləri bir qrupa yığa bilər, ki bu
    da tam ayrılmadır, əksi deyil.
    """
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    in_group = [True, False, True, False, True, False, True, False, True]
    observed, p, _ = exact_permutation(values, in_group, diff_in_means)
    assert abs(observed) < 1.0
    assert p > 0.5


def test_ranks_resist_one_extreme_value():
    """Bir kənar dəyər ortanı sürükləyir, sıraları sürükləmir.

    `Türk 1` -16.0-dadır, çünki ingiliscəsi çöküb. Sıra variantı məhz
    ona görə var: nəticə bir cütün kənar qiymətindən asılı qalmasın.
    """
    inside = [3.0, 2.0, 1.0]
    outside = [0.0, -1.0, -100.0]
    assert diff_in_means(inside, outside) > 30
    assert diff_in_mean_ranks(inside, outside) == pytest.approx(3.0)


def test_statistic_is_symmetric_under_relabelling():
    """Qrupu tərsinə çevirmək p-ni dəyişməməlidir.

    İki tərəfli test üçün "içəri" və "çölü" adlandırmaq ixtiyaridir.
    """
    values = [5.0, 4.0, 3.0, -1.0, -2.0, -3.0]
    a = [True, True, True, False, False, False]
    b = [not x for x in a]
    _, p_a, _ = exact_permutation(values, a, diff_in_means)
    _, p_b, _ = exact_permutation(values, b, diff_in_means)
    assert p_a == pytest.approx(p_b)


def test_empty_group_is_refused():
    """Boş qrup üzərində test qurmaq mənasızdır və səssiz keçməməlidir."""
    with pytest.raises(ValueError):
        exact_permutation([1.0, 2.0, 3.0], [False, False, False], diff_in_means)


def test_the_qwen_account_is_actually_tested():
    """Rəqib izah siyahıdan silinməməlidir.

    Bu, mühafizə testidir. Baza ailəsi izahı iddianın ƏLEYHİNƏ sınaqdır və
    onu siyahıdan çıxarmaq cədvəli daha inandırıcı, nəticəni isə daha zəif
    edərdi. Silinsə, test çökür.
    """
    names = [name for name, _ in ACCOUNTS]
    assert any("Qwen" in n for n in names)
    assert any("kiril" in n for n in names)


def test_base_family_is_derived_not_copied():
    """Baza ailəsi cütün özündən çıxarılır.

    Əl ilə köçürülmüş siyahı bu layihədə bir dəfə səssizcə köhnəldi
    (`tokenizer_fertility._PAIRS`), ona görə burada törəmə xassə işlədilir.
    """
    families = {p.label: p.base_family for p in PAIRS}
    assert families["Qazax 1"] == "Qwen"
    assert families["Türk 1"] == "Mistral"
    assert families["Türk 2"] == "Llama"
    assert families["Kiril 3 (qeyri-qazax)"] == "Gemma"


def test_every_damaging_pair_shares_one_base_family():
    """Konfaundun ÖZÜ testlə qeyd olunur.

    Bu test bir iddianı qorumur, bir təhlükəni qeyd edir: hazırda zərər
    verən cütlərin hamısının bazası eyni ailədəndir. Gələcəkdə Qwen
    olmayan zərərli cüt əlavə olunsa, bu test çökəcək və həmin anda
    məqalənin ən böyük məhdudiyyəti aradan qalxmış olacaq.

    Yəni testin çökməsi PİS XƏBƏR DEYİL; düzəlişi limitasiyanı silməkdir.
    """
    damaging = {"Qazax 1", "Qazax 2", "Rus 1 (ağır)", "Rus 2 (yüngül)"}
    families = {p.base_family for p in PAIRS if p.label in damaging}
    assert families == {"Qwen"}, (
        "zərər verən cütlərin bazaları artıq eyni ailədən deyil: "
        + str(families)
        + " — konfaund qırılıb, limitasiyanı yenilə"
    )
