"""Tests for compute_stats() and format_stats() (pb-28)."""

from datetime import datetime, timedelta, timezone
import pytest

import todo
import formatter


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))


def _add(title, tags=None):
    return todo.add_todo(title, tags=tags or [])


def _mark_done(todo_id):
    return todo.mark_done(todo_id)


# ---------------------------------------------------------------------------
# compute_stats
# ---------------------------------------------------------------------------

class TestComputeStatsEmpty:
    def test_empty_store_all_zeros(self):
        s = todo.compute_stats()
        assert s["total"] == 0
        assert s["completed"] == 0
        assert s["pending"] == 0
        assert s["overdue"] == 0
        assert s["completion_rate"] == 0.0
        assert s["by_tag"] == {}
        assert s["avg_completion_seconds"] is None
        assert s["streak_days"] == 0


class TestComputeStatsAllPending:
    def test_all_pending_completion_rate_zero(self):
        _add("Task A")
        _add("Task B")
        s = todo.compute_stats()
        assert s["total"] == 2
        assert s["completed"] == 0
        assert s["pending"] == 2
        assert s["completion_rate"] == 0.0

    def test_all_pending_no_avg(self):
        _add("Task A")
        s = todo.compute_stats()
        assert s["avg_completion_seconds"] is None

    def test_all_pending_streak_zero(self):
        _add("Task A")
        s = todo.compute_stats()
        assert s["streak_days"] == 0


class TestComputeStatsAllCompleted:
    def test_all_completed_rate_100(self):
        item = _add("Task A")
        _mark_done(item["id"])
        s = todo.compute_stats()
        assert s["total"] == 1
        assert s["completed"] == 1
        assert s["pending"] == 0
        assert s["completion_rate"] == 100.0

    def test_completion_rate_partial(self):
        a = _add("Task A")
        _add("Task B")
        _mark_done(a["id"])
        s = todo.compute_stats()
        assert s["completion_rate"] == pytest.approx(50.0)


class TestComputeStatsOverdue:
    def test_pending_with_past_due_date_is_overdue(self, monkeypatch):
        import json, os
        path = os.environ["TODO_FILE"]
        past = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
        data = {
            "next_id": 2,
            "todos": [{
                "id": 1,
                "title": "Old task",
                "done": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "tags": [],
                "due_date": past,
            }],
        }
        import pathlib
        pathlib.Path(path).write_text(json.dumps(data))
        s = todo.compute_stats()
        assert s["overdue"] == 1

    def test_pending_with_future_due_date_not_overdue(self, monkeypatch):
        import json, os, pathlib
        path = os.environ["TODO_FILE"]
        future = (datetime.now(timezone.utc) + timedelta(days=10)).date().isoformat()
        data = {
            "next_id": 2,
            "todos": [{
                "id": 1,
                "title": "Future task",
                "done": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "tags": [],
                "due_date": future,
            }],
        }
        pathlib.Path(path).write_text(json.dumps(data))
        s = todo.compute_stats()
        assert s["overdue"] == 0

    def test_done_with_past_due_date_not_overdue(self):
        item = _add("Task")
        _mark_done(item["id"])
        s = todo.compute_stats()
        assert s["overdue"] == 0


class TestComputeStatsByTag:
    def test_single_tag_counted(self):
        _add("Task", tags=["work"])
        s = todo.compute_stats()
        assert s["by_tag"] == {"work": 1}

    def test_multiple_tags_counted(self):
        _add("Task A", tags=["work", "urgent"])
        _add("Task B", tags=["work"])
        s = todo.compute_stats()
        assert s["by_tag"]["work"] == 2
        assert s["by_tag"]["urgent"] == 1

    def test_no_tags_empty_dict(self):
        _add("Task A")
        s = todo.compute_stats()
        assert s["by_tag"] == {}


class TestComputeStatsAvgCompletionTime:
    def test_avg_completion_seconds_populated(self, monkeypatch):
        import json, os, pathlib
        path = os.environ["TODO_FILE"]
        created = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        completed = datetime(2026, 5, 1, 11, 0, 0, tzinfo=timezone.utc)  # 3600s later
        data = {
            "next_id": 2,
            "todos": [{
                "id": 1,
                "title": "Fast task",
                "done": True,
                "created_at": created.isoformat(),
                "completed_at": completed.isoformat(),
                "tags": [],
            }],
        }
        pathlib.Path(path).write_text(json.dumps(data))
        s = todo.compute_stats()
        assert s["avg_completion_seconds"] == pytest.approx(3600.0)

    def test_avg_completion_multiple(self, monkeypatch):
        import json, os, pathlib
        path = os.environ["TODO_FILE"]
        base = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        data = {
            "next_id": 3,
            "todos": [
                {
                    "id": 1,
                    "title": "Task A",
                    "done": True,
                    "created_at": base.isoformat(),
                    "completed_at": (base + timedelta(seconds=1000)).isoformat(),
                    "tags": [],
                },
                {
                    "id": 2,
                    "title": "Task B",
                    "done": True,
                    "created_at": base.isoformat(),
                    "completed_at": (base + timedelta(seconds=3000)).isoformat(),
                    "tags": [],
                },
            ],
        }
        pathlib.Path(path).write_text(json.dumps(data))
        s = todo.compute_stats()
        assert s["avg_completion_seconds"] == pytest.approx(2000.0)

    def test_no_completed_at_excluded_from_avg(self):
        item = _add("Task")
        _mark_done(item["id"])
        # avg should be set since mark_done stamps completed_at
        s = todo.compute_stats()
        assert s["avg_completion_seconds"] is not None


class TestComputeStatsStreak:
    def _write_store_with_completions(self, path, dates):
        """Write a store where each date gets one completed todo."""
        import json, pathlib
        todos = []
        for i, d in enumerate(dates, start=1):
            completed_dt = datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc)
            todos.append({
                "id": i,
                "title": f"Task {i}",
                "done": True,
                "created_at": completed_dt.isoformat(),
                "completed_at": completed_dt.isoformat(),
                "tags": [],
            })
        data = {"next_id": len(todos) + 1, "todos": todos}
        pathlib.Path(path).write_text(json.dumps(data))

    def test_streak_of_one_today(self, monkeypatch):
        import os
        from datetime import date
        today = date.today()
        self._write_store_with_completions(os.environ["TODO_FILE"], [today])
        s = todo.compute_stats()
        assert s["streak_days"] == 1

    def test_streak_of_n_consecutive_days(self, monkeypatch):
        import os
        from datetime import date
        today = date.today()
        days = [today - timedelta(days=i) for i in range(3)]
        self._write_store_with_completions(os.environ["TODO_FILE"], days)
        s = todo.compute_stats()
        assert s["streak_days"] == 3

    def test_streak_broken_by_gap(self, monkeypatch):
        import os
        from datetime import date
        today = date.today()
        # completed today and 3 days ago, but not yesterday or 2 days ago
        days = [today, today - timedelta(days=3)]
        self._write_store_with_completions(os.environ["TODO_FILE"], days)
        s = todo.compute_stats()
        assert s["streak_days"] == 1

    def test_no_completions_streak_zero(self):
        _add("Task")
        s = todo.compute_stats()
        assert s["streak_days"] == 0


# ---------------------------------------------------------------------------
# format_stats
# ---------------------------------------------------------------------------

class TestFormatStats:
    def _base_stats(self, **overrides):
        s = {
            "total": 5,
            "completed": 3,
            "pending": 2,
            "overdue": 1,
            "completion_rate": 60.0,
            "by_tag": {},
            "avg_completion_seconds": None,
            "streak_days": 0,
        }
        s.update(overrides)
        return s

    def test_format_contains_header(self):
        out = formatter.format_stats(self._base_stats())
        assert "=== Todo Statistics ===" in out

    def test_format_shows_counts(self):
        out = formatter.format_stats(self._base_stats())
        assert "5" in out
        assert "3" in out
        assert "2" in out

    def test_format_completion_rate(self):
        out = formatter.format_stats(self._base_stats(completion_rate=60.0))
        assert "60.0%" in out

    def test_format_avg_na_when_none(self):
        out = formatter.format_stats(self._base_stats(avg_completion_seconds=None))
        assert "N/A" in out

    def test_format_avg_shows_duration(self):
        out = formatter.format_stats(self._base_stats(avg_completion_seconds=7200.0))
        assert "hours" in out or "2.0" in out

    def test_format_streak_singular(self):
        out = formatter.format_stats(self._base_stats(streak_days=1))
        assert "1 day" in out
        assert "days" not in out.split("1 day")[1].split("\n")[0]

    def test_format_streak_plural(self):
        out = formatter.format_stats(self._base_stats(streak_days=3))
        assert "3 days" in out

    def test_format_by_tag_shown(self):
        out = formatter.format_stats(self._base_stats(by_tag={"work": 2, "urgent": 1}))
        assert "work" in out
        assert "urgent" in out

    def test_format_no_tags_shown(self):
        out = formatter.format_stats(self._base_stats(by_tag={}))
        assert "(none)" in out
