"""Tests for natural language date parsing via validate_due_date (pb-32)."""

from datetime import date, timedelta
import pytest

import validator


# ---------------------------------------------------------------------------
# Fixture: freeze date.today() to 2026-05-13 (a Wednesday, weekday=2)
# ---------------------------------------------------------------------------

FIXED_TODAY = date(2026, 5, 13)  # Wednesday


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    class _FakeDate(date):
        @classmethod
        def today(cls):
            return FIXED_TODAY

    monkeypatch.setattr(validator, "date", _FakeDate)


# ---------------------------------------------------------------------------
# 'tomorrow'
# ---------------------------------------------------------------------------

class TestTomorrow:
    def test_tomorrow_returns_next_day(self):
        assert validator.validate_due_date("tomorrow") == "2026-05-14"

    def test_tomorrow_case_insensitive(self):
        assert validator.validate_due_date("Tomorrow") == "2026-05-14"

    def test_tomorrow_with_surrounding_whitespace(self):
        assert validator.validate_due_date("  tomorrow  ") == "2026-05-14"


# ---------------------------------------------------------------------------
# 'in N days'
# ---------------------------------------------------------------------------

class TestInNDays:
    def test_in_1_day(self):
        assert validator.validate_due_date("in 1 day") == "2026-05-14"

    def test_in_3_days(self):
        assert validator.validate_due_date("in 3 days") == "2026-05-16"

    def test_in_7_days(self):
        assert validator.validate_due_date("in 7 days") == "2026-05-20"

    def test_in_30_days(self):
        assert validator.validate_due_date("in 30 days") == "2026-06-12"

    def test_in_days_case_insensitive(self):
        assert validator.validate_due_date("In 5 Days") == "2026-05-18"

    def test_in_days_singular_form(self):
        assert validator.validate_due_date("in 1 day") == "2026-05-14"


# ---------------------------------------------------------------------------
# 'next <weekday>'
# ---------------------------------------------------------------------------

class TestNextWeekday:
    # From Wednesday (2), calculate expected dates:
    # friday (4): (4-2)%7 = 2 → May 15
    # monday (0): (0-2)%7 = 5 → May 18
    # saturday (5): (5-2)%7 = 3 → May 16
    # sunday (6): (6-2)%7 = 4 → May 17
    # tuesday (1): (1-2)%7 = 6 → May 19
    # wednesday (2): (2-2)%7 = 0 → 0 or 7 = 7 → May 20 (same weekday → next week)
    # thursday (3): (3-2)%7 = 1 → May 14

    def test_next_friday(self):
        assert validator.validate_due_date("next friday") == "2026-05-15"

    def test_next_monday(self):
        assert validator.validate_due_date("next monday") == "2026-05-18"

    def test_next_saturday(self):
        assert validator.validate_due_date("next saturday") == "2026-05-16"

    def test_next_sunday(self):
        assert validator.validate_due_date("next sunday") == "2026-05-17"

    def test_next_tuesday(self):
        assert validator.validate_due_date("next tuesday") == "2026-05-19"

    def test_next_thursday(self):
        assert validator.validate_due_date("next thursday") == "2026-05-14"

    def test_next_same_weekday_advances_full_week(self):
        # 'next wednesday' when today is Wednesday → 7 days ahead, not 0
        assert validator.validate_due_date("next wednesday") == "2026-05-20"

    def test_next_weekday_case_insensitive(self):
        assert validator.validate_due_date("Next Friday") == "2026-05-15"

    def test_next_unknown_weekday_raises(self):
        with pytest.raises(ValueError, match="unknown weekday"):
            validator.validate_due_date("next funday")


# ---------------------------------------------------------------------------
# ISO / freeform dates (via dateutil)
# ---------------------------------------------------------------------------

class TestIsoAndFreeform:
    def test_iso_date_string(self):
        assert validator.validate_due_date("2026-06-15") == "2026-06-15"

    def test_iso_date_in_past(self):
        # dateutil parses it; no prohibition on past dates at validation time
        assert validator.validate_due_date("2020-01-01") == "2020-01-01"

    def test_freeform_month_day_year(self):
        assert validator.validate_due_date("Jun 15 2026") == "2026-06-15"

    def test_freeform_american_format(self):
        assert validator.validate_due_date("06/15/2026") == "2026-06-15"

    def test_freeform_long_form(self):
        assert validator.validate_due_date("June 15, 2026") == "2026-06-15"


# ---------------------------------------------------------------------------
# Invalid input
# ---------------------------------------------------------------------------

class TestInvalidInput:
    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            validator.validate_due_date("")

    def test_gibberish_raises(self):
        with pytest.raises(ValueError):
            validator.validate_due_date("not-a-date")

    def test_in_zero_days_is_valid(self):
        # 'in 0 days' matches the regex — returns today
        assert validator.validate_due_date("in 0 days") == "2026-05-13"

    def test_in_non_numeric_days_raises(self):
        with pytest.raises(ValueError):
            validator.validate_due_date("in many days")

    def test_next_with_no_weekday_raises(self):
        with pytest.raises(ValueError):
            validator.validate_due_date("next")


# ---------------------------------------------------------------------------
# Integration: add --due-date wired through cmd_add
# ---------------------------------------------------------------------------

class TestAddWithDueDate:
    @pytest.fixture(autouse=True)
    def storage(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))

    def test_add_stores_parsed_due_date(self):
        import todo
        item = todo.add_todo("Task", due_date="2026-06-15")
        assert item.get("due_date") == "2026-06-15"

    def test_add_without_due_date_omits_field(self):
        import todo
        item = todo.add_todo("Task")
        assert "due_date" not in item

    def test_cmd_add_parses_natural_date(self):
        import main as main_mod
        import todo
        parser = main_mod.build_parser()
        args = parser.parse_args(["add", "Task", "--due-date", "tomorrow"])
        args.func(args)
        stored = todo.get_todo(1)
        assert stored["due_date"] == "2026-05-14"

    def test_cmd_add_rejects_invalid_due_date(self, capsys):
        import main as main_mod
        parser = main_mod.build_parser()
        args = parser.parse_args(["add", "Task", "--due-date", "not-a-date"])
        rc = args.func(args)
        assert rc == 1
        assert "Error" in capsys.readouterr().err
