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


def add_todo(title: str, tags: Optional[list[str]] = None) -> dict:
    data = _load_raw()
    todo = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tags": tags or [],
    }
    data["todos"].append(todo)
    data["next_id"] += 1
    _save_raw(data)
    return todo


def get_todo(todo_id: int) -> Optional[dict]:
    for todo in load_todos():
        if todo["id"] == todo_id:
            return todo
    return None


def list_todos(show_done: bool = False, tag: Optional[str] = None) -> list[dict]:
    todos = load_todos()
    if not show_done:
        todos = [t for t in todos if not t["done"]]
    if tag:
        todos = [t for t in todos if tag in t.get("tags", [])]
    return todos


def search_todos(query: str) -> list[dict]:
    q = query.lower()
    results = []
    for todo in load_todos():
        if q in todo["title"].lower():
            results.append(todo)
            continue
        if any(q in tag.lower() for tag in todo.get("tags", [])):
            results.append(todo)
    return results


def mark_done(todo_id: int) -> dict:
    data = _load_raw()
    for todo in data["todos"]:
        if todo["id"] == todo_id:
            todo["done"] = True
            _save_raw(data)
            return todo
    raise KeyError(f"Todo #{todo_id} not found.")


def delete_todo(todo_id: int) -> dict:
    data = _load_raw()
    for i, todo in enumerate(data["todos"]):
        if todo["id"] == todo_id:
            removed = data["todos"].pop(i)
            _save_raw(data)
            return removed
    raise KeyError(f"Todo #{todo_id} not found.")
