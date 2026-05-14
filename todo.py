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


def add_todo(
    title: str,
    tags: Optional[list[str]] = None,
    parent_id: Optional[int] = None,
) -> dict:
    data = _load_raw()
    if parent_id is not None:
        if not any(t["id"] == parent_id for t in data["todos"]):
            raise KeyError(f"Parent todo #{parent_id} not found.")
    todo = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tags": tags or [],
        "parent_id": parent_id,
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


def _sort_hierarchically(todos: list[dict]) -> list[dict]:
    """Return todos with each parent immediately followed by its children."""
    by_parent: dict = {}
    for t in todos:
        pid = t.get("parent_id")
        by_parent.setdefault(pid, []).append(t)

    result: list[dict] = []

    def _collect(parent_id: Optional[int]) -> None:
        for t in by_parent.get(parent_id, []):
            result.append(t)
            _collect(t["id"])

    _collect(None)
    # Subtasks whose parent was filtered out appear at the end.
    seen_ids = {t["id"] for t in result}
    for t in todos:
        if t["id"] not in seen_ids:
            result.append(t)
    return result


def _collect_subtree_ids(todos: list[dict], root_id: int) -> set[int]:
    """Return ids of root_id and all its descendants."""
    ids = {root_id}
    changed = True
    while changed:
        changed = False
        for t in todos:
            if t.get("parent_id") in ids and t["id"] not in ids:
                ids.add(t["id"])
                changed = True
    return ids


def list_todos(show_done: bool = False, tag: Optional[str] = None) -> list[dict]:
    todos = load_todos()
    if not show_done:
        todos = [t for t in todos if not t["done"]]
    if tag:
        todos = [t for t in todos if tag in t.get("tags", [])]
    return _sort_hierarchically(todos)


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
    target = next((t for t in data["todos"] if t["id"] == todo_id), None)
    if target is None:
        raise KeyError(f"Todo #{todo_id} not found.")
    ids_to_mark = _collect_subtree_ids(data["todos"], todo_id)
    for todo in data["todos"]:
        if todo["id"] in ids_to_mark:
            todo["done"] = True
    _save_raw(data)
    return target


def delete_todo(todo_id: int) -> dict:
    data = _load_raw()
    for i, todo in enumerate(data["todos"]):
        if todo["id"] == todo_id:
            removed = data["todos"].pop(i)
            _save_raw(data)
            return removed
    raise KeyError(f"Todo #{todo_id} not found.")
