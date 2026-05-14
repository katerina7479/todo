"""Terminal output formatting for todo items."""

from datetime import datetime, timezone
from typing import Optional


def _status_char(todo: dict) -> str:
    return "x" if todo["done"] else " "


def _created_label(todo: dict) -> str:
    try:
        dt = datetime.fromisoformat(todo["created_at"])
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except (KeyError, ValueError):
        return "unknown"


def _tags_label(todo: dict) -> str:
    tags = todo.get("tags", [])
    return f"  [{', '.join(tags)}]" if tags else ""


def format_todo(todo: dict) -> str:
    """Single-line summary: '[x] #1  Buy milk  [tag1, tag2]'"""
    if todo.get("archived"):
        return f"[archived] #{todo['id']:<4} {todo['title']}{_tags_label(todo)}"
    return f"[{_status_char(todo)}] #{todo['id']:<4} {todo['title']}{_tags_label(todo)}"


def format_todo_list(todos: list[dict]) -> str:
    if not todos:
        return "No todos found."
    return "\n".join(format_todo(t) for t in todos)


def format_todo_detail(todo: dict) -> str:
    """Multi-line detail view for a single todo."""
    tags = todo.get("tags", [])
    if todo.get("archived"):
        status = "archived"
    elif todo["done"]:
        status = "done"
    else:
        status = "pending"
    lines = [
        f"ID:      {todo['id']}",
        f"Title:   {todo['title']}",
        f"Status:  {status}",
        f"Created: {_created_label(todo)}",
        f"Tags:    {', '.join(tags) if tags else '(none)'}",
    ]
    return "\n".join(lines)


def _format_duration(seconds: float) -> str:
    if seconds < 3600:
        return f"{seconds / 60:.1f} minutes"
    if seconds < 86400:
        return f"{seconds / 3600:.1f} hours"
    return f"{seconds / 86400:.1f} days"


def format_stats(stats: dict) -> str:
    """Format the stats dict returned by todo.compute_stats() for display."""
    total = stats["total"]
    completed = stats["completed"]
    pending = stats["pending"]
    overdue = stats["overdue"]
    rate = stats["completion_rate"]
    avg_sec: Optional[float] = stats.get("avg_completion_seconds")
    streak = stats["streak_days"]
    by_tag: dict = stats.get("by_tag", {})

    lines = [
        "=== Todo Statistics ===",
        f"Total:             {total}",
        f"  Completed:       {completed}",
        f"  Pending:         {pending}",
        f"  Overdue:         {overdue}",
        f"Completion rate:   {rate:.1f}%",
        f"Avg time to done:  {_format_duration(avg_sec) if avg_sec is not None else 'N/A'}",
        f"Completion streak: {streak} day{'s' if streak != 1 else ''}",
    ]

    if by_tag:
        lines.append("By tag:")
        for tag, count in sorted(by_tag.items()):
            lines.append(f"  {tag}: {count}")
    else:
        lines.append("By tag:            (none)")

    return "\n".join(lines)
