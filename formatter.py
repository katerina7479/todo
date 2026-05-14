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


def _tags_label(todo: dict) -> str:
    tags = todo.get("tags", [])
    return f"  [{', '.join(tags)}]" if tags else ""


def format_todo(todo: dict, indent: int = 0) -> str:
    """Single-line summary: '[x] #1  Buy milk  [tag1, tag2]'"""
    prefix = "  " * indent
    return f"[{_status_char(todo)}] {prefix}#{todo['id']:<4} {todo['title']}{_tags_label(todo)}"


def format_todo_list(todos: list[dict]) -> str:
    if not todos:
        return "No todos found."
    lines = []
    for t in todos:
        indent = 1 if t.get("parent_id") is not None else 0
        lines.append(format_todo(t, indent=indent))
    return "\n".join(lines)


def format_todo_detail(todo: dict) -> str:
    """Multi-line detail view for a single todo."""
    tags = todo.get("tags", [])
    lines = [
        f"ID:      {todo['id']}",
        f"Title:   {todo['title']}",
        f"Status:  {'done' if todo['done'] else 'pending'}",
        f"Created: {_created_label(todo)}",
        f"Tags:    {', '.join(tags) if tags else '(none)'}",
    ]
    if todo.get("parent_id") is not None:
        lines.insert(2, f"Parent:  #{todo['parent_id']}")
    return "\n".join(lines)
