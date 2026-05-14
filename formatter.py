from typing import List

from todo import Todo


PRIORITY_SYMBOLS = {
    "high": "!!!",
    "medium": "!!",
    "low": "!",
}

DONE_SYMBOL = "[x]"
PENDING_SYMBOL = "[ ]"


def format_todo(todo: Todo) -> str:
    status = DONE_SYMBOL if todo.done else PENDING_SYMBOL
    priority = PRIORITY_SYMBOLS.get(todo.priority, "!!")
    return f"{todo.id:3}. {status} {priority} {todo.title}"


def format_list(todos: List[Todo]) -> str:
    if not todos:
        return "No todos found."
    lines = [format_todo(t) for t in todos]
    return "\n".join(lines)


def format_detail(todo: Todo) -> str:
    status = "done" if todo.done else "pending"
    return (
        f"ID:       {todo.id}\n"
        f"Title:    {todo.title}\n"
        f"Status:   {status}\n"
        f"Priority: {todo.priority}\n"
        f"Created:  {todo.created_at}"
    )
