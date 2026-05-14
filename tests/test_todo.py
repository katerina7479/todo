import pytest

import todo


@pytest.fixture(autouse=True)
def isolate_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))


class TestAddTodo:
    def test_returns_dict(self):
        item = todo.add_todo("Buy milk")
        assert isinstance(item, dict)

    def test_title_set(self):
        item = todo.add_todo("Buy milk")
        assert item["title"] == "Buy milk"

    def test_done_is_false(self):
        item = todo.add_todo("Buy milk")
        assert item["done"] is False

    def test_id_starts_at_one(self):
        item = todo.add_todo("First")
        assert item["id"] == 1

    def test_ids_increment(self):
        t1 = todo.add_todo("First")
        t2 = todo.add_todo("Second")
        assert t2["id"] == t1["id"] + 1

    def test_created_at_present(self):
        item = todo.add_todo("Buy milk")
        assert "created_at" in item

    def test_persists_to_file(self, tmp_path):
        todo.add_todo("Persisted")
        assert (tmp_path / "todos.json").exists()


class TestListTodos:
    def test_empty_store_returns_empty_list(self):
        assert todo.list_todos() == []

    def test_returns_pending_by_default(self):
        todo.add_todo("Pending")
        items = todo.list_todos()
        assert len(items) == 1

    def test_excludes_done_by_default(self):
        t = todo.add_todo("Done item")
        todo.mark_done(t["id"])
        assert todo.list_todos() == []

    def test_show_done_includes_completed(self):
        t = todo.add_todo("Done item")
        todo.mark_done(t["id"])
        assert len(todo.list_todos(show_done=True)) == 1

    def test_show_done_includes_all(self):
        todo.add_todo("Pending")
        t = todo.add_todo("Done")
        todo.mark_done(t["id"])
        assert len(todo.list_todos(show_done=True)) == 2

    def test_returns_list_of_dicts(self):
        todo.add_todo("Item")
        items = todo.list_todos()
        assert isinstance(items, list)
        assert isinstance(items[0], dict)


class TestGetTodo:
    def test_returns_correct_todo(self):
        added = todo.add_todo("Findable")
        found = todo.get_todo(added["id"])
        assert found is not None
        assert found["title"] == "Findable"

    def test_nonexistent_returns_none(self):
        assert todo.get_todo(999) is None

    def test_returns_correct_item_among_multiple(self):
        todo.add_todo("First")
        second = todo.add_todo("Second")
        todo.add_todo("Third")
        found = todo.get_todo(second["id"])
        assert found["title"] == "Second"


class TestMarkDone:
    def test_sets_done_true(self):
        t = todo.add_todo("Finish me")
        result = todo.mark_done(t["id"])
        assert result["done"] is True

    def test_persists(self):
        t = todo.add_todo("Finish me")
        todo.mark_done(t["id"])
        assert todo.get_todo(t["id"])["done"] is True

    def test_not_found_raises_key_error(self):
        with pytest.raises(KeyError):
            todo.mark_done(999)

    def test_does_not_affect_other_items(self):
        t1 = todo.add_todo("First")
        t2 = todo.add_todo("Second")
        todo.mark_done(t1["id"])
        assert todo.get_todo(t2["id"])["done"] is False


class TestDeleteTodo:
    def test_returns_deleted_item(self):
        t = todo.add_todo("Delete me")
        removed = todo.delete_todo(t["id"])
        assert removed["title"] == "Delete me"

    def test_removes_from_store(self):
        t = todo.add_todo("Delete me")
        todo.delete_todo(t["id"])
        assert todo.get_todo(t["id"]) is None

    def test_not_found_raises_key_error(self):
        with pytest.raises(KeyError):
            todo.delete_todo(999)

    def test_does_not_affect_other_items(self):
        t1 = todo.add_todo("Keep")
        t2 = todo.add_todo("Delete me")
        todo.delete_todo(t2["id"])
        assert todo.get_todo(t1["id"]) is not None

    def test_ids_not_reused_after_delete(self):
        t1 = todo.add_todo("First")
        todo.delete_todo(t1["id"])
        t2 = todo.add_todo("Second")
        assert t2["id"] > t1["id"]
