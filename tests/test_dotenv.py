"""`.env` oxunması üçün testlər.

NİYƏ LAZIMDIR. Açar `setx` ilə qurulanda yalnız YENİ proseslər onu görür;
artıq işləyən terminal köhnə mühiti saxlayır. Uzun sessiyada bu, "açarı
qurdum, amma proqram görmür" vəziyyəti yaradır və səbəbi aydın olmur.
"""

from __future__ import annotations

from src.backends_api import load_dotenv, read_api_key


def test_reads_simple_pairs(tmp_path):
    path = tmp_path / ".env"
    path.write_text("OPENROUTER_API_KEY=sk-or-v1-test\n", encoding="utf-8")
    assert load_dotenv(path)["OPENROUTER_API_KEY"] == "sk-or-v1-test"


def test_quotes_are_stripped(tmp_path):
    path = tmp_path / ".env"
    path.write_text('K="sk-quoted"\nJ=\'sk-single\'\n', encoding="utf-8")
    values = load_dotenv(path)
    assert values["K"] == "sk-quoted"
    assert values["J"] == "sk-single"


def test_comments_and_blank_lines_are_ignored(tmp_path):
    path = tmp_path / ".env"
    path.write_text("# şərh\n\nK=v\n  \n", encoding="utf-8")
    assert load_dotenv(path) == {"K": "v"}


def test_missing_file_is_not_an_error(tmp_path):
    assert load_dotenv(tmp_path / "yoxdur.env") == {}


def test_environment_wins_over_the_file(tmp_path, monkeypatch):
    """Mühitdə dəyişən varsa, fayl ona TOXUNMAMALIDIR.

    Əks halda köhnə fayl aktiv mühiti səssizcə üstələyərdi və bu, izlənməsi
    ən çətin səhv tipidir: proqram işləyir, amma yanlış açarla.
    """
    path = tmp_path / ".env"
    path.write_text("K=fayldan\n", encoding="utf-8")
    monkeypatch.setenv("K", "mühitdən")
    assert read_api_key("K", path) == "mühitdən"


def test_file_is_used_when_the_environment_is_empty(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("K=fayldan\n", encoding="utf-8")
    monkeypatch.delenv("K", raising=False)
    assert read_api_key("K", path) == "fayldan"


def test_absent_everywhere_returns_none(tmp_path, monkeypatch):
    monkeypatch.delenv("YOXDUR_XYZ", raising=False)
    assert read_api_key("YOXDUR_XYZ", tmp_path / ".env") is None
