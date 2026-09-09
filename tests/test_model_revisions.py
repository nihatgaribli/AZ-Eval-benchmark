"""model_revisions.py üçün testlər."""

from __future__ import annotations

import pytest

from src.model_revisions import (
    build_report,
    cache_dir,
    current_ref,
    is_api_model,
    local_revisions,
    revision_of,
)


@pytest.mark.parametrize(
    "model,expected",
    [
        ("openai:openai/gpt-4o", True),
        ("google:gemini-3.5-flash", True),
        ("openai:qwen/qwen3-8b", True),
        ("Qwen/Qwen3-4B", False),
        ("issai/Qolda-AVL-5B", False),
        ("thelamapi/next-1b", False),
    ],
)
def test_api_models_are_recognised(model, expected):
    """`google:` da API-dir; yalnız `openai:` axtarmaq səhv idi."""
    assert is_api_model(model) is expected


def snapshot(tmp_path, model, *hashes, ref=None):
    d = cache_dir(model, tmp_path) / "snapshots"
    for h in hashes:
        (d / h).mkdir(parents=True)
    if ref is not None:
        refs = cache_dir(model, tmp_path) / "refs"
        refs.mkdir(parents=True, exist_ok=True)
        (refs / "main").write_text(ref, encoding="utf-8")
    return tmp_path


def test_single_snapshot_is_reported(tmp_path):
    snapshot(tmp_path, "org/model", "abc123")
    assert local_revisions("org/model", tmp_path) == ["abc123"]
    assert revision_of("org/model", tmp_path) == "abc123"
    assert "`abc123`" in build_report(["org/model"], tmp_path)


def test_missing_model_is_marked_not_invented(tmp_path):
    """Silinmiş modelə uydurma hash yazılmamalıdır."""
    report = build_report(["org/gone"], tmp_path)
    assert "qeyd edilməyib" in report
    assert revision_of("org/gone", tmp_path) is None


def test_ambiguous_snapshots_are_flagged(tmp_path):
    snapshot(tmp_path, "org/two", "aaa", "bbb", ref="bbb")
    assert revision_of("org/two", tmp_path) is None, "iki snapshot -> qəti cavab yoxdur"
    report = build_report(["org/two"], tmp_path)
    assert "birdən çox snapshot" in report
    assert "`aaa`" in report and "`bbb`" in report
    assert current_ref("org/two", tmp_path) == "bbb"


def test_api_model_is_not_reported_as_deleted(tmp_path):
    report = build_report(["openai:openai/gpt-4o"], tmp_path)
    assert "API ilə qaçırılıb" in report
    assert "qeyd edilməyib" not in report


def test_report_counts_missing(tmp_path):
    snapshot(tmp_path, "org/here", "abc")
    report = build_report(["org/here", "org/gone", "openai:x/y"], tmp_path)
    assert "**1**" in report, "yalnız silinmiş yerli model sayılmalıdır"
