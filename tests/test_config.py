import pytest
from pathlib import Path

from config import get_storage_path


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    monkeypatch.delenv("TODO_FILE", raising=False)


def test_default_path_filename():
    assert get_storage_path().name == "todos.json"


def test_default_path_is_under_home():
    path = get_storage_path()
    assert str(Path.home()) in str(path)


def test_default_path_creates_parent_dir():
    path = get_storage_path()
    assert path.parent.exists()


def test_env_override_returns_custom_path(monkeypatch, tmp_path):
    custom = tmp_path / "my_todos.json"
    monkeypatch.setenv("TODO_FILE", str(custom))
    assert get_storage_path() == custom


def test_env_override_does_not_create_dirs(monkeypatch, tmp_path):
    nested = tmp_path / "a" / "b" / "todos.json"
    monkeypatch.setenv("TODO_FILE", str(nested))
    get_storage_path()
    assert not nested.parent.exists()


def test_env_override_returns_path_object(monkeypatch, tmp_path):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))
    result = get_storage_path()
    assert isinstance(result, Path)
