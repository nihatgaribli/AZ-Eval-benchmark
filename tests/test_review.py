"""review.py üçün testlər — vəziyyət idarəsi və diskə yazma."""

from __future__ import annotations

import json
import threading

import pytest

from src.build_dataset import write_jsonl
from src.review import ReviewState

ROW = {
    "id": "az-001",
    "question_az": "Fransa ölkəsinin paytaxtı hansı şəhərdir?",
    "question_en": "What is the capital city of France?",
    "answer": "Paris",
    "answer_en": "Paris",
    "answer_aliases": ["Parisdə"],
    "category": "geography",
    "source": "https://www.wikidata.org/wiki/Q142",
    "difficulty": "easy",
    "provenance": "wikidata-template",
    "verified_by": "pending",
    "notes": "template=country_capital",
}


@pytest.fixture
def state(tmp_path):
    path = tmp_path / "draft.jsonl"
    write_jsonl(path, [ROW, {**ROW, "id": "az-002", "answer": "Bakı"}])
    return ReviewState(path)


def test_loads_all_records(state):
    assert len(state.records) == 2


def test_snapshot_carries_index_and_warnings(state):
    snapshot = state.snapshot()
    assert [item["index"] for item in snapshot["items"]] == [0, 1]
    assert all("warnings" in item for item in snapshot["items"])


def test_approval_is_written_to_disk_immediately(state):
    # Yarımçıq qalan yoxlama işi itməməlidir — hər qərar dərhal yazılır.
    state.update(0, {**ROW, "verified_by": "human"})

    reloaded = [json.loads(line) for line in state.path.read_text(encoding="utf-8").splitlines()]
    assert reloaded[0]["verified_by"] == "human"
    assert reloaded[1]["verified_by"] == "pending"


def test_edits_are_persisted(state):
    state.update(0, {**ROW, "question_az": "Düzəldilmiş sual?"})
    assert "Düzəldilmiş sual?" in state.path.read_text(encoding="utf-8")


def test_azerbaijani_characters_survive_the_round_trip(state):
    state.update(0, {**ROW, "answer": "Gəncə", "question_az": "Şəkidə nə var?"})
    text = state.path.read_text(encoding="utf-8")
    assert "Gəncə" in text and "Şəkidə" in text


def test_record_count_never_changes(state):
    state.update(0, {**ROW, "verified_by": "rejected"})
    lines = state.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2  # rədd edilən sətir SİLİNMİR


def test_rejected_rows_are_kept_for_the_acceptance_rate(state):
    # Qəbul faizi datasetin keyfiyyət göstəricisidir və məqalədə verilir.
    state.update(0, {**ROW, "verified_by": "rejected"})
    state.update(1, {**ROW, "id": "az-002", "verified_by": "human"})

    statuses = [r["verified_by"] for r in ReviewState(state.path).records]
    assert sorted(statuses) == ["human", "rejected"]


def test_out_of_range_index_raises(state):
    with pytest.raises(IndexError):
        state.update(99, ROW)


def test_warnings_hide_the_verified_by_notice(state):
    # Sətirlər `pending`-dir, amma yoxlama məhz bunu dəyişmək üçün açılıb —
    # hər sətirdə eyni xəbərdarlığı göstərmək siqnalı boğardı.
    warnings = state.warnings_by_index()
    assert not any("əl yoxlamasından" in w for group in warnings.values() for w in group)


def test_real_warnings_still_surface(tmp_path):
    path = tmp_path / "draft.jsonl"
    write_jsonl(path, [{**ROW, "question_az": "Durğu işarəsi olmayan cümlə"}])
    warnings = ReviewState(path).warnings_by_index()
    assert any("yarımçıq" in w for w in warnings[0])


def test_concurrent_updates_do_not_corrupt_the_file(tmp_path):
    # Brauzer paralel sorğu göndərə bilər; atomik yazı faylı qorumalıdır.
    path = tmp_path / "draft.jsonl"
    write_jsonl(path, [{**ROW, "id": f"az-{i:03d}"} for i in range(1, 21)])
    state = ReviewState(path)

    def approve(index: int) -> None:
        state.update(index, {**state.records[index], "verified_by": "human"})

    threads = [threading.Thread(target=approve, args=(i,)) for i in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 20
    assert all(json.loads(line)["verified_by"] == "human" for line in lines)
