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


def format_markdown_list(todos: list[dict]) -> str:
    """GitHub-flavored Markdown checklist with priorities and due dates."""
    if not todos:
        return "_No todos found._"
    lines = []
    for t in todos:
        check = "x" if t["done"] else " "
        title = f"~~{t['title']}~~" if t["done"] else t["title"]
        parts = [f"- [{check}] {title}"]
        priority = t.get("priority", "")
        if priority:
            parts.append(f"**[{priority}]**")
        due = t.get("due_date", "")
        if due:
            parts.append(f"_due: {due}_")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def format_todo_detail(todo: dict) -> str:
    """Multi-line detail view for a single todo."""
    lines = [
        f"ID:       {todo['id']}",
        f"Title:    {todo['title']}",
        f"Status:   {'done' if todo['done'] else 'pending'}",
        f"Priority: {todo.get('priority', '-')}",
        f"Due:      {todo.get('due_date', '-')}",
        f"Tags:     {', '.join(todo['tags']) if todo.get('tags') else '-'}",
        f"Created:  {_created_label(todo)}",
    ]
    return "\n".join(lines)
