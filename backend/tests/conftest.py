import pytest

from app import config


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point every test at an isolated temporary database."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
