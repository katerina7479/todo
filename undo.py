"""Single-level undo journal for destructive todo operations."""

import json
from typing import Optional

from config import get_storage_path


def _journal_path():
    return get_storage_path().parent / ".todo_undo.json"


def record(action: str, todo: dict) -> None:
    """Overwrite the journal with the pre-action snapshot."""
    with _journal_path().open("w") as f:
        json.dump({"action": action, "todo": todo}, f, indent=2)


def load() -> Optional[dict]:
    path = _journal_path()
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


def clear() -> None:
    path = _journal_path()
    if path.exists():
        path.unlink()
