"""Input validation for the todo CLI."""


def validate_title(title: str) -> str:
    """Return stripped title, raising ValueError if blank."""
    stripped = title.strip()
    if not stripped:
        raise ValueError("Todo title cannot be empty.")
    return stripped


def validate_id(raw_id: str) -> int:
    """Return integer id, raising ValueError if not a positive integer."""
    try:
        todo_id = int(raw_id)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid id '{raw_id}': must be a positive integer.")
    if todo_id < 1:
        raise ValueError(f"Invalid id '{raw_id}': must be a positive integer.")
    return todo_id
