"""format_contrast.py üçün testlər."""

from __future__ import annotations

from src.format_contrast import (
    LETTERS,
    build_prompts,
    letter_of,
    score_short,
)
from src.metrics import STRICT, TRANSLIT
from src.run_eval import PROMPT_TEMPLATES

ITEM = {
    "id": "tumlu-az-1",
    "question_az": "Türkiyənin milli pul vahidi hansıdır?",
    "answer": "lirə",
    "answer_aliases": [],
    "choices": ["dollar", "lirə", "avro", "rubl"],
    "answer_letter": "B",
    "subject": "Geography",
}


def test_short_prompt_is_identical_to_the_main_benchmark():
    """Prompt HƏRFƏN eyni olmalıdır.

    Fərqli olsaydı, buradakı qısa cavab balı AZ-Eval-in cədvəlləri ilə
    müqayisə edilə bilməzdi və format fərqinə prompt fərqi qarışardı.
    """
    prompts = build_prompts(ITEM)
    assert prompts["short"] == PROMPT_TEMPLATES["az"].format(
        question=ITEM["question_az"]
    )


def test_mcq_prompt_lists_every_option_once():
    prompt = build_prompts(ITEM)["mcq"]
    for letter, choice in zip(LETTERS, ITEM["choices"]):
        assert f"{letter}) {choice}" in prompt
    assert prompt.rstrip().endswith("Cavab:")


def test_letter_extraction_accepts_the_shapes_models_produce():
    """Model hərfi bir neçə cür yazır; hamısı eyni seçimdir."""
    assert letter_of("B") == "B"
    assert letter_of("B)") == "B"
    assert letter_of("Cavab: B") == "B"
    assert letter_of("B) Qahirə") == "B"
    assert letter_of(": C") == "C"
    assert letter_of("") == ""


def test_answer_prefix_does_not_swallow_the_choice():
    """"Cavab: B" -> B, "C" hərfinə görə itməməlidir.

    Prefiks `C` ilə başlayır və naxış onu variant kimi tutmağa çalışırdı;
    sonrakı `a` uyğunluğu pozduğu üçün nəticə boş qalırdı. Model isə B
    seçmişdi. Bu, MCQ balını sistematik aşağı salır və format fərqini
    süni böyüdürdü.
    """
    assert letter_of("Cavab: B") == "B"
    assert letter_of("Cavab: C") == "C"
    assert letter_of("Answer: D") == "D"


def test_letter_extraction_ignores_a_letter_buried_in_prose():
    """Naxış sətrin əvvəlinə bağlıdır.

    Olmasaydı, "Bu sualın cavabı Ankaradır" cümləsindəki `B` seçim kimi
    oxunardı və model heç nə seçmədən bal alardı.
    """
    assert letter_of("Bu sualın cavabı Ankaradır") == ""
    assert letter_of("Düşünürəm ki, D variantı doğrudur") == ""


def test_short_scoring_uses_the_normalization_chain():
    assert score_short("lirə", ITEM, STRICT) == 1.0
    assert score_short("Cavab: lirə", ITEM, STRICT) == 1.0
    assert score_short("dollar", ITEM, STRICT) == 0.0


def test_short_scoring_accepts_the_aliases():
    item = dict(ITEM, answer="23km/saat", answer_aliases=["23 km/saat"])
    assert score_short("23 km/saat", item, STRICT) == 1.0


def test_cyrillic_answer_fails_strict_but_passes_translit():
    """Modulun ölçdüyü effektin özü.

    Qazax dilinə köklənmiş model latın sualına kirillə cavab verir. STRICT
    bunu səhv sayır, TRANSLIT isə doğru; aradakı məsafə tapıntının ölçüsüdür.
    """
    item = dict(ITEM, answer="lirə", answer_aliases=[])
    assert score_short("лирә", item, STRICT) == 0.0
    assert score_short("лирә", item, TRANSLIT) == 1.0


def test_markdown_emphasis_does_not_hide_the_choice():
    """`Cavab: **B) 800 m**` -> B.

    Qwen3-VL cavabı markdown ilə verir, Qolda isə düz mətnlə. Bəzək qəbul
    edilməsəydi, 521 cavabdan 92-si YALNIZ NƏZARƏT MODELİNDƏ oxunmazdı və
    nəticə gözlənilən istiqamətə əyilərdi: nəzarətin format fərqi süni
    kiçilər, Qoldanınkı nisbətən böyük görünərdi.
    """
    assert letter_of("Cavab: **B) 800 m**") == "B"
    assert letter_of("**B) 160**") == "B"
    assert letter_of("Cavab: **B**") == "B"
    assert letter_of('"C"') == "C"


def test_answer_after_a_restated_question_is_found():
    """Model sualı təkrar yazıb sonra cavab verirsə, cavab tapılmalıdır.

    Chat şablonu tətbiq olunanda Qwen3-VL-Thinking və Qwen3-1.7B sualı və
    variantları təkrar yazır, cavabı isə sonra verir. Yalnız sətrin əvvəlinə
    baxılsaydı, Thinking modeli 521 cavabın 494-ündə OXUNMAZ sayılardı və MCQ
    balı sıfıra yaxın çıxardı: modelin deyil, çıxarıcının uğursuzluğu.
    """
    text = "Sual: Qüvvənin momenti hansı hərflə işarə olunur?\n\nCavab: B\n\nQüvvə"
    assert letter_of(text) == "B"


def test_fallback_still_requires_the_answer_marker():
    """Sərbəst hərf axtarışı YOXDUR.

    Olsaydı, izahat mətnindəki ilk böyük hərf seçim sayılardı və model heç nə
    seçmədən bal alardı.
    """
    assert letter_of("Sual: Bu nədir?\n\nCavab yoxdur, çünki sual dolaşıqdır") == ""
    assert letter_of("Bu sualın izahı Ankara şəhəri ilə bağlıdır") == ""


def test_start_of_string_wins_over_the_fallback():
    """Əvvəldəki cavab daha az şərh tələb edir, ona görə üstündür."""
    assert letter_of("A\n\nSual: başqa sual\nCavab: D") == "A"
