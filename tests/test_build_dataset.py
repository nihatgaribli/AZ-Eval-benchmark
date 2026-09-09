"""build_dataset.py üçün testlər."""

from __future__ import annotations

import json

import pytest

from src.build_dataset import (
    build_dataset,
    equivalence_aliases,
    dataset_stats,
    fill_aliases,
    load_jsonl,
    validate_dataset,
    write_jsonl,
)

VALID_ROW = {
    "id": "az-001",
    "question_az": "Azərbaycanın paytaxtı hansı şəhərdir?",
    "question_en": "What is the capital of Azerbaijan?",
    "answer": "Bakı",
    "answer_en": "Baku",
    "answer_aliases": ["Bakıda"],
    "category": "geography",
    "source": "https://example.org/az-geo",
    "provenance": "manual",
    "verified_by": "human",
}


def row(**overrides):
    return {**VALID_ROW, **overrides}


def messages(report):
    return " | ".join(i.message for i in report.issues)


def as_records(rows):
    return list(enumerate(rows, start=1))


# --------------------------------------------------------------------------
# Sxem yoxlaması
# --------------------------------------------------------------------------


def test_valid_row_passes_without_errors_or_warnings():
    report = validate_dataset(as_records([VALID_ROW]))
    assert report.ok
    assert report.warnings == []


@pytest.mark.parametrize(
    "missing",
    [
        "id", "question_az", "question_en", "answer", "answer_en",
        "category", "source", "provenance", "verified_by",
    ],
)
def test_missing_required_field_is_an_error(missing):
    bad = row()
    del bad[missing]
    report = validate_dataset(as_records([bad]))
    assert not report.ok
    assert any(i.field == missing for i in report.errors)


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_value_is_an_error(blank):
    report = validate_dataset(as_records([row(answer=blank)]))
    assert not report.ok
    assert any(i.field == "answer" for i in report.errors)


def test_non_string_required_field_is_an_error():
    report = validate_dataset(as_records([row(answer=42)]))
    assert not report.ok


@pytest.mark.parametrize("bad_id", ["001", "az_001", "AZ-001", "az-1", "az-abc"])
def test_malformed_id_is_an_error(bad_id):
    report = validate_dataset(as_records([row(id=bad_id)]))
    assert any(i.field == "id" for i in report.errors)


def test_unknown_category_is_an_error():
    report = validate_dataset(as_records([row(category="sports")]))
    assert any(i.field == "category" for i in report.errors)


def test_unknown_verification_state_is_an_error():
    report = validate_dataset(as_records([row(verified_by="maybe")]))
    assert any(i.field == "verified_by" for i in report.errors)


def test_unknown_provenance_is_an_error():
    report = validate_dataset(as_records([row(provenance="somewhere")]))
    assert any(i.field == "provenance" for i in report.errors)


@pytest.mark.parametrize(
    "provenance", ["manual", "wikidata-template", "llm-passage"]
)
def test_known_provenance_values_pass(provenance):
    assert validate_dataset(as_records([row(provenance=provenance)])).ok


def test_empty_aliases_are_flagged_as_a_warning():
    report = validate_dataset(as_records([row(answer_aliases=[])]))
    assert report.ok
    assert any(i.field == "answer_aliases" for i in report.warnings)


def test_unknown_field_is_a_warning_not_an_error():
    report = validate_dataset(as_records([row(extra_field="x")]))
    assert report.ok
    assert any(i.field == "extra_field" for i in report.warnings)


def test_answer_aliases_must_be_a_list_of_non_empty_strings():
    assert not validate_dataset(as_records([row(answer_aliases="Bakı")])).ok
    assert not validate_dataset(as_records([row(answer_aliases=["Bakı", ""])])).ok
    assert validate_dataset(as_records([row(answer_aliases=["Bakıda"])])).ok


def test_malformed_json_line_is_reported_not_raised():
    # Bir korlanmış sətir bütün faylın yoxlanışını dayandırmamalıdır.
    decode_error = json.JSONDecodeError("Expecting value", "{bad", 0)
    report = validate_dataset([(1, decode_error), (2, VALID_ROW)])
    assert not report.ok
    assert "JSON parse" in messages(report)
    assert report.n_records == 2


def test_non_object_line_is_an_error():
    report = validate_dataset([(1, ["not", "an", "object"])])
    assert not report.ok


# --------------------------------------------------------------------------
# Fayl səviyyəsində yoxlamalar
# --------------------------------------------------------------------------


def test_duplicate_id_is_an_error():
    report = validate_dataset(as_records([VALID_ROW, row(question_az="Başqa sual?")]))
    assert any(i.field == "id" and "təkrar" in i.message for i in report.errors)


def test_unique_ids_pass():
    second = row(id="az-002", question_az="Gəncə hansı bölgədədir?")
    assert validate_dataset(as_records([VALID_ROW, second])).ok


def test_duplicate_question_is_a_warning():
    # Fərqli ID, eyni sual — datasetdə çəkini ikiqat artırır.
    twin = row(id="az-002")
    report = validate_dataset(as_records([VALID_ROW, twin]))
    assert report.ok
    assert any(i.field == "question_az" for i in report.warnings)


def test_duplicate_question_detection_ignores_case_and_punctuation():
    twin = row(id="az-002", question_az="AZƏRBAYCANIN PAYTAXTI HANSI ŞƏHƏRDİR?!")
    report = validate_dataset(as_records([VALID_ROW, twin]))
    assert any(i.field == "question_az" for i in report.warnings)


# --------------------------------------------------------------------------
# Keyfiyyət xəbərdarlıqları
# --------------------------------------------------------------------------


def test_untranslated_question_is_flagged():
    text = "What is the capital of Azerbaijan?"
    report = validate_dataset(as_records([row(question_az=text, question_en=text)]))
    assert "tərcümə olunmayıb" in messages(report)


def test_latinised_question_is_flagged():
    report = validate_dataset(
        as_records([row(question_az="Azerbaycan Respublikasinin paytaxti hansi seherdir?")])
    )
    assert "diakritiklər itib" in messages(report)


@pytest.mark.parametrize(
    "question",
    [
        "Qurban Qurbanov harada anadan olub?",   # düzgün AZ, xüsusi hərf yoxdur
        "Mariya Stadnik harada anadan olub?",
        "Kim yazdi bu romani?",
    ],
)
def test_correct_azerbaijani_without_special_letters_is_not_flagged(question):
    # "Xüsusi hərf yoxdursa xəbərdarlıq ver" qaydası bu cümlələri yandırırdı.
    # Yalançı siqnal istifadəçini xəbərdarlıqlara etinasız olmağa öyrədir.
    report = validate_dataset(as_records([row(question_az=question)]))
    assert "diakritiklər itib" not in messages(report)


def test_truncated_question_is_flagged():
    report = validate_dataset(as_records([row(question_az="Bakı böyük şəhər")]))
    assert "yarımçıq" in messages(report)


@pytest.mark.parametrize(
    "question",
    [
        "Fransanın paytaxtı hansı şəhərdir?",
        "Fransanın paytaxtını yaz.",       # əmr formalı tapşırıq
        "Diqqət! Cavabı yaz.",
    ],
)
def test_imperative_prompts_are_not_flagged(question):
    # Datasetdə əmr formalı variantlar var; sual işarəsi tələb etsək,
    # onların hamısı yalançı xəbərdarlıq verərdi.
    report = validate_dataset(as_records([row(question_az=question)]))
    assert "yarımçıq" not in messages(report)


def test_answer_leaking_into_question_is_flagged():
    leaky = row(
        question_az="Bakı Azərbaycanın paytaxtıdırmı?",
        answer="Bakı",
    )
    assert "sızması" in messages(validate_dataset(as_records([leaky])))


def test_multiword_answer_leaking_into_question_is_flagged():
    leaky = row(
        question_az="Xəzər dənizi hansı ölkələri əhatə edir?",
        answer="Xəzər dənizi",
    )
    assert "sızması" in messages(validate_dataset(as_records([leaky])))


@pytest.mark.parametrize(
    ("question", "answer"),
    [
        ("hidrogen elementinin kimyəvi simvolu nədir?", "H"),
        ("oksigen elementinin kimyəvi simvolu nədir?", "O"),
        ("alüminium elementinin kimyəvi simvolu nədir?", "Al"),
    ],
)
def test_short_answers_are_not_false_flagged_as_leakage(question, answer):
    # Alt-sətir yoxlaması "H" cavabını "hidrogen" sualının içində tapırdı və
    # 72 sətirlik yığımda 7 yalançı xəbərdarlıq verirdi. Yoxlama token
    # səviyyəsində aparılmalıdır.
    report = validate_dataset(as_records([row(question_az=question, answer=answer)]))
    assert "sızması" not in messages(report)


def test_unverified_row_is_flagged():
    report = validate_dataset(as_records([row(verified_by="llm-draft")]))
    assert report.ok  # xəta deyil — sadəcə yekun datasetə keçmir
    assert "əl yoxlamasından keçməyib" in messages(report)


# --------------------------------------------------------------------------
# G/Ç dövrü
# --------------------------------------------------------------------------


def test_write_then_load_roundtrip_preserves_az_characters(tmp_path):
    path = tmp_path / "out.jsonl"
    write_jsonl(path, [VALID_ROW])
    loaded = load_jsonl(path)
    assert loaded == [(1, VALID_ROW)]
    assert "ə" in path.read_text(encoding="utf-8")  # ensure_ascii=False


def test_load_jsonl_skips_blank_lines(tmp_path):
    path = tmp_path / "in.jsonl"
    path.write_text(
        json.dumps(VALID_ROW, ensure_ascii=False) + "\n\n  \n", encoding="utf-8"
    )
    assert len(load_jsonl(path)) == 1


def test_load_jsonl_keeps_original_line_numbers(tmp_path):
    path = tmp_path / "in.jsonl"
    path.write_text(
        "\n\n" + json.dumps(VALID_ROW, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    assert load_jsonl(path)[0][0] == 3


# --------------------------------------------------------------------------
# build — keyfiyyət qapısı
# --------------------------------------------------------------------------


def test_build_keeps_only_human_verified_rows(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    write_jsonl(
        raw / "pilot.jsonl",
        [
            VALID_ROW,
            row(id="az-002", question_az="Gəncə harada yerləşir?", verified_by="llm-draft"),
            row(id="az-003", question_az="Şəki hansı bölgədədir?", verified_by="pending"),
        ],
    )

    out = tmp_path / "az_eval_v0.jsonl"
    accepted, report = build_dataset(raw, out)

    assert report.ok
    assert [r["id"] for r in accepted] == ["az-001"]
    assert len(load_jsonl(out)) == 1


def test_build_refuses_to_write_when_errors_exist(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    write_jsonl(raw / "pilot.jsonl", [row(category="sports")])

    out = tmp_path / "az_eval_v0.jsonl"
    accepted, report = build_dataset(raw, out)

    assert not report.ok
    assert accepted == []
    assert not out.exists()  # korlanmış dataset diskə düşmür


def test_build_merges_multiple_raw_files_and_sorts_by_id(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    write_jsonl(raw / "b.jsonl", [row(id="az-003", question_az="Şəki haradadır?")])
    write_jsonl(raw / "a.jsonl", [row(id="az-002", question_az="Gəncə haradadır?")])

    accepted, report = build_dataset(raw, tmp_path / "out.jsonl")

    assert report.ok
    assert [r["id"] for r in accepted] == ["az-002", "az-003"]


def test_build_detects_duplicate_ids_across_files(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    write_jsonl(raw / "a.jsonl", [VALID_ROW])
    write_jsonl(raw / "b.jsonl", [row(question_az="Tamam başqa sual?")])

    accepted, report = build_dataset(raw, tmp_path / "out.jsonl")

    assert not report.ok
    assert "təkrar ID" in messages(report)
    assert accepted == []


def test_build_allow_unverified_flag_includes_drafts(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    write_jsonl(raw / "pilot.jsonl", [row(verified_by="llm-draft")])

    accepted, _ = build_dataset(raw, tmp_path / "out.jsonl", require_human=False)
    assert len(accepted) == 1


def test_build_on_empty_raw_dir_produces_empty_dataset(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    accepted, report = build_dataset(raw, tmp_path / "out.jsonl")
    assert report.ok
    assert accepted == []


# --------------------------------------------------------------------------
# Statistika
# --------------------------------------------------------------------------


def test_dataset_stats_counts_categories_and_coverage():
    records = [
        VALID_ROW,
        row(id="az-002", category="history"),
        row(id="az-003", category="history", question_az="Diakritiksiz sual?"),
    ]
    stats = dataset_stats(records)

    assert stats["n"] == 3
    assert stats["by_category"] == {"geography": 1, "history": 2}
    assert stats["by_verified_by"] == {"human": 3}
    assert stats["by_provenance"] == {"manual": 3}
    assert stats["with_aliases"] == 3
    assert stats["rows_with_az_chars"] == 2  # "Diakritiksiz sual?" sayılmır


def test_dataset_stats_handles_empty_dataset():
    stats = dataset_stats([])
    assert stats["n"] == 0
    assert stats["answer_words_mean"] == 0
    assert stats["answer_words_max"] == 0
    assert stats["majority_baseline"] == 0.0


def test_majority_baseline_exposes_answer_skew():
    # Wikidata şablonlaşdırmasının əsas tələsi: cavabların çoxu eyni dəyər olur.
    # Belə datasetdə heç nə bilməyən model 80% alır — `stats` bunu göstərməlidir.
    skewed = [row(id=f"az-{i:03d}", answer="Bakı") for i in range(1, 9)]
    skewed += [row(id="az-009", answer="Gəncə"), row(id="az-010", answer="Şəki")]

    stats = dataset_stats(skewed)
    assert stats["majority_baseline"] == 80.0
    assert stats["most_common_answer"] == "bakı"
    assert stats["distinct_answers"] == 3


def test_majority_baseline_is_low_for_a_balanced_dataset():
    balanced = [
        row(id=f"az-{i:03d}", answer=answer)
        for i, answer in enumerate(
            ["Bakı", "Gəncə", "Şəki", "Quba", "Lənkəran"], start=1
        )
    ]
    assert dataset_stats(balanced)["majority_baseline"] == 20.0


# --------------------------------------------------------------------------
# Alias doldurma
# --------------------------------------------------------------------------


def test_fill_aliases_populates_empty_field():
    updated, filled = fill_aliases([row(answer="Bakı", answer_aliases=[])])
    assert filled == 1
    assert "Bakıda" in updated[0]["answer_aliases"]


def test_fill_aliases_preserves_manual_entries():
    manual = row(answer="Bakı", answer_aliases=["Bakı şəhəri"])
    updated, _ = fill_aliases([manual], overwrite=True)
    assert "Bakı şəhəri" in updated[0]["answer_aliases"]  # əl işi itmir
    assert "Bakıda" in updated[0]["answer_aliases"]       # avtomatik əlavə olunur


def test_fill_aliases_skips_rows_that_already_have_them():
    _, filled = fill_aliases([row(answer="Bakı", answer_aliases=["Bakıda"])])
    assert filled == 0


def test_fill_aliases_does_not_mutate_input():
    original = row(answer="Bakı", answer_aliases=[])
    fill_aliases([original])
    assert original["answer_aliases"] == []


# --------------------------------------------------------------------------
# Etalonların bərabərləşdirilməsi
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("answer_az", "answer_en", "expected"),
    [
        ("fransız dili", "French", ["fransız", "dili"]),
        ("Meksika pesosu", "peso", ["Meksika", "pesosu"]),
        ("Yapon yeni", "yen", ["Yapon", "yeni"]),
    ],
)
def test_equivalence_aliases_when_az_gold_is_longer(answer_az, answer_en, expected):
    """Wikidata etiket konvensiyası AZ tərəfə əlavə söz yükləyir.

    Düzəliş olmasa, "fransız" cavabı — faktiki olaraq doğru — sıfır alır,
    ingilis ekvivalenti "French" isə bal alır; fərqin bir hissəsi dildən yox,
    etiket konvensiyasından gələr.
    """
    assert equivalence_aliases(answer_az, answer_en) == expected


@pytest.mark.parametrize(
    ("answer_az", "answer_en"),
    [
        ("Paris", "Paris"),                    # bərabər uzunluq
        ("Bakı", "Baku"),
        ("ABŞ dolları", "United States dollar"),  # AZ daha qısadır
        ("Au", "Au"),
    ],
)
def test_no_equivalence_aliases_when_golds_already_match(answer_az, answer_en):
    assert equivalence_aliases(answer_az, answer_en) == []


def test_fill_aliases_adds_equivalence_forms_and_inflects_them():
    row = {"answer": "fransız dili", "answer_en": "French", "answer_aliases": []}
    updated, _ = fill_aliases([row])
    aliases = updated[0]["answer_aliases"]
    assert "fransız" in aliases          # EN etalonun ekvivalenti
    assert "fransız dilində" in aliases  # tam formanın hallanması


# --------------------------------------------------------------------------
# Few-shot çirklənməsi
# --------------------------------------------------------------------------


def test_prompt_example_answers_match_run_eval():
    """Qapı `run_eval`-dakı promptla sinxron qalmalıdır.

    İki modul bir-birini import edə bilmir (dövrə yaranır: `run_eval` artıq
    `build_dataset.load_jsonl`-i çağırır), ona görə nümunə cavabları iki yerdə
    yazılıb. Bu test onları bir-birinə bağlayır: prompt dəyişsə və qapı
    yenilənməsə, test düşür.
    """
    import re

    from src.build_dataset import PROMPT_EXAMPLE_ANSWERS
    from src.metrics import STRICT, normalize
    from src.run_eval import PROMPT_STYLES

    found: set[str] = set()
    for templates in PROMPT_STYLES.values():
        for text in templates.values():
            for answer in re.findall(r"(?:Cavab|Answer):\s*(\S+)", text):
                if "{" in answer:  # `{question}` yer tutucusu deyil, cavab deyil
                    continue
                found.add(normalize(answer, STRICT))

    assert found, "promptda nümunə cavabı tapılmadı — regex köhnəlib?"
    assert found <= PROMPT_EXAMPLE_ANSWERS, (
        f"promptda qapıda olmayan nümunə cavabı var: {found - PROMPT_EXAMPLE_ANSWERS}"
    )


def test_few_shot_answer_is_rejected():
    """Promptdakı cavabı təkrarlayan sətir datasetə buraxılmamalıdır.

    Məhz bu sətir v1-də yayınıb (`az-546`): sual sözlə fərqlidir, fakt eynidir.
    """
    report = validate_dataset(as_records([row(
        answer="H2O",
        answer_en="H2O",
        question_az="Suyun kimyəvi formulu nədir?",
        question_en="What is the chemical formula of water?",
        category="science",
    )]))

    assert "few-shot" in messages(report)
    assert any(i.severity == "error" for i in report.issues)


def test_unrelated_answer_is_not_rejected():
    """Qapı dar olmalıdır: yalnız nümunə cavabları bloklanır."""
    report = validate_dataset(as_records([row()]))
    assert "few-shot" not in messages(report)


def test_rejected_row_with_few_shot_answer_is_not_an_error():
    """Rədd edilmiş sətir qapını tetikləməməlidir.

    Layihə rədd edilənləri qəsdən saxlayır (qəbul faizi auditə açıq qalsın
    deyə). Onlara xəta versək, `build` həmişəlik bloklanardı: sətir faylda
    qalır, amma datasetə onsuz da düşmür.
    """
    report = validate_dataset(as_records([row(
        answer="H2O", answer_en="H2O", category="science",
        verified_by="rejected",
    )]))

    assert not [
        i for i in report.issues if i.severity == "error" and "few-shot" in i.message
    ]


def test_external_verification_does_not_enter_the_dataset():
    """`external` KƏNAR dəstin müəllifləri yoxlayıb deməkdir, biz yox.

    Bu sətirlər yekun datasetə KEÇMƏMƏLİDİR. Keçsəydi, "hər sətir bizim
    annotatorumuz tərəfindən yoxlanılıb" iddiası yalan olardı.

    Vəziyyət `pending`-dən ayrılmalıdır, çünki `pending` "heç kim baxmayıb"
    deməkdir və kənar yoxlamanı gizlədir.
    """
    from src.build_dataset import VERIFICATION_STATES

    assert "external" in VERIFICATION_STATES
    assert "external" != "human"


# --------------------------------------------------------------------------
# DROPPED_FIELDS: xam faylda qəbul edilir, hazır dəstə yazılmır
# --------------------------------------------------------------------------


def test_difficulty_is_accepted_in_raw_but_not_emitted(tmp_path):
    """`difficulty` şablon sabitidir; dəstə çıxsa, sual-sual mühakimə kimi oxunar."""
    from src.build_dataset import DROPPED_FIELDS, OPTIONAL_FIELDS, build_dataset

    assert "difficulty" in DROPPED_FIELDS
    assert "difficulty" in OPTIONAL_FIELDS, "xam fayl hələ də qəbul edilməlidir"

    raw = tmp_path / "raw"
    raw.mkdir()
    row = {
        "id": "az-001",
        "question_az": "Fransanın paytaxtı?",
        "question_en": "Capital of France?",
        "answer": "Paris",
        "answer_en": "Paris",
        "category": "world",
        "source": "https://example.org",
        "provenance": "manual",
        "verified_by": "human",
        "difficulty": "hard",
    }
    (raw / "a.jsonl").write_text(
        json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    out = tmp_path / "built.jsonl"
    accepted, report = build_dataset(raw, out)
    assert report.ok
    assert len(accepted) == 1
    assert "difficulty" not in accepted[0]
    assert "difficulty" not in json.loads(out.read_text(encoding="utf-8"))
    assert accepted[0]["answer"] == "Paris", "başqa sahələr toxunulmamalıdır"


def test_shipped_dataset_carries_no_difficulty():
    """Regressiya: qapı istehsal faylında da qüvvədə olmalıdır."""
    from pathlib import Path

    from src.build_dataset import load_jsonl

    rows = [r for _, r in load_jsonl(Path("data/az_eval_v0.jsonl")) if isinstance(r, dict)]
    assert rows, "dataset boşdur"
    assert not any("difficulty" in r for r in rows)
