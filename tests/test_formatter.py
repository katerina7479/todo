import pytest

from todo import Todo
from formatter import format_todo, format_list, format_detail, DONE_SYMBOL, PENDING_SYMBOL


@pytest.fixture
def pending_todo():
    return Todo(id=1, title="Buy groceries", done=False, priority="medium")


@pytest.fixture
def done_todo():
    return Todo(id=2, title="Write tests", done=True, priority="high")


@pytest.fixture
def todo_list(pending_todo, done_todo):
    return [pending_todo, done_todo]


class TestFormatTodo:
    def test_pending_todo_shows_pending_symbol(self, pending_todo):
        result = format_todo(pending_todo)
        assert PENDING_SYMBOL in result

    def test_done_todo_shows_done_symbol(self, done_todo):
        result = format_todo(done_todo)
        assert DONE_SYMBOL in result

    def test_includes_title(self, pending_todo):
        result = format_todo(pending_todo)
        assert "Buy groceries" in result

    def test_includes_id(self, pending_todo):
        result = format_todo(pending_todo)
        assert "1" in result

    def test_high_priority_symbol(self):
        todo = Todo(id=1, title="Urgent", priority="high")
        result = format_todo(todo)
        assert "!!!" in result

    def test_medium_priority_symbol(self):
        todo = Todo(id=1, title="Normal", priority="medium")
        result = format_todo(todo)
        assert "!!" in result

    def test_low_priority_symbol(self):
        todo = Todo(id=1, title="Whenever", priority="low")
        result = format_todo(todo)
        assert "!" in result

    def test_returns_string(self, pending_todo):
        assert isinstance(format_todo(pending_todo), str)


class TestFormatList:
    def test_empty_list_returns_no_todos_message(self):
        result = format_list([])
        assert "No todos" in result

    def test_single_todo(self, pending_todo):
        result = format_list([pending_todo])
        assert "Buy groceries" in result

    def test_multiple_todos_each_on_own_line(self, todo_list):
        result = format_list(todo_list)
        lines = result.strip().split("\n")
        assert len(lines) == 2

    def test_all_todos_included(self, todo_list):
        result = format_list(todo_list)
        assert "Buy groceries" in result
        assert "Write tests" in result

    def test_returns_string(self, todo_list):
        assert isinstance(format_list(todo_list), str)


class TestFormatDetail:
    def test_includes_id(self, pending_todo):
        result = format_detail(pending_todo)
        assert "1" in result

    def test_includes_title(self, pending_todo):
        result = format_detail(pending_todo)
        assert "Buy groceries" in result

    def test_pending_status(self, pending_todo):
        result = format_detail(pending_todo)
        assert "pending" in result.lower()

    def test_done_status(self, done_todo):
        result = format_detail(done_todo)
        assert "done" in result.lower()

    def test_includes_priority(self, pending_todo):
        result = format_detail(pending_todo)
        assert "medium" in result

    def test_includes_created_at(self, pending_todo):
        result = format_detail(pending_todo)
        assert pending_todo.created_at in result

    def test_returns_string(self, pending_todo):
        assert isinstance(format_detail(pending_todo), str)
