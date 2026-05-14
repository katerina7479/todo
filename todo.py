"""Core todo CRUD operations backed by a JSON file."""

import json
from datetime import date, datetime, timedelta, timezone
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
            todo["completed_at"] = datetime.now(timezone.utc).isoformat()
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


def compute_stats() -> dict:
    """Compute productivity statistics over all active todos."""
    data = _load_raw()
    all_todos = data["todos"]

    total = len(all_todos)
    done_todos = [t for t in all_todos if t.get("done")]
    pending_todos = [t for t in all_todos if not t.get("done")]

    # Overdue: pending with a due_date in the past
    now = datetime.now(timezone.utc)
    overdue_count = 0
    for t in pending_todos:
        raw_due = t.get("due_date")
        if not raw_due:
            continue
        try:
            due_dt = datetime.fromisoformat(raw_due)
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)
            if due_dt < now:
                overdue_count += 1
        except ValueError:
            pass

    completion_rate = len(done_todos) / total * 100 if total > 0 else 0.0

    # Todos per tag (across all todos, done or not)
    tag_counts: dict[str, int] = {}
    for t in all_todos:
        for tag in t.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Average time to completion: created_at → completed_at
    completion_seconds: list[float] = []
    completion_dates: set[date] = set()
    for t in done_todos:
        created_raw = t.get("created_at")
        completed_raw = t.get("completed_at")
        if created_raw and completed_raw:
            try:
                created_dt = datetime.fromisoformat(created_raw)
                completed_dt = datetime.fromisoformat(completed_raw)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                if completed_dt.tzinfo is None:
                    completed_dt = completed_dt.replace(tzinfo=timezone.utc)
                completion_seconds.append((completed_dt - created_dt).total_seconds())
                completion_dates.add(completed_dt.astimezone().date())
            except ValueError:
                pass

    avg_seconds: Optional[float] = (
        sum(completion_seconds) / len(completion_seconds)
        if completion_seconds
        else None
    )

    # Streak: longest run of consecutive days ending today (or yesterday)
    streak = 0
    if completion_dates:
        today = date.today()
        start = today if today in completion_dates else today - timedelta(days=1)
        check = start
        while check in completion_dates:
            streak += 1
            check -= timedelta(days=1)

    return {
        "total": total,
        "completed": len(done_todos),
        "pending": len(pending_todos),
        "overdue": overdue_count,
        "completion_rate": completion_rate,
        "by_tag": tag_counts,
        "avg_completion_seconds": avg_seconds,
        "streak_days": streak,
    }
