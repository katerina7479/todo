"""Input validation for the todo CLI."""

import re
from datetime import date, timedelta

from dateutil.parser import parse as _dateutil_parse
from dateutil.parser import ParserError

VALID_PRIORITIES = {"low", "medium", "high"}

_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


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


def validate_priority(raw: str) -> str:
    """Return normalised priority string (low/medium/high), raising ValueError otherwise."""
    normalised = raw.strip().lower()
    if normalised not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority '{raw}': must be low, medium, or high.")
    return normalised


def validate_due_date(raw: str) -> str:
    """Parse natural language or ISO date to YYYY-MM-DD string.

    Accepted forms: 'tomorrow', 'next <weekday>', 'in N days', or any date
    string parseable by python-dateutil (e.g. '2026-06-15', 'Jun 15 2026').
    """
    text = raw.strip().lower()
    today = date.today()

    if text == "tomorrow":
        return (today + timedelta(days=1)).isoformat()

    m = re.match(r"^in\s+(\d+)\s+days?$", text)
    if m:
        return (today + timedelta(days=int(m.group(1)))).isoformat()

    m = re.match(r"^next\s+(\w+)$", text)
    if m:
        day_name = m.group(1)
        if day_name not in _WEEKDAYS:
            raise ValueError(
                f"Invalid due date '{raw}': unknown weekday '{day_name}'."
            )
        target = _WEEKDAYS[day_name]
        days_ahead = (target - today.weekday()) % 7 or 7
        return (today + timedelta(days=days_ahead)).isoformat()

    try:
        return _dateutil_parse(raw, dayfirst=False).date().isoformat()
    except (ParserError, ValueError, OverflowError):
        raise ValueError(
            f"Invalid due date '{raw}': expected a date like '2026-06-15', "
            "'tomorrow', 'next friday', or 'in 3 days'."
        )


def validate_tags(raw: str) -> list[str]:
    """Return list of stripped, non-empty tag strings from a comma-separated input."""
    tags = [t.strip() for t in raw.split(",")]
    tags = [t for t in tags if t]
    if not tags:
        raise ValueError("Tags cannot be empty.")
    return tags
