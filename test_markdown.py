"""Tests for formatter.format_markdown_list and the --format markdown CLI flag."""

import subprocess
import sys
import os
import pytest

from formatter import format_markdown_list


def _todo(id, title, done=False, priority="", due_date=""):
    t = {"id": id, "title": title, "done": done}
    if priority:
        t["priority"] = priority
    if due_date:
        t["due_date"] = due_date
    return t


# ---------------------------------------------------------------------------
# format_markdown_list unit tests
# ---------------------------------------------------------------------------

class TestFormatMarkdownList:
    def test_empty_list_returns_no_todos_message(self):
        assert format_markdown_list([]) == "_No todos found._"

    def test_pending_item_uses_unchecked_box(self):
        result = format_markdown_list([_todo(1, "Buy milk")])
        assert result.startswith("- [ ]")

    def test_pending_item_contains_plain_title(self):
        result = format_markdown_list([_todo(1, "Buy milk")])
        assert "Buy milk" in result
        assert "~~" not in result

    def test_done_item_uses_checked_box(self):
        result = format_markdown_list([_todo(1, "Buy milk", done=True)])
        assert result.startswith("- [x]")

    def test_done_item_uses_strikethrough(self):
        result = format_markdown_list([_todo(1, "Buy milk", done=True)])
        assert "~~Buy milk~~" in result

    def test_priority_annotation_included_when_set(self):
        result = format_markdown_list([_todo(1, "Task", priority="high")])
        assert "**[high]**" in result

    def test_due_date_annotation_included_when_set(self):
        result = format_markdown_list([_todo(1, "Task", due_date="2026-06-15")])
        assert "_due: 2026-06-15_" in result

    def test_priority_omitted_when_absent(self):
        result = format_markdown_list([_todo(1, "Task")])
        assert "**[" not in result

    def test_due_date_omitted_when_absent(self):
        result = format_markdown_list([_todo(1, "Task")])
        assert "_due:" not in result

    def test_both_annotations_present_when_set(self):
        result = format_markdown_list([_todo(1, "Task", priority="low", due_date="2026-07-01")])
        assert "**[low]**" in result
        assert "_due: 2026-07-01_" in result

    def test_multiple_todos_each_on_own_line(self):
        todos = [_todo(1, "A"), _todo(2, "B"), _todo(3, "C")]
        lines = format_markdown_list(todos).split("\n")
        assert len(lines) == 3

    def test_mixed_done_and_pending(self):
        todos = [_todo(1, "Pending"), _todo(2, "Done", done=True)]
        lines = format_markdown_list(todos).split("\n")
        assert lines[0].startswith("- [ ]")
        assert lines[1].startswith("- [x]")

    def test_returns_string(self):
        assert isinstance(format_markdown_list([_todo(1, "Task")]), str)

    def test_priority_appears_before_due_date(self):
        result = format_markdown_list([_todo(1, "Task", priority="medium", due_date="2026-06-01")])
        pri_pos = result.index("**[medium]**")
        due_pos = result.index("_due:")
        assert pri_pos < due_pos


# ---------------------------------------------------------------------------
# CLI integration: --format markdown flag
# ---------------------------------------------------------------------------

class TestMarkdownCLIFlag:
    @pytest.fixture(autouse=True)
    def isolate_storage(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))

    def test_format_markdown_exits_zero(self, tmp_path, monkeypatch):
        env = {**os.environ, "TODO_FILE": str(tmp_path / "todos.json")}
        result = subprocess.run(
            [sys.executable, "main.py", "list", "--format", "markdown"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0

    def test_format_markdown_outputs_no_todos_message(self, tmp_path):
        env = {**os.environ, "TODO_FILE": str(tmp_path / "todos.json")}
        result = subprocess.run(
            [sys.executable, "main.py", "list", "--format", "markdown"],
            capture_output=True, text=True, env=env,
        )
        assert "_No todos found._" in result.stdout

    def test_format_text_still_works(self, tmp_path):
        env = {**os.environ, "TODO_FILE": str(tmp_path / "todos.json")}
        result = subprocess.run(
            [sys.executable, "main.py", "list", "--format", "text"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0

    def test_invalid_format_exits_nonzero(self, tmp_path):
        env = {**os.environ, "TODO_FILE": str(tmp_path / "todos.json")}
        result = subprocess.run(
            [sys.executable, "main.py", "list", "--format", "html"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode != 0
