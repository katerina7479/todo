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


_SORT_SENTINEL = "\xff"  # sorts after all printable strings


def sort_todos(todos: list[dict], sort_by: str) -> list[dict]:
    """Return a new list sorted by *sort_by* field. Missing values sort last."""
    if sort_by == "title":
        key = lambda t: t.get("title", "").lower()
    elif sort_by == "created_at":
        key = lambda t: t.get("created_at") or _SORT_SENTINEL
    else:
        key = lambda t: t.get(sort_by) or _SORT_SENTINEL
    return sorted(todos, key=key)


def group_todos(todos: list[dict], group_by: str) -> list[tuple[str, list[dict]]]:
    """Return [(label, [todos])] groups, sorted by label. Missing values → '(none)'.

    For group_by='tag' each todo appears under every tag it carries; untagged
    todos appear under '(no tag)'.
    """
    buckets: dict[str, list[dict]] = {}

    if group_by == "tag":
        for t in todos:
            tags = t.get("tags", [])
            if not tags:
                buckets.setdefault("(no tag)", []).append(t)
            else:
                for tag in tags:
                    buckets.setdefault(tag, []).append(t)
    else:
        for t in todos:
            val = t.get(group_by)
            label = str(val) if val is not None else "(none)"
            buckets.setdefault(label, []).append(t)

    return sorted(buckets.items(), key=lambda kv: kv[0])


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
    raise ValueError(f"Todo #{todo_id} not found.")


def delete_todo(todo_id: int) -> dict:
    data = _load_raw()
    for i, todo in enumerate(data["todos"]):
        if todo["id"] == todo_id:
            removed = data["todos"].pop(i)
            _save_raw(data)
            return removed
    raise ValueError(f"Todo #{todo_id} not found.")
