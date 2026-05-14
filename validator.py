"""Input validation for the todo CLI."""

from datetime import date

VALID_PRIORITIES = {"1", "2", "3", "4"}


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


def validate_priority(raw: str) -> int:
    """Return integer priority 1-4, raising ValueError otherwise."""
    if raw not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority '{raw}': must be 1, 2, 3, or 4.")
    return int(raw)


def validate_due_date(raw: str) -> str:
    """Return ISO date string (YYYY-MM-DD), raising ValueError on bad format."""
    try:
        date.fromisoformat(raw)
    except ValueError:
        raise ValueError(f"Invalid due date '{raw}': expected YYYY-MM-DD.")
    return raw


def validate_tags(raw: str) -> list[str]:
    """Return list of stripped, non-empty tag strings from a comma-separated input."""
    tags = [t.strip() for t in raw.split(",")]
    tags = [t for t in tags if t]
    if not tags:
        raise ValueError("Tags cannot be empty.")
    return tags
