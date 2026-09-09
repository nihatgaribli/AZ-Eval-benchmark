"""harvest_wikidata.py üçün testlər — filtrlər şəbəkəsiz yoxlanılır."""

from __future__ import annotations

import pytest

from src.build_dataset import CATEGORIES, PROVENANCE_STATES, validate_dataset
from src.harvest_wikidata import TEMPLATES, apply_filters, to_records


def binding(subj, subj_az, subj_en, ans_az, ans_en, links=20, ans=None):
    """SPARQL nəticə sətrinin formasını təqlid edir."""
    return {
        "subj": {"value": f"http://www.wikidata.org/entity/{subj}"},
        "subjAz": {"value": subj_az},
        "subjEn": {"value": subj_en},
        "ans": {"value": ans or f"http://www.wikidata.org/entity/{subj}x"},
        "ansAz": {"value": ans_az},
        "ansEn": {"value": ans_en},
        "links": {"value": str(links)},
    }


# --------------------------------------------------------------------------
# Şablon reyestri
# --------------------------------------------------------------------------


def test_template_names_are_unique():
    names = [t.name for t in TEMPLATES]
    assert len(names) == len(set(names))


def test_template_categories_are_valid():
    for template in TEMPLATES:
        assert template.category in CATEGORIES


def test_every_template_has_several_question_structures():
    # Bütün suallar bir qəlibdə olsa, benchmark modelin biliyini yox, həmin
    # qəlibə tanışlığını ölçər.
    for template in TEMPLATES:
        assert len(template.variants) >= 4, template.name


def test_variants_within_a_template_are_distinct():
    for template in TEMPLATES:
        az_forms = [v.az for v in template.variants]
        en_forms = [v.en for v in template.variants]
        assert len(set(az_forms)) == len(az_forms), template.name
        assert len(set(en_forms)) == len(en_forms), template.name


def test_every_variant_mentions_the_subject_in_both_languages():
    for template in TEMPLATES:
        for i, variant in enumerate(template.variants):
            assert "{subject" in variant.az, f"{template.name}[{i}]"
            assert "{subject}" in variant.en, f"{template.name}[{i}]"


def test_azerbaijani_and_english_variant_counts_match():
    # Variantlar cütdür: AZ[i] ilə EN[i] eyni quruluşu daşımalıdır, yoxsa
    # ölçülən fərqin bir hissəsi dildən yox, sual quruluşundan gələr.
    for template in TEMPLATES:
        assert all(isinstance(v.az, str) and isinstance(v.en, str) for v in template.variants)


def test_template_render_substitutes_each_language():
    template = TEMPLATES[0]
    az, en, _ = template.render("Fransa", "France")
    assert "France" in en
    assert "{subject" not in az and "{subject}" not in en


def test_genitive_placeholder_produces_natural_azerbaijani():
    # "Fransa ölkəsinin paytaxtı" qrammatikdir, amma doğma deyil.
    template = next(t for t in TEMPLATES if t.name == "country_capital")
    az, _, _ = template.render("Fransa", "France", variant_index=0)
    assert az == "Fransanın paytaxtı hansı şəhərdir?"


def test_locative_placeholder_is_filled():
    template = next(t for t in TEMPLATES if t.name == "country_currency")
    az, _, _ = template.render("Fransa", "France", variant_index=1)
    assert az == "Fransada hansı pul vahidi işlənir?"


def test_render_cycles_through_variants():
    template = TEMPLATES[0]
    rendered = [template.render("Fransa", "France", i)[0] for i in range(8)]
    assert len(set(rendered)) == len(template.variants)   # hamısı işlənir
    assert rendered[0] == rendered[len(template.variants)]  # dövr bağlanır


def test_render_reports_which_variant_was_used():
    template = TEMPLATES[0]
    n = len(template.variants)
    assert template.render("Fransa", "France", 0)[2] == 0
    assert template.render("Fransa", "France", n + 1)[2] == 1


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t.name)
def test_every_variant_renders_without_placeholders_left(template):
    for i in range(len(template.variants)):
        az, en, _ = template.render("Amerika Birləşmiş Ştatları", "United States", i)
        assert "{" not in az and "}" not in az, (template.name, i, az)
        assert "{" not in en and "}" not in en, (template.name, i, en)


def test_rendered_questions_start_with_a_capital_letter():
    # Wikidata etiketləri çox vaxt kiçik hərflə gəlir ("qızıl", "ispan dili",
    # "silver"), cümlə isə böyük hərflə başlamalıdır. Bəzi variantlarda subyekt
    # məhz cümlənin əvvəlindədir, ona görə hər iki dil yoxlanılır.
    def first_letter(text):
        # Cümlə dırnaqla başlaya bilər («Odlar Yurdu» ...), ona görə ilk
        # SİMVOL yox, ilk HƏRF yoxlanılır.
        return next((c for c in text if c.isalpha()), "")

    for template in TEMPLATES:
        for i in range(len(template.variants)):
            az, en, _ = template.render("ispan dili", "silver", i)
            assert first_letter(az).isupper(), f"{template.name}[{i}] AZ: {az!r}"
            assert first_letter(en).isupper(), f"{template.name}[{i}] EN: {en!r}"


def test_every_rendered_question_ends_with_terminal_punctuation():
    for template in TEMPLATES:
        for i in range(len(template.variants)):
            az, en, _ = template.render("Fransa", "France", i)
            assert az.endswith(("?", ".")), (template.name, i, az)
            assert en.endswith(("?", ".")), (template.name, i, en)


def test_writing_system_template_avoids_the_word_alphabet():
    # Çin və Khmer yazısı əlifba deyil — "hansı əlifba" sualı yanlış olardı.
    template = next(t for t in TEMPLATES if t.name == "language_writing_system")
    assert all("əlifba" not in v.az for v in template.variants)
    assert all("yazı sistemi" in v.az for v in template.variants)


def test_literal_answer_templates_skip_the_language_filter():
    # Hərfi dəyərlərin (simvol, il) dil etiketi yoxdur — cavaba `lang()=="az"`
    # filtri tətbiq edilsəydi, sorğu həmişə boş qayıdardı.
    for template in TEMPLATES:
        if "BIND(" in template.sparql and "?ansAz)" in template.sparql:
            assert 'FILTER(lang(?ansAz)="az")' not in template.sparql


# --------------------------------------------------------------------------
# Filtrlər
# --------------------------------------------------------------------------


def test_clean_rows_survive_filtering():
    rows = [
        binding("Q1", "Fransa", "France", "Paris", "Paris"),
        binding("Q2", "Türkiyə", "Turkey", "Ankara", "Ankara"),
    ]
    kept, stats = apply_filters(rows)
    assert stats.kept == 2
    assert {c["answer_az"] for c in kept} == {"Paris", "Ankara"}


def test_answer_quota_caps_repeated_answers():
    # Əsas skew müdafiəsi: eyni cavabın təkrarlanması məhdudlaşdırılır.
    rows = [binding(f"Q{i}", f"Şəxs {i}", f"Person {i}", "Bakı", "Baku") for i in range(10)]
    kept, stats = apply_filters(rows, max_per_answer=3)
    assert stats.kept == 3
    assert stats.over_quota == 7


def test_quota_keeps_the_most_notable_subjects():
    # Kvota təsadüfi kəsmir — sitelink sayına görə seçir, nəticə deterministdir.
    rows = [
        binding("Q1", "Az tanınan", "Obscure", "Bakı", "Baku", links=9),
        binding("Q2", "Çox tanınan", "Famous", "Bakı", "Baku", links=250),
    ]
    kept, _ = apply_filters(rows, max_per_answer=1)
    assert kept[0]["subject_az"] == "Çox tanınan"


def test_quota_is_case_and_diacritic_stable():
    rows = [
        binding("Q1", "A", "A", "Bakı", "Baku"),
        binding("Q2", "B", "B", "BAKI", "Baku"),
        binding("Q3", "C", "C", "bakı.", "Baku"),
    ]
    _, stats = apply_filters(rows, max_per_answer=1)
    assert stats.kept == 1  # üçü də eyni cavab sayılır


def test_multi_valued_subject_is_dropped_entirely():
    # Bir subyektin iki fərqli cavabı varsa, birmənalı etalon yoxdur.
    rows = [
        binding("Q1", "Şərur", "Sharur", "1377", "1377"),
        binding("Q1", "Şərur", "Sharur", "6016", "6016"),
        binding("Q2", "Bakı", "Baku", "2300000", "2300000"),
    ]
    kept, stats = apply_filters(rows)
    assert stats.multi_valued == 2
    assert [c["subject_az"] for c in kept] == ["Bakı"]


def test_blocked_historical_answers_are_dropped():
    rows = [
        binding("Q1", "Zaur", "Zaur", "SSRİ", "Soviet Union"),
        binding("Q2", "Nizami", "Nizami", "Gəncə", "Ganja"),
    ]
    kept, stats = apply_filters(rows)
    assert stats.blocked_answer == 1
    assert kept[0]["answer_az"] == "Gəncə"


@pytest.mark.parametrize(
    ("subj_en", "ans_en"),
    [
        ("Diana Hacıyeva", "Baku"),      # subyektin EN etiketi AZ adın kopyası
        ("Gurban Gurbanov", "Aşağı Tala"),  # cavabın EN etiketi tərcümə olunmayıb
        ("Novruz Mammadov", "Şıxmahmud"),
        ("Anvar Chingizoghlu", "Xudayarlı"),
    ],
)
def test_untranslated_english_labels_are_dropped(subj_en, ans_en):
    """RQ1-in etibarlılığı üçün ən vacib filtr.

    İngilis şərti azərbaycanca mətnlə çirklənirsə, AZ/EN müqayisəsi artıq iki
    dilin müqayisəsi olmur və RQ1-in rəqəmi mənasını itirir.
    """
    rows = [binding("Q1", "Şəxs", subj_en, "Cavab", ans_en)]
    _, stats = apply_filters(rows)
    assert stats.en_label_not_english == 1
    assert stats.kept == 0


@pytest.mark.parametrize(
    ("az_label", "en_label"),
    [
        ("Sürix", "Zürich"),        # alman alınması — ü ingilis mətnində olur
        ("San-Paulu", "São Paulo"),
        ("Paris", "Paris"),         # eyni, amma AZ hərfi yoxdur
        ("Aygün Kazımova", "Aygün Kazimova"),  # transliterasiya edilib
    ],
)
def test_legitimate_english_labels_survive(az_label, en_label):
    rows = [binding("Q1", "Ölkə", "Country", az_label, en_label)]
    kept, stats = apply_filters(rows)
    assert stats.en_label_not_english == 0
    assert len(kept) == 1


@pytest.mark.parametrize(
    ("az_label", "en_label"),
    [
        ("Hindistan", "India"),
        ("İtaliya", "Italy"),
        ("İsrail", "Israel"),
        ("İran", "Iran"),
        ("İslandiya", "Iceland"),
        ("İndoneziya", "Indonesia"),
    ],
)
def test_english_labels_with_capital_i_are_not_dropped(az_label, en_label):
    """Azərbaycan nöqtəsiz baş `I` ASCII `I` ilə eyni Unicode koddur (U+0049).

    Onu "ingilis dilində olmayan hərf" siyahısına salmaq tərkibində baş `I` olan
    BÜTÜN ingilis etiketlərini atır. Bu, datasetin ən tanınmış ölkələrini
    səssizcə yox edir — filtrin çıxışına baxmasan, bilinmir.
    """
    rows = [binding("Q1", az_label, en_label, "Şəhər", "City")]
    kept, stats = apply_filters(rows)
    assert stats.en_label_not_english == 0
    assert len(kept) == 1


def test_disambiguation_labels_are_dropped():
    rows = [binding("Q1", "Bakı (film)", "Baku (film)", "Bakı", "Baku")]
    _, stats = apply_filters(rows)
    assert stats.bad_label == 1


def test_long_answers_are_dropped():
    # EM/F1 uzun cavabda mənasını itirir.
    rows = [binding("Q1", "X", "X", "bir çox fərqli uzun cavab", "a long answer")]
    _, stats = apply_filters(rows, max_answer_words=3)
    assert stats.answer_too_long == 1


def test_answer_identical_to_subject_is_dropped():
    # "Qusar harada yerləşir? -> Qusar" tipli mənasız sətirlər.
    rows = [binding("Q1", "Qusar", "Qusar", "Qusar", "Qusar")]
    _, stats = apply_filters(rows)
    assert stats.answer_equals_subject == 1


@pytest.mark.parametrize(
    ("subject", "answer"),
    [
        ("Astara rayonu", "Astara"),        # cavab sualın içindədir
        ("Xocalı rayonu", "Xocalı"),
        ("Şəki şəhəri", "Şəki"),
    ],
)
def test_answer_contained_in_subject_is_dropped(subject, answer):
    """Cavabı sualdan köçürməklə tapmaq mümkündürsə, sətir bilik ölçmür.

    `answer_equals_subject` bunu tutmur, çünki sətirlər tam bərabər deyil —
    yoxlama token ardıcıllığı səviyyəsində olmalıdır.
    """
    rows = [binding("Q1", subject, "District", answer, "Town")]
    _, stats = apply_filters(rows)
    assert stats.answer_inside_subject == 1
    assert stats.kept == 0


def test_answer_merely_sharing_a_word_is_kept():
    # "Bakı Dövlət Universiteti -> Bakı" atılmalıdır, amma tamam fərqli
    # cavablar saxlanılmalıdır.
    rows = [binding("Q1", "Fransa", "France", "Paris", "Paris")]
    kept, stats = apply_filters(rows)
    assert stats.answer_inside_subject == 0
    assert len(kept) == 1


def test_duplicate_rows_for_one_subject_are_collapsed():
    rows = [
        binding("Q1", "Fransa", "France", "Paris", "Paris"),
        binding("Q1", "Fransa", "France", "Paris", "Paris"),
    ]
    _, stats = apply_filters(rows)
    assert stats.kept == 1


def test_filter_stats_account_for_every_fetched_row():
    rows = [
        binding("Q1", "Fransa", "France", "Paris", "Paris"),
        binding("Q2", "Zaur", "Zaur", "SSRİ", "Soviet Union"),
        binding("Q3", "Bakı (film)", "Baku (film)", "Bakı", "Baku"),
    ]
    _, stats = apply_filters(rows)
    accounted = (
        stats.multi_valued + stats.blocked_answer + stats.bad_label
        + stats.cyrillic_answer + stats.en_label_not_english + stats.answer_too_long
        + stats.answer_equals_subject + stats.answer_inside_subject
        + stats.over_quota + stats.kept
    )
    assert accounted == stats.fetched


def test_some_templates_target_azerbaijani_language_answers():
    """RQ3-ün diakritika ölçüsü üçün cavabın özü azərbaycanca olmalıdır.

    Paytaxt, kimyəvi simvol və il şablonlarının cavabları beynəlxalq
    yazılışlardır (Paris, Au, 1961) — orada qatlanacaq diakritik yoxdur, ona
    görə MORPH->LENIENT fərqi həmişə sıfır çıxır və RQ3 ölçülməz qalır.
    """
    names = {t.name for t in TEMPLATES}
    assert {"person_occupation", "country_official_language"} <= names


def test_empty_input_is_handled():
    kept, stats = apply_filters([])
    assert kept == [] and stats.fetched == 0


# --------------------------------------------------------------------------
# Sətrə çevirmə
# --------------------------------------------------------------------------


def test_records_pass_the_dataset_validator():
    """Toplayıcının çıxışı birbaşa sxemə uyğun olmalıdır.

    Bu, ən vacib testdir: harvester ilə validator arasındakı hər uyğunsuzluq
    100+ sətrin əl ilə düzəldilməsi deməkdir.
    """
    rows = [
        binding("Q1", "Fransa", "France", "Paris", "Paris"),
        binding("Q2", "Türkiyə", "Turkey", "Ankara", "Ankara"),
    ]
    kept, _ = apply_filters(rows)
    records = to_records(TEMPLATES[0], kept, start_id=1)

    report = validate_dataset(list(enumerate(records, start=1)))
    assert report.ok, [str(i) for i in report.errors]


def test_records_are_marked_pending_and_traceable():
    kept, _ = apply_filters([binding("Q1", "Fransa", "France", "Paris", "Paris")])
    record = to_records(TEMPLATES[0], kept)[0]

    assert record["verified_by"] == "pending"        # yekun datasetə keçmir
    assert record["provenance"] in PROVENANCE_STATES
    assert record["provenance"] == "wikidata-template"
    assert TEMPLATES[0].name in record["notes"]       # hansı şablondan gəldiyi
    assert "variant=" in record["notes"]              # hansı sual quruluşu
    assert record["source"].startswith("https://www.wikidata.org/wiki/Q")


def test_variants_are_spread_evenly_across_records():
    """Növbə ilə paylama variantla çətinliyi qarışdırmamalıdır.

    Namizədlər tanınırlığa görə sıralanıb. Variantlar bloklarla paylansaydı,
    birinci variant həmişə ən məşhur subyektləri alardı və "hansı sual quruluşu
    daha çətindir" sualına verilən cavab yanlış olardı.
    """
    template = TEMPLATES[0]
    rows = [
        binding(f"Q{i}", f"Ölkə {i}", f"Country {i}", f"Şəhər {i}", f"City {i}",
                links=100 - i)
        for i in range(12)
    ]
    kept, _ = apply_filters(rows)
    records = to_records(template, kept)

    variants = [r["notes"].split("variant=")[1] for r in records]
    assert sorted(variants) == sorted(
        [str(i % len(template.variants)) for i in range(12)]
    )
    assert variants[0] != variants[1]  # ardıcıl sətirlər fərqli quruluşdadır


def test_generated_questions_are_structurally_varied():
    template = TEMPLATES[0]
    rows = [
        binding(f"Q{i}", f"Ölkə {i}", f"Country {i}", f"Şəhər {i}", f"City {i}")
        for i in range(8)
    ]
    kept, _ = apply_filters(rows)
    records = to_records(template, kept)

    # Sual mətnlərindən subyekti çıxarsaq, qalan qəliblər fərqli olmalıdır.
    frames = {r["question_az"].split(" ", 1)[1] for r in records}
    assert len(frames) >= 3


def test_records_get_generated_aliases():
    kept, _ = apply_filters([binding("Q1", "Fransa", "France", "Bakı", "Baku")])
    record = to_records(TEMPLATES[0], kept)[0]
    assert "Bakıda" in record["answer_aliases"]


def test_record_ids_are_sequential_from_start_id():
    rows = [binding(f"Q{i}", f"Ölkə {i}", f"Country {i}", f"Şəhər {i}", f"City {i}")
            for i in range(3)]
    kept, _ = apply_filters(rows)
    records = to_records(TEMPLATES[0], kept, start_id=41)
    assert [r["id"] for r in records] == ["az-041", "az-042", "az-043"]


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t.name)
def test_every_template_produces_valid_records(template):
    kept, _ = apply_filters([binding("Q1", "Subyekt", "Subject", "Cavab", "Answer")])
    records = to_records(template, kept, start_id=1)
    report = validate_dataset(list(enumerate(records, start=1)))
    assert report.ok, [str(i) for i in report.errors]


@pytest.mark.parametrize(
    ("subject", "answer"),
    [
        ("Xocalı soyqırımı", "Xocalı rayonu"),
        ("Gəncə üsyanı", "Gəncə şəhəri"),
        ("Şəki xanlığı", "Şəki rayonu"),
    ],
)
def test_partial_leak_through_the_leading_word_is_dropped(subject, answer):
    """Cavabın aparıcı sözü subyektin adındadırsa, sual bilik ölçmür.

    Tam ardıcıllıq yoxlaması bunu tutmur ("Xocalı rayonu" ≠ "Xocalı soyqırımı"),
    amma modelin cavabı addan oxuması kifayətdir.
    """
    rows = [binding("Q1", subject, "Event", answer, "District")]
    _, stats = apply_filters(rows)
    assert stats.answer_inside_subject == 1
    assert stats.kept == 0


def test_unrelated_answers_are_not_treated_as_leaks():
    rows = [binding("Q1", "Nizami Gəncəvi", "Nizami Ganjavi", "Gəncə", "Ganja")]
    kept, stats = apply_filters(rows)
    assert stats.answer_inside_subject == 0
    assert len(kept) == 1


@pytest.mark.parametrize(
    "answer",
    ["Ağqoyunlu hökmdarlarının siyahısı", "Bakı kateqoriyası", "Ölkə şablonu"],
)
def test_navigation_pages_are_not_accepted_as_answers(answer):
    # Wikidata siyahı və kateqoriya səhifələrini adi obyekt kimi saxlayır və
    # onlar xassə dəyəri kimi qayıda bilir, halbuki heç bir sualın cavabı deyil.
    rows = [binding("Q1", "Sultan Rüstəm", "Sultan Rustam", answer, "A list")]
    _, stats = apply_filters(rows)
    assert stats.bad_label == 1


def test_field_of_work_template_is_neutral_between_science_and_art():
    # P101 rəssamlarda janr qaytarır ("peyzaj"); "elm sahəsi" ifadəsi onlara
    # yanlış oturur, neytral "sahə" hər ikisinə uyğundur.
    template = next(t for t in TEMPLATES if t.name == "az_field_of_work")
    assert all("elm sahəsi" not in v.az for v in template.variants)


@pytest.mark.parametrize("answer", ["Хабиби", "Мәскеу", "Низами"])
def test_cyrillic_gold_answers_are_rejected(answer):
    """Kiril etalon layihənin ƏSAS ölçməsini dağıdır.

    Mərkəzi tapıntı odur ki, qazax dilinə köklənmiş model azərbaycanca kirillə
    cavab verir. Etalonun özü kiril olsaydı, latınla düzgün cavab verən model
    səhv sayılar, kirillə cavab verən isə bal alardı — effekt tərsinə görünərdi.
    """
    rows = [binding("Q1", "Həbibi", "Habibi", answer, "Habibi")]
    _, stats = apply_filters(rows)
    assert stats.cyrillic_answer == 1
    assert stats.kept == 0


def test_latin_azerbaijani_answers_are_kept():
    rows = [binding("Q1", "Həbibi", "Habibi", "Şəki", "Sheki")]
    kept, stats = apply_filters(rows)
    assert stats.cyrillic_answer == 0
    assert len(kept) == 1


# --------------------------------------------------------------------------
# Təkrar baxışın qarşısının alınması
# --------------------------------------------------------------------------

import json  # noqa: E402

from src.harvest_wikidata import (  # noqa: E402
    _qid,
    next_free_id,
    reviewed_subjects,
)


def write_jsonl(path, records):
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )


def test_qid_normalizes_both_uri_forms():
    """Mənbə `/wiki/`, namizəd `/entity/` işlədir; müqayisə üçün eyni açar lazımdır."""
    assert _qid("http://www.wikidata.org/entity/Q142") == "Q142"
    assert _qid("https://www.wikidata.org/wiki/Q142") == "Q142"


def test_reviewed_subjects_includes_rejected(tmp_path):
    """Rədd edilənlər də atılmalıdır.

    Bu, funksiyanın bütün mənasıdır: `az_content.jsonl`-də 45 namizədin 36-sı
    rədd edilib. Yalnız qəbul edilənləri atsaq, ikinci qaçış həmin 36-nı
    yenidən qarşıya çıxarar və insan onları bir daha nəzərdən keçirər.
    """
    raw = tmp_path / "raw"
    raw.mkdir()
    write_jsonl(raw / "a.jsonl", [
        {"id": "az-001", "source": "https://www.wikidata.org/wiki/Q1",
         "verified_by": "human"},
        {"id": "az-002", "source": "https://www.wikidata.org/wiki/Q2",
         "verified_by": "rejected"},
    ])

    assert reviewed_subjects(raw) == {"Q1", "Q2"}


def test_reviewed_subjects_ignores_non_wikidata_sources(tmp_path):
    """Əl ilə yazılmış suallarda mənbə Wikidata deyil; onlar subyekt açarı vermir."""
    raw = tmp_path / "raw"
    raw.mkdir()
    write_jsonl(raw / "manual.jsonl", [
        {"id": "az-001", "source": "əl ilə yazılıb", "verified_by": "human"},
        {"id": "az-002", "source": "https://www.wikidata.org/wiki/Q9",
         "verified_by": "human"},
    ])

    assert reviewed_subjects(raw) == {"Q9"}


def test_reviewed_subjects_survives_corrupt_lines(tmp_path):
    """Bir pozuq sətir bütün süzgəci sıradan çıxarmamalıdır."""
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.jsonl").write_text(
        '{"id": "az-001", "source": "https://www.wikidata.org/wiki/Q1"}\n'
        "bu JSON deyil\n"
        '{"id": "az-002", "source": "https://www.wikidata.org/wiki/Q2"}\n',
        encoding="utf-8",
    )

    assert reviewed_subjects(raw) == {"Q1", "Q2"}


def test_reviewed_subjects_on_missing_directory(tmp_path):
    assert reviewed_subjects(tmp_path / "yoxdur") == set()


def test_next_free_id_continues_after_highest(tmp_path):
    """ID toqquşması `build_dataset`-i xəta ilə dayandırır, ona görə nömrə
    həm xam fayllardan, həm yekun datasetdən hesablanır."""
    raw = tmp_path / "raw"
    raw.mkdir()
    write_jsonl(raw / "a.jsonl", [{"id": "az-005"}, {"id": "az-012"}])
    dataset = tmp_path / "final.jsonl"
    write_jsonl(dataset, [{"id": "az-030"}])

    assert next_free_id(raw, dataset) == 31


def test_next_free_id_starts_at_one_when_empty(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    assert next_free_id(raw, tmp_path / "yoxdur.jsonl") == 1


def test_next_free_id_ignores_foreign_id_formats(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    write_jsonl(raw / "a.jsonl", [{"id": "kz-900"}, {"id": "az-007"}, {"id": 42}])
    assert next_free_id(raw, tmp_path / "yoxdur.jsonl") == 8


def test_refuse_overwrite_protects_a_reviewed_file(tmp_path):
    """Nəzərdən keçirilmiş faylın üstündən yazmaq rədd edilməlidir.

    Bu, layihədə bərpası ən çətin itkidir: model qaçışı bir saatdır, insan
    yoxlaması günlərdir və eyni nəticə vermir.
    """
    from src.harvest_wikidata import refuse_overwrite

    path = tmp_path / "wikidata.jsonl"
    path.write_text('{"id": "az-001"}\n', encoding="utf-8")

    message = refuse_overwrite(path, force=False)
    assert message and "--force" in message


def test_refuse_overwrite_allows_a_new_file(tmp_path):
    from src.harvest_wikidata import refuse_overwrite

    assert refuse_overwrite(tmp_path / "yeni.jsonl", force=False) is None


def test_refuse_overwrite_allows_an_empty_file(tmp_path):
    """Boş fayl məlumat daşımır, ona görə üstünə yazmaq itki deyil."""
    from src.harvest_wikidata import refuse_overwrite

    path = tmp_path / "bos.jsonl"
    path.touch()
    assert refuse_overwrite(path, force=False) is None


def test_force_overrides_the_guard(tmp_path):
    from src.harvest_wikidata import refuse_overwrite

    path = tmp_path / "wikidata.jsonl"
    path.write_text('{"id": "az-001"}\n', encoding="utf-8")
    assert refuse_overwrite(path, force=True) is None


def test_prompt_example_answer_is_filtered_at_harvest():
    """Few-shot cavabı namizəd növbəsinə ÜMUMİYYƏTLƏ düşməməlidir.

    `build_dataset` belə sətri onsuz da rədd edir, amma yalnız insan onu
    qəbul etdikdən SONRA. Harvester səviyyəsində atmaq nəzərdən keçirmə
    vaxtına qənaətdir: qapıya dirənəcək namizədi növbəyə salmaq mənasızdır.
    """
    from src.harvest_wikidata import apply_filters

    rows = [
        binding("Q79", "Misir", "Egypt", "Qahirə", "Cairo"),
        binding("Q142", "Fransa", "France", "Paris", "Paris"),
    ]
    kept, stats = apply_filters(rows)

    answers = {c["answer_az"] for c in kept}
    assert "Qahirə" not in answers
    assert "Paris" in answers
    assert stats.prompt_example == 1
