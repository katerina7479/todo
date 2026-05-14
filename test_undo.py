"""Tests for undo.py and todo.undo_last()."""

import pytest

import todo
import undo


@pytest.fixture(autouse=True)
def isolate_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))


# ---------------------------------------------------------------------------
# Nothing to undo
# ---------------------------------------------------------------------------

class TestNothingToUndo:
    def test_empty_journal_raises(self):
        with pytest.raises(ValueError, match="Nothing to undo"):
            todo.undo_last()

    def test_add_does_not_write_journal(self):
        todo.add_todo("New item")
        assert undo.load() is None

    def test_undo_after_add_raises(self):
        todo.add_todo("New item")
        with pytest.raises(ValueError, match="Nothing to undo"):
            todo.undo_last()


# ---------------------------------------------------------------------------
# Undo done
# ---------------------------------------------------------------------------

class TestUndoDone:
    def test_restores_done_to_false(self):
        t = todo.add_todo("Finish me")
        todo.mark_done(t["id"])
        assert todo.get_todo(t["id"])["done"] is True

        action, restored = todo.undo_last()
        assert action == "done"
        assert todo.get_todo(t["id"])["done"] is False

    def test_returns_correct_action_and_todo(self):
        t = todo.add_todo("Task")
        todo.mark_done(t["id"])
        action, restored = todo.undo_last()
        assert action == "done"
        assert restored["id"] == t["id"]
        assert restored["title"] == t["title"]

    def test_journal_cleared_after_undo(self):
        t = todo.add_todo("Task")
        todo.mark_done(t["id"])
        todo.undo_last()
        assert undo.load() is None

    def test_persists_restored_state(self):
        t = todo.add_todo("Task")
        todo.mark_done(t["id"])
        todo.undo_last()
        # reload from disk — must still be pending
        assert todo.get_todo(t["id"])["done"] is False


# ---------------------------------------------------------------------------
# Undo delete
# ---------------------------------------------------------------------------

class TestUndoDelete:
    def test_reinserts_deleted_todo(self):
        t = todo.add_todo("Gone")
        todo.delete_todo(t["id"])
        assert todo.get_todo(t["id"]) is None

        action, restored = todo.undo_last()
        assert action == "delete"
        assert todo.get_todo(t["id"]) is not None

    def test_restored_title_matches(self):
        t = todo.add_todo("Gone")
        todo.delete_todo(t["id"])
        _, restored = todo.undo_last()
        assert restored["title"] == "Gone"

    def test_reinserts_in_id_order_middle(self):
        t1 = todo.add_todo("First")
        t2 = todo.add_todo("Middle")
        t3 = todo.add_todo("Last")

        todo.delete_todo(t2["id"])
        todo.undo_last()

        ids = [t["id"] for t in todo.list_todos(show_done=True)]
        assert ids == sorted(ids), f"Expected sorted ids, got {ids}"
        assert t2["id"] in ids

    def test_reinserts_at_end_when_highest_id(self):
        t1 = todo.add_todo("First")
        t2 = todo.add_todo("Second")
        todo.delete_todo(t2["id"])
        todo.undo_last()
        ids = [t["id"] for t in todo.list_todos(show_done=True)]
        assert ids[-1] == t2["id"]

    def test_reinserts_at_start_when_lowest_id(self):
        t1 = todo.add_todo("First")
        t2 = todo.add_todo("Second")
        todo.delete_todo(t1["id"])
        todo.undo_last()
        ids = [t["id"] for t in todo.list_todos(show_done=True)]
        assert ids[0] == t1["id"]

    def test_journal_cleared_after_undo(self):
        t = todo.add_todo("Gone")
        todo.delete_todo(t["id"])
        todo.undo_last()
        assert undo.load() is None


# ---------------------------------------------------------------------------
# Undo edit
# ---------------------------------------------------------------------------

class TestUndoEdit:
    def test_restores_previous_title(self):
        t = todo.add_todo("Original title")
        todo.update_todo(t["id"], title="New title")
        assert todo.get_todo(t["id"])["title"] == "New title"

        todo.undo_last()
        assert todo.get_todo(t["id"])["title"] == "Original title"

    def test_restores_previous_priority(self):
        t = todo.add_todo("Task")
        todo.update_todo(t["id"], priority="high")
        todo.undo_last()
        assert "priority" not in todo.get_todo(t["id"]) or todo.get_todo(t["id"]).get("priority") != "high"

    def test_restores_all_fields_to_snapshot(self):
        t = todo.add_todo("Task")
        snapshot = dict(todo.get_todo(t["id"]))
        todo.update_todo(t["id"], title="Changed", priority="low")
        todo.undo_last()
        current = todo.get_todo(t["id"])
        assert current["title"] == snapshot["title"]

    def test_returns_correct_action(self):
        t = todo.add_todo("Task")
        todo.update_todo(t["id"], title="New")
        action, _ = todo.undo_last()
        assert action == "edit"

    def test_journal_cleared_after_undo(self):
        t = todo.add_todo("Task")
        todo.update_todo(t["id"], title="New")
        todo.undo_last()
        assert undo.load() is None


# ---------------------------------------------------------------------------
# Double undo
# ---------------------------------------------------------------------------

class TestDoubleUndo:
    def test_second_undo_raises_after_done(self):
        t = todo.add_todo("Task")
        todo.mark_done(t["id"])
        todo.undo_last()
        with pytest.raises(ValueError, match="Nothing to undo"):
            todo.undo_last()

    def test_second_undo_raises_after_delete(self):
        t = todo.add_todo("Task")
        todo.delete_todo(t["id"])
        todo.undo_last()
        with pytest.raises(ValueError, match="Nothing to undo"):
            todo.undo_last()

    def test_second_undo_raises_after_edit(self):
        t = todo.add_todo("Task")
        todo.update_todo(t["id"], title="New")
        todo.undo_last()
        with pytest.raises(ValueError, match="Nothing to undo"):
            todo.undo_last()

    def test_new_action_overwrites_journal(self):
        t1 = todo.add_todo("First")
        t2 = todo.add_todo("Second")
        todo.mark_done(t1["id"])
        todo.mark_done(t2["id"])  # overwrites journal
        action, restored = todo.undo_last()
        assert restored["id"] == t2["id"]  # only last action undone
