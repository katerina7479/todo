"""Core todo CRUD operations backed by a JSON file."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import get_storage_path


def _load_raw() -> dict:
    path = get_storage_path()
    if not path.exists():
        return {"next_id": 1, "todos": []}
    with path.open() as f:
        return json.load(f)


def _save_raw(data: dict) -> None:
    path = get_storage_path()
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def load_todos() -> list[dict]:
    return _load_raw()["todos"]


def add_todo(title: str, due_date: Optional[str] = None) -> dict:
    data = _load_raw()
    todo = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if due_date is not None:
        todo["due_date"] = due_date
    data["todos"].append(todo)
    data["next_id"] += 1
    _save_raw(data)
    return todo


def get_todo(todo_id: int) -> Optional[dict]:
    for todo in load_todos():
        if todo["id"] == todo_id:
            return todo
    return None


def list_todos(show_done: bool = False) -> list[dict]:
    todos = load_todos()
    if not show_done:
        todos = [t for t in todos if not t["done"]]
    return todos


def mark_done(todo_id: int) -> dict:
    data = _load_raw()
    for todo in data["todos"]:
        if todo["id"] == todo_id:
            todo["done"] = True
            _save_raw(data)
            return todo
    raise ValueError(f"Todo #{todo_id} not found.")


def delete_todo(todo_id: int) -> dict:
    data = _load_raw()
    for i, todo in enumerate(data["todos"]):
        if todo["id"] == todo_id:
            removed = data["todos"].pop(i)
            _save_raw(data)
            return removed
    raise ValueError(f"Todo #{todo_id} not found.")


_SENTINEL = object()


def update_todo(
    todo_id: int,
    *,
    title: object = _SENTINEL,
    priority: object = _SENTINEL,
    due_date: object = _SENTINEL,
    tags: object = _SENTINEL,
) -> dict:
    """Partial update — only fields passed (not _SENTINEL) are changed."""
    data = _load_raw()
    for todo in data["todos"]:
        if todo["id"] == todo_id:
            if title is not _SENTINEL:
                todo["title"] = title
            if priority is not _SENTINEL:
                todo["priority"] = priority
            if due_date is not _SENTINEL:
                todo["due_date"] = due_date
            if tags is not _SENTINEL:
                todo["tags"] = tags
            _save_raw(data)
            return todo
    raise ValueError(f"Todo #{todo_id} not found.")
