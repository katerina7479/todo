import re
from datetime import datetime


MAX_TITLE_LENGTH = 200
VALID_PRIORITIES = {"low", "medium", "high"}


def validate_title(title: str) -> str:
    if not isinstance(title, str):
        raise TypeError("Title must be a string")
    title = title.strip()
    if not title:
        raise ValueError("Title cannot be empty")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"Title cannot exceed {MAX_TITLE_LENGTH} characters")
    return title


def validate_priority(priority: str) -> str:
    if not isinstance(priority, str):
        raise TypeError("Priority must be a string")
    priority = priority.strip().lower()
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Priority must be one of: {', '.join(sorted(VALID_PRIORITIES))}")
    return priority


def validate_todo_id(todo_id: int) -> int:
    if not isinstance(todo_id, int):
        raise TypeError("Todo ID must be an integer")
    if todo_id < 1:
        raise ValueError("Todo ID must be a positive integer")
    return todo_id
