"""Tests for batch todo operations: mark_done_batch, mark_done_overdue,
delete_batch, delete_completed."""

import pytest

import todo


@pytest.fixture(autouse=True)
def isolate_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))


def _seed(*titles) -> list[dict]:
    return [todo.add_todo(t) for t in titles]


# ---------------------------------------------------------------------------
# mark_done_batch
# ---------------------------------------------------------------------------

class TestMarkDoneBatch:
    def test_all_found_returns_all_completed(self):
        items = _seed("A", "B", "C")
        ids = [t["id"] for t in items]
        completed, missing = todo.mark_done_batch(ids)
        assert len(completed) == 3
        assert missing == []

    def test_all_found_sets_done_true(self):
        items = _seed("A", "B")
        ids = [t["id"] for t in items]
        todo.mark_done_batch(ids)
        for t in items:
            assert todo.get_todo(t["id"])["done"] is True

    def test_all_found_single_write_persists(self):
        items = _seed("A", "B")
        ids = [t["id"] for t in items]
        todo.mark_done_batch(ids)
        assert all(todo.get_todo(i["id"])["done"] for i in items)

    def test_partial_missing_returns_found_and_missing(self):
        items = _seed("A", "B")
        completed, missing = todo.mark_done_batch([items[0]["id"], 9999])
        assert len(completed) == 1
        assert completed[0]["id"] == items[0]["id"]
        assert missing == [9999]

    def test_partial_missing_marks_found_ones_done(self):
        items = _seed("A", "B")
        todo.mark_done_batch([items[0]["id"], 9999])
        assert todo.get_todo(items[0]["id"])["done"] is True
        assert todo.get_todo(items[1]["id"])["done"] is False

    def test_all_missing_returns_empty_completed(self):
        _seed("A")
        completed, missing = todo.mark_done_batch([9998, 9999])
        assert completed == []
        assert missing == [9998, 9999]

    def test_all_missing_does_not_write(self, tmp_path, monkeypatch):
        path = tmp_path / "todos.json"
        monkeypatch.setenv("TODO_FILE", str(path))
        todo.add_todo("A")
        mtime_before = path.stat().st_mtime
        todo.mark_done_batch([9999])
        assert path.stat().st_mtime == mtime_before

    def test_missing_ids_sorted(self):
        _seed("A")
        _, missing = todo.mark_done_batch([30, 10, 20])
        assert missing == [10, 20, 30]

    def test_empty_ids_list(self):
        _seed("A")
        completed, missing = todo.mark_done_batch([])
        assert completed == []
        assert missing == []


# ---------------------------------------------------------------------------
# mark_done_overdue
# ---------------------------------------------------------------------------

class TestMarkDoneOverdue:
    def test_past_due_date_marked_done(self):
        t = todo.add_todo("Overdue")
        # inject a past due_date directly
        import json, os
        path = os.environ["TODO_FILE"]
        data = json.loads(open(path).read())
        for item in data["todos"]:
            if item["id"] == t["id"]:
                item["due_date"] = "2000-01-01"
        open(path, "w").write(json.dumps(data))

        result = todo.mark_done_overdue()
        assert len(result) == 1
        assert result[0]["id"] == t["id"]
        assert todo.get_todo(t["id"])["done"] is True

    def test_future_due_date_not_marked(self):
        t = todo.add_todo("Future")
        import json, os
        path = os.environ["TODO_FILE"]
        data = json.loads(open(path).read())
        for item in data["todos"]:
            if item["id"] == t["id"]:
                item["due_date"] = "2099-12-31"
        open(path, "w").write(json.dumps(data))

        result = todo.mark_done_overdue()
        assert result == []
        assert todo.get_todo(t["id"])["done"] is False

    def test_no_due_date_not_marked(self):
        todo.add_todo("No due date")
        result = todo.mark_done_overdue()
        assert result == []

    def test_already_done_skipped(self):
        t = todo.add_todo("Already done")
        todo.mark_done(t["id"])
        import json, os
        path = os.environ["TODO_FILE"]
        data = json.loads(open(path).read())
        for item in data["todos"]:
            if item["id"] == t["id"]:
                item["due_date"] = "2000-01-01"
        open(path, "w").write(json.dumps(data))

        result = todo.mark_done_overdue()
        assert result == []

    def test_mixed_returns_only_overdue(self):
        t_over = todo.add_todo("Overdue")
        t_future = todo.add_todo("Future")
        import json, os
        path = os.environ["TODO_FILE"]
        data = json.loads(open(path).read())
        for item in data["todos"]:
            if item["id"] == t_over["id"]:
                item["due_date"] = "2000-01-01"
            elif item["id"] == t_future["id"]:
                item["due_date"] = "2099-12-31"
        open(path, "w").write(json.dumps(data))

        result = todo.mark_done_overdue()
        assert len(result) == 1
        assert result[0]["id"] == t_over["id"]

    def test_empty_store_returns_empty(self):
        assert todo.mark_done_overdue() == []


# ---------------------------------------------------------------------------
# delete_batch
# ---------------------------------------------------------------------------

class TestDeleteBatch:
    def test_all_found_deletes_all(self):
        items = _seed("A", "B", "C")
        ids = [t["id"] for t in items]
        deleted, missing = todo.delete_batch(ids)
        assert len(deleted) == 3
        assert missing == []
        assert todo.list_todos(show_done=True) == []

    def test_partial_missing_deletes_found(self):
        items = _seed("A", "B")
        deleted, missing = todo.delete_batch([items[0]["id"], 9999])
        assert len(deleted) == 1
        assert deleted[0]["id"] == items[0]["id"]
        assert missing == [9999]
        assert todo.get_todo(items[1]["id"]) is not None

    def test_all_missing_returns_empty_deleted(self):
        _seed("A")
        deleted, missing = todo.delete_batch([9998, 9999])
        assert deleted == []
        assert missing == [9998, 9999]

    def test_all_missing_does_not_write(self, tmp_path, monkeypatch):
        path = tmp_path / "todos2.json"
        monkeypatch.setenv("TODO_FILE", str(path))
        todo.add_todo("A")
        mtime_before = path.stat().st_mtime
        todo.delete_batch([9999])
        assert path.stat().st_mtime == mtime_before

    def test_missing_ids_sorted(self):
        _seed("A")
        _, missing = todo.delete_batch([30, 10, 20])
        assert missing == [10, 20, 30]

    def test_empty_ids_list(self):
        _seed("A")
        deleted, missing = todo.delete_batch([])
        assert deleted == []
        assert missing == []


# ---------------------------------------------------------------------------
# delete_completed
# ---------------------------------------------------------------------------

class TestDeleteCompleted:
    def test_deletes_all_completed(self):
        items = _seed("A", "B", "C")
        for t in items:
            todo.mark_done(t["id"])
        deleted = todo.delete_completed()
        assert len(deleted) == 3
        assert todo.list_todos(show_done=True) == []

    def test_leaves_pending_intact(self):
        keep = todo.add_todo("Keep")
        remove = todo.add_todo("Remove")
        todo.mark_done(remove["id"])
        todo.delete_completed()
        assert todo.get_todo(keep["id"]) is not None
        assert todo.get_todo(remove["id"]) is None

    def test_no_completed_returns_empty(self):
        _seed("A", "B")
        result = todo.delete_completed()
        assert result == []

    def test_no_completed_does_not_write(self, tmp_path, monkeypatch):
        path = tmp_path / "todos3.json"
        monkeypatch.setenv("TODO_FILE", str(path))
        todo.add_todo("Pending")
        mtime_before = path.stat().st_mtime
        todo.delete_completed()
        assert path.stat().st_mtime == mtime_before

    def test_empty_store_returns_empty(self):
        assert todo.delete_completed() == []

    def test_returns_deleted_items(self):
        t = todo.add_todo("Remove me")
        todo.mark_done(t["id"])
        deleted = todo.delete_completed()
        assert len(deleted) == 1
        assert deleted[0]["title"] == "Remove me"
