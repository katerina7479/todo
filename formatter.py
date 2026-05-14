"""Terminal output formatting for todo items."""

from datetime import datetime


def _status_char(todo: dict) -> str:
    return "x" if todo["done"] else " "


def _created_label(todo: dict) -> str:
    try:
        dt = datetime.fromisoformat(todo["created_at"])
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except (KeyError, ValueError):
        return "unknown"


def format_todo(todo: dict) -> str:
    """Single-line summary: '[x] #1  Buy milk'"""
    return f"[{_status_char(todo)}] #{todo['id']:<4} {todo['title']}"


def format_todo_list(todos: list[dict]) -> str:
    if not todos:
        return "No todos found."
    return "\n".join(format_todo(t) for t in todos)


def format_todo_detail(todo: dict) -> str:
    """Multi-line detail view for a single todo."""
    lines = [
        f"ID:      {todo['id']}",
        f"Title:   {todo['title']}",
        f"Status:  {'done' if todo['done'] else 'pending'}",
        f"Created: {_created_label(todo)}",
    ]
    return "\n".join(lines)
