import json
import pytest
from pathlib import Path

from config import Config, DEFAULT_STORAGE_FILE


def test_config_default_storage_path():
    config = Config()
    assert config.storage_path == DEFAULT_STORAGE_FILE


def test_config_custom_storage_path(tmp_path):
    custom = tmp_path / "custom" / "todos.json"
    config = Config(storage_path=custom)
    assert config.storage_path == custom


def test_config_load_missing_file(tmp_path):
    config = Config.load(tmp_path / "nonexistent.json")
    assert config.storage_path == DEFAULT_STORAGE_FILE


def test_config_save_and_load(tmp_path):
    config_file = tmp_path / "config.json"
    storage = tmp_path / "data" / "todos.json"
    config = Config(storage_path=storage)
    config.save(config_file)

    loaded = Config.load(config_file)
    assert loaded.storage_path == storage


def test_config_save_creates_parent_dirs(tmp_path):
    config_file = tmp_path / "nested" / "dir" / "config.json"
    config = Config()
    config.save(config_file)
    assert config_file.exists()


def test_config_save_writes_valid_json(tmp_path):
    config_file = tmp_path / "config.json"
    storage = tmp_path / "todos.json"
    config = Config(storage_path=storage)
    config.save(config_file)

    with open(config_file) as f:
        data = json.load(f)
    assert "storage_path" in data
    assert data["storage_path"] == str(storage)


def test_config_load_uses_default_when_key_missing(tmp_path):
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump({}, f)

    config = Config.load(config_file)
    assert config.storage_path == DEFAULT_STORAGE_FILE


def test_config_ensure_storage_dir(tmp_path):
    storage = tmp_path / "subdir" / "todos.json"
    config = Config(storage_path=storage)
    config.ensure_storage_dir()
    assert storage.parent.exists()
