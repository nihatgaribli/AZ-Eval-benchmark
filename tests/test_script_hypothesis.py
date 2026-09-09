"""script_hypothesis.py üçün testlər.

Diqqət mərkəzi iki şeydədir: 2x2-nin natamam qalmasının SƏSSİZ ötüşməməsi və
"bağlanan pay" hesabının genişlənən fərqdə də doğru işarə verməsi. İkisi də
nəticəni yanlış oxutmağa qadir səhvlərdir.
"""

from __future__ import annotations

import json

import pytest

from src.script_hypothesis import (
    BASE_MODEL,
    TUNED_MODEL,
    _CYRILLIC,
    Cell,
    gap_table,
    load_cells,
    script_counts_table,
)


def record(record_id, answer, category="geography"):
    return {
        "id": record_id,
        "question_az": f"{record_id} sualı?",
        "question_en": f"{record_id} question?",
        "answer": answer,
        "answer_en": answer,
        "answer_aliases": [],
        "category": category,
        "variant": "0",
        "source": "https://example.org",
        "provenance": "wikidata-template",
        "verified_by": "human",
    }


def write_run(directory, model, prompt_style, answers):
    suffix = "" if prompt_style == "default" else "__script"
    path = directory / f"{model.replace('/', '__')}__az{suffix}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record_id, text in answers.items():
            handle.write(
                json.dumps(
                    {
                        "id": record_id,
                        "model": model,
                        "language": "az",
                        "prompt_style": prompt_style,
                        "raw_response": text,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return path


@pytest.fixture
def dataset():
    return {r["id"]: r for r in (record("a-1", "Bakı"), record("a-2", "Gəncə"))}


def full_grid(directory, answers=None):
    answers = answers or {"a-1": "Bakı", "a-2": "Gəncə"}
    for model in (BASE_MODEL, TUNED_MODEL):
        for style in ("default", "script"):
            write_run(directory, model, style, answers)


def test_missing_cell_aborts(tmp_path, dataset):
    """Natamam 2x2 SƏSSİZ ötüşməməlidir.

    Üç xana ilə cədvəl qurulsaydı, "latın tələbinin təsiri" sətri bir model
    üçün ümumiyyətlə görünməzdi və oxucu bunu effektin olmaması kimi oxuyardı.
    """
    write_run(tmp_path, BASE_MODEL, "default", {"a-1": "Bakı"})
    write_run(tmp_path, TUNED_MODEL, "default", {"a-1": "Бакы"})
    with pytest.raises(SystemExit) as excinfo:
        load_cells(tmp_path, dataset)
    assert "script" in str(excinfo.value)


def test_only_common_ids_are_used(tmp_path, dataset):
    """Bir xanada çatışmayan sual BÜTÜN xanalardan çıxarılmalıdır."""
    full_grid(tmp_path)
    write_run(tmp_path, TUNED_MODEL, "script", {"a-1": "Bakı"})
    _, ids = load_cells(tmp_path, dataset)
    assert ids == ["a-1"]


def test_english_runs_are_ignored(tmp_path, dataset):
    """Sual azərbaycancadır; ingilis qaçışı təsadüfən xanaya düşməməlidir."""
    full_grid(tmp_path)
    path = tmp_path / "extra_en.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "a-1",
                "model": BASE_MODEL,
                "language": "en",
                "prompt_style": "default",
                "raw_response": "Baku",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    runs, ids = load_cells(tmp_path, dataset)
    assert len(ids) == 2
    assert all(run.key.language == "az" for run in runs.values())


def test_widening_gap_reports_negative_share(tmp_path, dataset):
    """Fərq genişlənəndə "bağlanan pay" MƏNFİ olmalıdır.

    Mütləq qiymət götürülsəydi, genişlənən fərq bağlanan fərq kimi görünərdi.
    """
    full_grid(tmp_path)
    # Baza hər ikisini düz bilir, Qolda isə yalnız şəkilçili formanı yazır:
    # STRICT-də fərq var, MORPH-da baza dəyişmir, Qolda isə qazanır.
    write_run(tmp_path, BASE_MODEL, "default", {"a-1": "Bakı", "a-2": "Gəncə"})
    write_run(tmp_path, TUNED_MODEL, "default", {"a-1": "Bakıda", "a-2": "səhv"})
    runs, ids = load_cells(tmp_path, dataset)
    table = gap_table(runs, dataset, ids, seed=0)
    assert "strict" in table and "translit" in table
    assert "Bağlanan pay" in table


def test_cyrillic_detection_covers_mixed_strings():
    """Qarışıq yazı kiril sayılmalıdır: sətir müqayisəsi onu da uğursuz sayır."""
    assert _CYRILLIC.search("Бакы")
    assert _CYRILLIC.search("1991 илы")
    assert not _CYRILLIC.search("Bakı")
    assert not _CYRILLIC.search("1991")


def test_script_counts_has_no_chain_column(tmp_path, dataset):
    """Zəncir sütunu OLMAMALIDIR: zəncir cavabı deyil, balı dəyişir."""
    full_grid(tmp_path)
    write_run(tmp_path, TUNED_MODEL, "default", {"a-1": "Бакы", "a-2": "Gəncə"})
    runs, ids = load_cells(tmp_path, dataset)
    table = script_counts_table(runs, ids)
    assert "Zəncir" not in table
    assert "strict" not in table
    # Qoldanın adi qaçışında bir kiril cavab var.
    line = next(
        row for row in table.splitlines() if TUNED_MODEL in row and "default" in row
    )
    assert "| 1" in line


def test_cells_are_hashable_keys():
    """Cell dondurulmuş olmalıdır, yoxsa lüğət açarı ola bilməz."""
    assert Cell(BASE_MODEL, "default") == Cell(BASE_MODEL, "default")
    assert len({Cell(BASE_MODEL, "default"), Cell(BASE_MODEL, "script")}) == 2
