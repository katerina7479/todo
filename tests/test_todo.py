import json
import pytest
from pathlib import Path

from config import Config
from todo import Todo, TodoStore


@pytest.fixture
def store(tmp_path):
    config = Config(storage_path=tmp_path / "todos.json")
    return TodoStore(config)


class TestTodo:
    def test_defaults(self):
        todo = Todo(title="Write tests", id=1)
        assert todo.done is False
        assert todo.priority == "medium"
        assert todo.created_at is not None

    def test_to_dict_round_trip(self):
        todo = Todo(id=5, title="Buy milk", done=True, priority="high")
        restored = Todo.from_dict(todo.to_dict())
        assert restored.id == todo.id
        assert restored.title == todo.title
        assert restored.done == todo.done
        assert restored.priority == todo.priority
        assert restored.created_at == todo.created_at

    def test_from_dict_uses_defaults_for_missing_keys(self):
        todo = Todo.from_dict({"id": 1, "title": "Test"})
        assert todo.done is False
        assert todo.priority == "medium"
        assert todo.created_at is not None


class TestTodoStoreAdd:
    def test_add_creates_todo(self, store):
        todo = store.add("Write tests")
        assert todo.id == 1
        assert todo.title == "Write tests"
        assert todo.done is False

    def test_add_increments_id(self, store):
        t1 = store.add("First")
        t2 = store.add("Second")
        assert t2.id == t1.id + 1

    def test_add_persists_to_file(self, store):
        store.add("Persisted todo")
        assert store.config.storage_path.exists()

    def test_add_with_priority(self, store):
        todo = store.add("High priority", priority="high")
        assert todo.priority == "high"

    def test_add_multiple_todos(self, store):
        for i in range(5):
            store.add(f"Todo {i}")
        todos = store.list(show_done=True)
        assert len(todos) == 5


class TestTodoStoreList:
    def test_list_empty_store(self, store):
        assert store.list() == []

    def test_list_returns_pending_only_by_default(self, store):
        store.add("Pending")
        todo = store.add("Done")
        store.complete(todo.id)
        pending = store.list()
        assert len(pending) == 1
        assert pending[0].title == "Pending"

    def test_list_show_done_includes_all(self, store):
        store.add("Pending")
        todo = store.add("Done")
        store.complete(todo.id)
        all_todos = store.list(show_done=True)
        assert len(all_todos) == 2

    def test_list_no_file_returns_empty(self, store):
        assert not store.config.storage_path.exists()
        assert store.list() == []


class TestTodoStoreGet:
    def test_get_existing_todo(self, store):
        added = store.add("Findable")
        found = store.get(added.id)
        assert found is not None
        assert found.title == "Findable"

    def test_get_nonexistent_returns_none(self, store):
        assert store.get(999) is None

    def test_get_returns_correct_todo(self, store):
        store.add("First")
        second = store.add("Second")
        store.add("Third")
        found = store.get(second.id)
        assert found.title == "Second"


class TestTodoStoreComplete:
    def test_complete_marks_done(self, store):
        todo = store.add("Finish me")
        result = store.complete(todo.id)
        assert result is not None
        assert result.done is True

    def test_complete_persists(self, store):
        todo = store.add("Finish me")
        store.complete(todo.id)
        reloaded = store.get(todo.id)
        assert reloaded.done is True

    def test_complete_nonexistent_returns_none(self, store):
        assert store.complete(999) is None

    def test_complete_does_not_affect_others(self, store):
        t1 = store.add("First")
        t2 = store.add("Second")
        store.complete(t1.id)
        assert store.get(t2.id).done is False


class TestTodoStoreDelete:
    def test_delete_existing_returns_true(self, store):
        todo = store.add("Delete me")
        assert store.delete(todo.id) is True

    def test_delete_removes_from_list(self, store):
        todo = store.add("Delete me")
        store.delete(todo.id)
        assert store.get(todo.id) is None

    def test_delete_nonexistent_returns_false(self, store):
        assert store.delete(999) is False

    def test_delete_does_not_affect_others(self, store):
        t1 = store.add("Keep")
        t2 = store.add("Delete me")
        store.delete(t2.id)
        assert store.get(t1.id) is not None
        assert store.list(show_done=True) == [store.get(t1.id)]

    def test_delete_then_add_id_does_not_reuse(self, store):
        t1 = store.add("First")
        store.delete(t1.id)
        t2 = store.add("Second")
        assert t2.id > t1.id
