import pytest
from datetime import datetime, timezone

from formatter import format_todo, format_todo_list, format_todo_detail


@pytest.fixture
def pending_todo():
    return {
        "id": 1,
        "title": "Buy groceries",
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def done_todo():
    return {
        "id": 2,
        "title": "Write tests",
        "done": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def todo_list(pending_todo, done_todo):
    return [pending_todo, done_todo]


class TestFormatTodo:
    def test_pending_shows_space(self, pending_todo):
        result = format_todo(pending_todo)
        assert "[ ]" in result

    def test_done_shows_x(self, done_todo):
        result = format_todo(done_todo)
        assert "[x]" in result

    def test_includes_title(self, pending_todo):
        assert "Buy groceries" in format_todo(pending_todo)

    def test_includes_id(self, pending_todo):
        assert "1" in format_todo(pending_todo)

    def test_returns_string(self, pending_todo):
        assert isinstance(format_todo(pending_todo), str)


class TestFormatTodoList:
    def test_empty_list_message(self):
        result = format_todo_list([])
        assert "No todos" in result

    def test_single_todo_includes_title(self, pending_todo):
        assert "Buy groceries" in format_todo_list([pending_todo])

    def test_multiple_todos_each_on_own_line(self, todo_list):
        lines = format_todo_list(todo_list).strip().split("\n")
        assert len(lines) == 2

    def test_all_titles_included(self, todo_list):
        result = format_todo_list(todo_list)
        assert "Buy groceries" in result
        assert "Write tests" in result

    def test_returns_string(self, todo_list):
        assert isinstance(format_todo_list(todo_list), str)


class TestFormatTodoDetail:
    def test_includes_id(self, pending_todo):
        assert "1" in format_todo_detail(pending_todo)

    def test_includes_title(self, pending_todo):
        assert "Buy groceries" in format_todo_detail(pending_todo)

    def test_pending_status(self, pending_todo):
        assert "pending" in format_todo_detail(pending_todo).lower()

    def test_done_status(self, done_todo):
        assert "done" in format_todo_detail(done_todo).lower()

    def test_includes_created_label(self, pending_todo):
        result = format_todo_detail(pending_todo)
        assert "Created" in result

    def test_returns_string(self, pending_todo):
        assert isinstance(format_todo_detail(pending_todo), str)

    def test_missing_created_at_shows_unknown(self):
        todo = {"id": 3, "title": "No date", "done": False}
        assert "unknown" in format_todo_detail(todo)
