"""Core todo CRUD operations backed by a JSON file."""

import calendar
import json
from datetime import date, datetime, timedelta, timezone
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
    due_date: Optional[str] = None,
    repeat: Optional[str] = None,
) -> dict:
    data = _load_raw()
    todo: dict = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tags": tags or [],
    }
    if due_date is not None:
        todo["due_date"] = due_date
    if repeat is not None:
        todo["repeat"] = repeat
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


def _advance_date(base: date, repeat: str) -> Optional[date]:
    """Return the next date given a repeat schedule, or None if schedule is invalid."""
    if repeat == "daily":
        return base + timedelta(days=1)
    if repeat == "weekly":
        return base + timedelta(weeks=1)
    if repeat == "monthly":
        month = base.month + 1
        year = base.year
        if month > 12:
            month = 1
            year += 1
        day = min(base.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    if repeat.startswith("custom:"):
        try:
            days = int(repeat[7:])
            return base + timedelta(days=days)
        except ValueError:
            return None
    return None


def _next_due_date(todo: dict) -> Optional[str]:
    """Calculate the next due date for a recurring todo."""
    repeat = todo.get("repeat")
    if not repeat:
        return None
    raw = todo.get("due_date")
    if raw:
        try:
            base = datetime.fromisoformat(raw).date()
        except ValueError:
            base = date.today()
    else:
        base = date.today()
    next_date = _advance_date(base, repeat)
    return next_date.isoformat() if next_date else None


def mark_done(todo_id: int) -> tuple[dict, Optional[dict]]:
    """Mark a todo done.

    Returns (completed_todo, next_occurrence) where next_occurrence is a newly
    created todo when the completed item has a repeat schedule, else None.
    """
    data = _load_raw()
    for todo in data["todos"]:
        if todo["id"] == todo_id:
            todo["done"] = True
            next_occurrence: Optional[dict] = None
            if todo.get("repeat"):
                next_due = _next_due_date(todo)
                next_occurrence = {
                    "id": data["next_id"],
                    "title": todo["title"],
                    "done": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "tags": list(todo.get("tags", [])),
                    "repeat": todo["repeat"],
                }
                if next_due is not None:
                    next_occurrence["due_date"] = next_due
                if todo.get("priority"):
                    next_occurrence["priority"] = todo["priority"]
                data["todos"].append(next_occurrence)
                data["next_id"] += 1
            _save_raw(data)
            return todo, next_occurrence
    raise ValueError(f"Todo #{todo_id} not found.")


def delete_todo(todo_id: int) -> dict:
    data = _load_raw()
    for i, todo in enumerate(data["todos"]):
        if todo["id"] == todo_id:
            removed = data["todos"].pop(i)
            _save_raw(data)
            return removed
    raise ValueError(f"Todo #{todo_id} not found.")
