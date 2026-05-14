"""Core todo CRUD operations backed by a JSON file."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import get_archive_path, get_storage_path


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


def _load_archive() -> dict:
    path = get_archive_path()
    if not path.exists():
        return {"todos": []}
    with path.open() as f:
        return json.load(f)


def _save_archive(data: dict) -> None:
    path = get_archive_path()
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


def load_archived() -> list[dict]:
    return _load_archive()["todos"]


def archive_done() -> int:
    """Move all done todos from the active store to the archive. Returns count moved."""
    data = _load_raw()
    done = [t for t in data["todos"] if t["done"]]
    if not done:
        return 0
    for t in done:
        t["archived"] = True
    archive = _load_archive()
    archive["todos"].extend(done)
    _save_archive(archive)
    data["todos"] = [t for t in data["todos"] if not t["done"]]
    _save_raw(data)
    return len(done)


def list_todos(
    show_done: bool = False,
    tag: Optional[str] = None,
    include_archived: bool = False,
) -> list[dict]:
    todos = load_todos()
    if not show_done:
        todos = [t for t in todos if not t["done"]]
    if tag:
        todos = [t for t in todos if tag in t.get("tags", [])]
    if include_archived:
        archived = load_archived()
        if tag:
            archived = [t for t in archived if tag in t.get("tags", [])]
        todos = todos + archived
    return todos


def search_todos(query: str, include_archived: bool = False) -> list[dict]:
    q = query.lower()
    sources = load_todos()
    if include_archived:
        sources = sources + load_archived()
    results = []
    for todo in sources:
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


def mark_done_batch(ids: list[int]) -> tuple[list[dict], list[int]]:
    """Mark multiple todos done in a single write.

    Returns (completed, missing_ids) where missing_ids are IDs not found.
    """
    data = _load_raw()
    remaining = set(ids)
    completed = []
    for todo in data["todos"]:
        if todo["id"] in remaining:
            todo["done"] = True
            completed.append(todo)
            remaining.discard(todo["id"])
    if completed:
        _save_raw(data)
    return completed, sorted(remaining)


def mark_done_overdue() -> list[dict]:
    """Mark all pending todos whose due_date is in the past as done.

    Returns the list of todos that were marked done.
    """
    now = datetime.now(timezone.utc)
    data = _load_raw()
    completed = []
    for todo in data["todos"]:
        if todo.get("done"):
            continue
        raw_due = todo.get("due_date")
        if not raw_due:
            continue
        try:
            due_dt = datetime.fromisoformat(raw_due)
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if due_dt < now:
            todo["done"] = True
            completed.append(todo)
    if completed:
        _save_raw(data)
    return completed


def delete_todo(todo_id: int) -> dict:
    data = _load_raw()
    for i, todo in enumerate(data["todos"]):
        if todo["id"] == todo_id:
            removed = data["todos"].pop(i)
            _save_raw(data)
            return removed
    raise ValueError(f"Todo #{todo_id} not found.")


def delete_batch(ids: list[int]) -> tuple[list[dict], list[int]]:
    """Delete multiple todos in a single write.

    Returns (deleted, missing_ids) where missing_ids are IDs not found.
    """
    data = _load_raw()
    id_set = set(ids)
    deleted = []
    kept = []
    for todo in data["todos"]:
        if todo["id"] in id_set:
            deleted.append(todo)
            id_set.discard(todo["id"])
        else:
            kept.append(todo)
    if deleted:
        data["todos"] = kept
        _save_raw(data)
    return deleted, sorted(id_set)


def delete_completed() -> list[dict]:
    """Delete all completed todos. Returns the list of deleted todos."""
    data = _load_raw()
    deleted = [t for t in data["todos"] if t["done"]]
    if deleted:
        data["todos"] = [t for t in data["todos"] if not t["done"]]
        _save_raw(data)
    return deleted
