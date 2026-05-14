"""Terminal output formatting for todo items using the rich library."""

from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table, box
from rich.text import Text

console = Console()

_PRIORITY_STYLES = {
    "P1": "bold red",
    "P2": "yellow",
    "P3": "green",
    "P4": "dim",
}


def _done_char(todo: dict) -> str:
    return "✓" if todo["done"] else "☐"


def _created_label(todo: dict) -> str:
    try:
        dt = datetime.fromisoformat(todo["created_at"])
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except (KeyError, ValueError):
        return "unknown"


def _due_parts(todo: dict) -> tuple[str, str]:
    """Return (date_str, style) for due date; red if overdue and not done."""
    due = todo.get("due_date")
    if not due:
        return "", ""
    try:
        due_dt = datetime.fromisoformat(due)
        if due_dt.tzinfo is None:
            due_dt = due_dt.replace(tzinfo=timezone.utc)
        date_str = due_dt.strftime("%Y-%m-%d")
        overdue = due_dt < datetime.now(timezone.utc) and not todo.get("done")
        return date_str, "bold red" if overdue else ""
    except ValueError:
        return due, ""


def _repeat_label(todo: dict) -> str:
    """Return a short human-readable repeat label, or empty string if none."""
    repeat = todo.get("repeat")
    if not repeat:
        return ""
    if repeat in ("daily", "weekly", "monthly"):
        return repeat
    if repeat.startswith("custom:"):
        tail = repeat[7:]
        try:
            days = int(tail)
            return f"every {days}d"
        except ValueError:
            return repeat
    return repeat


def print_todo_list(todos: list[dict]) -> None:
    if not todos:
        console.print("No todos found.", style="dim")
        return

    table = Table(show_header=True, header_style="bold", box=box.SIMPLE)
    table.add_column("", width=2, no_wrap=True)
    table.add_column("ID", style="dim", width=5, no_wrap=True)
    table.add_column("Title")
    table.add_column("Priority", width=8, no_wrap=True)
    table.add_column("Due", width=12, no_wrap=True)
    table.add_column("Repeat", width=8, no_wrap=True)
    table.add_column("Tags", style="cyan", no_wrap=True)

    for t in todos:
        done = t["done"]
        done_text = Text(_done_char(t), style="green" if done else "")
        title_text = Text(t["title"], style="strike dim" if done else "")
        priority = t.get("priority", "")
        pri_text = Text(priority, style=_PRIORITY_STYLES.get(priority, ""))
        due_str, due_style = _due_parts(t)
        due_text = Text(due_str, style=due_style)
        repeat_text = Text(_repeat_label(t), style="magenta")
        tags = ", ".join(t.get("tags", []))
        table.add_row(done_text, str(t["id"]), title_text, pri_text, due_text, repeat_text, tags)

    console.print(table)


def print_todo_detail(todo: dict) -> None:
    done = todo["done"]
    done_label = "✓ done" if done else "☐ pending"
    done_style = "green" if done else "yellow"
    priority = todo.get("priority", "")
    due_str, due_style = _due_parts(todo)
    tags = ", ".join(todo.get("tags", [])) or "(none)"
    repeat = _repeat_label(todo)

    content = Text()
    content.append(f"ID:      {todo['id']}\n", style="dim")
    content.append("Title:   ")
    content.append(f"{todo['title']}\n", style="bold")
    content.append("Status:  ")
    content.append(f"{done_label}\n", style=done_style)
    content.append(f"Created: {_created_label(todo)}\n")
    if priority:
        content.append("Priority: ")
        content.append(f"{priority}\n", style=_PRIORITY_STYLES.get(priority, ""))
    if due_str:
        content.append("Due:     ")
        content.append(f"{due_str}\n", style=due_style)
    if repeat:
        content.append("Repeat:  ")
        content.append(f"{repeat}\n", style="magenta")
    content.append(f"Tags:    {tags}\n")

    console.print(Panel(content, title=f"Todo #{todo['id']}", expand=False))


def print_todo_added(todo: dict) -> None:
    repeat = _repeat_label(todo)
    suffix = f" [magenta](repeats {repeat})[/magenta]" if repeat else ""
    console.print(f"[green]✓ Added:[/green] #{todo['id']} {todo['title']}{suffix}")


def print_todo_done(todo: dict, next_occurrence: Optional[dict] = None) -> None:
    console.print(f"[green]✓ Marked done:[/green] #{todo['id']} {todo['title']}")
    if next_occurrence:
        due = next_occurrence.get("due_date", "")
        due_str = f" (due {due})" if due else ""
        console.print(
            f"[blue]↻ Next occurrence scheduled:[/blue] "
            f"#{next_occurrence['id']} {next_occurrence['title']}{due_str}"
        )


def print_todo_deleted(todo: dict) -> None:
    console.print(f"[red]✗ Deleted:[/red] #{todo['id']} {todo['title']}")
