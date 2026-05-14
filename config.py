"""Configuration and storage path management for the todo CLI."""

import os
from pathlib import Path


def get_storage_path() -> Path:
    """Return path to the todos JSON file, respecting TODO_FILE env override."""
    env_path = os.environ.get("TODO_FILE")
    if env_path:
        return Path(env_path)
    data_dir = Path.home() / ".local" / "share" / "todo-cli"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "todos.json"


def get_archive_path() -> Path:
    """Return path to the archive JSON file, respecting TODO_ARCHIVE_FILE env override."""
    env_path = os.environ.get("TODO_ARCHIVE_FILE")
    if env_path:
        return Path(env_path)
    data_dir = Path.home() / ".local" / "share" / "todo-cli"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "archive.json"
