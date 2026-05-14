"""Tests for recurring todo logic (pb-25)."""

from datetime import date
import pytest

import todo


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))


# ---------------------------------------------------------------------------
# _advance_date
# ---------------------------------------------------------------------------

class TestAdvanceDate:
    def test_daily_adds_one_day(self):
        base = date(2026, 5, 1)
        assert todo._advance_date(base, "daily") == date(2026, 5, 2)

    def test_weekly_adds_seven_days(self):
        base = date(2026, 5, 1)
        assert todo._advance_date(base, "weekly") == date(2026, 5, 8)

    def test_monthly_same_day_next_month(self):
        base = date(2026, 3, 15)
        assert todo._advance_date(base, "monthly") == date(2026, 4, 15)

    def test_monthly_clamps_short_month(self):
        # Jan 31 → Feb 28 (non-leap year)
        base = date(2026, 1, 31)
        assert todo._advance_date(base, "monthly") == date(2026, 2, 28)

    def test_monthly_clamps_leap_year(self):
        # Jan 31 → Feb 29 in a leap year
        base = date(2024, 1, 31)
        assert todo._advance_date(base, "monthly") == date(2024, 2, 29)

    def test_monthly_rolls_december_to_january(self):
        base = date(2026, 12, 15)
        assert todo._advance_date(base, "monthly") == date(2027, 1, 15)

    def test_custom_adds_n_days(self):
        base = date(2026, 5, 1)
        assert todo._advance_date(base, "custom:10") == date(2026, 5, 11)

    def test_custom_one_day(self):
        base = date(2026, 5, 1)
        assert todo._advance_date(base, "custom:1") == date(2026, 5, 2)

    def test_custom_invalid_string_returns_none(self):
        base = date(2026, 5, 1)
        assert todo._advance_date(base, "custom:abc") is None

    def test_unknown_schedule_returns_none(self):
        base = date(2026, 5, 1)
        assert todo._advance_date(base, "fortnight") is None

    def test_empty_string_returns_none(self):
        base = date(2026, 5, 1)
        assert todo._advance_date(base, "") is None


# ---------------------------------------------------------------------------
# _next_due_date
# ---------------------------------------------------------------------------

class TestNextDueDate:
    def test_no_repeat_returns_none(self):
        item = {"title": "T", "done": False}
        assert todo._next_due_date(item) is None

    def test_daily_with_due_date(self):
        item = {"repeat": "daily", "due_date": "2026-05-01"}
        assert todo._next_due_date(item) == "2026-05-02"

    def test_weekly_with_due_date(self):
        item = {"repeat": "weekly", "due_date": "2026-05-01"}
        assert todo._next_due_date(item) == "2026-05-08"

    def test_monthly_boundary(self):
        item = {"repeat": "monthly", "due_date": "2026-01-31"}
        assert todo._next_due_date(item) == "2026-02-28"

    def test_invalid_due_date_falls_back_to_today(self):
        # Should not raise; falls back to date.today() + advance
        item = {"repeat": "daily", "due_date": "not-a-date"}
        result = todo._next_due_date(item)
        assert result is not None  # gets today + 1

    def test_no_due_date_uses_today(self):
        item = {"repeat": "daily"}
        result = todo._next_due_date(item)
        assert result is not None

    def test_invalid_repeat_returns_none(self):
        item = {"repeat": "fortnight", "due_date": "2026-05-01"}
        assert todo._next_due_date(item) is None


# ---------------------------------------------------------------------------
# mark_done with repeat
# ---------------------------------------------------------------------------

class TestMarkDoneWithRepeat:
    def test_mark_done_no_repeat_returns_none_next(self):
        t = todo.add_todo("Simple task")
        completed, next_occ = todo.mark_done(t["id"])
        assert completed["done"] is True
        assert next_occ is None

    def test_mark_done_with_repeat_returns_next_occurrence(self):
        t = todo.add_todo("Daily standup", repeat="daily", due_date="2026-05-01")
        completed, next_occ = todo.mark_done(t["id"])
        assert next_occ is not None

    def test_next_occurrence_has_advanced_due_date(self):
        t = todo.add_todo("Daily standup", repeat="daily", due_date="2026-05-01")
        _, next_occ = todo.mark_done(t["id"])
        assert next_occ["due_date"] == "2026-05-02"

    def test_next_occurrence_is_pending(self):
        t = todo.add_todo("Daily standup", repeat="daily", due_date="2026-05-01")
        _, next_occ = todo.mark_done(t["id"])
        assert next_occ["done"] is False

    def test_next_occurrence_copies_title(self):
        t = todo.add_todo("Weekly review", repeat="weekly", due_date="2026-05-01")
        _, next_occ = todo.mark_done(t["id"])
        assert next_occ["title"] == "Weekly review"

    def test_next_occurrence_copies_repeat(self):
        t = todo.add_todo("Monthly report", repeat="monthly", due_date="2026-01-31")
        _, next_occ = todo.mark_done(t["id"])
        assert next_occ["repeat"] == "monthly"

    def test_next_occurrence_persisted_in_store(self):
        t = todo.add_todo("Daily standup", repeat="daily", due_date="2026-05-01")
        _, next_occ = todo.mark_done(t["id"])
        assert todo.get_todo(next_occ["id"]) is not None

    def test_next_occurrence_gets_new_id(self):
        t = todo.add_todo("Daily standup", repeat="daily", due_date="2026-05-01")
        _, next_occ = todo.mark_done(t["id"])
        assert next_occ["id"] != t["id"]

    def test_next_occurrence_monthly_boundary(self):
        t = todo.add_todo("End of month", repeat="monthly", due_date="2026-01-31")
        _, next_occ = todo.mark_done(t["id"])
        assert next_occ["due_date"] == "2026-02-28"

    def test_mark_done_nonexistent_raises_value_error(self):
        with pytest.raises(ValueError, match="not found"):
            todo.mark_done(999)

    def test_completed_todo_marked_done_in_store(self):
        t = todo.add_todo("Daily standup", repeat="daily", due_date="2026-05-01")
        todo.mark_done(t["id"])
        assert todo.get_todo(t["id"])["done"] is True

    def test_next_occurrence_copies_tags(self):
        t = todo.add_todo("Standup", repeat="daily", due_date="2026-05-01",
                          tags=["work", "meeting"])
        _, next_occ = todo.mark_done(t["id"])
        assert next_occ["tags"] == ["work", "meeting"]


# ---------------------------------------------------------------------------
# delete_todo error type
# ---------------------------------------------------------------------------

class TestDeleteTodo:
    def test_delete_nonexistent_raises_value_error(self):
        with pytest.raises(ValueError, match="not found"):
            todo.delete_todo(999)

    def test_delete_existing_removes_from_store(self):
        t = todo.add_todo("Temporary")
        todo.delete_todo(t["id"])
        assert todo.get_todo(t["id"]) is None
