"""Tests for subtask (parent_id) functionality."""

import pytest
import os

import todo
import formatter


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))


class TestAddTodoWithParent:
    def test_add_top_level_has_none_parent(self):
        item = todo.add_todo("Top level")
        assert item["parent_id"] is None

    def test_add_subtask_sets_parent_id(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        assert child["parent_id"] == parent["id"]

    def test_add_subtask_with_invalid_parent_raises(self):
        with pytest.raises(KeyError, match="not found"):
            todo.add_todo("Orphan", parent_id=999)

    def test_subtask_persists_parent_id(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        reloaded = todo.get_todo(child["id"])
        assert reloaded["parent_id"] == parent["id"]

    def test_add_subtask_of_subtask(self):
        grandparent = todo.add_todo("Grandparent")
        parent = todo.add_todo("Parent", parent_id=grandparent["id"])
        child = todo.add_todo("Child", parent_id=parent["id"])
        assert child["parent_id"] == parent["id"]


class TestListTodosHierarchical:
    def test_parent_appears_before_child(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        items = todo.list_todos()
        ids = [t["id"] for t in items]
        assert ids.index(parent["id"]) < ids.index(child["id"])

    def test_child_immediately_follows_parent(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        items = todo.list_todos()
        ids = [t["id"] for t in items]
        assert ids.index(child["id"]) == ids.index(parent["id"]) + 1

    def test_multiple_children_follow_parent(self):
        parent = todo.add_todo("Parent")
        c1 = todo.add_todo("Child 1", parent_id=parent["id"])
        c2 = todo.add_todo("Child 2", parent_id=parent["id"])
        items = todo.list_todos()
        ids = [t["id"] for t in items]
        parent_pos = ids.index(parent["id"])
        assert ids.index(c1["id"]) > parent_pos
        assert ids.index(c2["id"]) > parent_pos

    def test_top_level_siblings_keep_relative_order(self):
        t1 = todo.add_todo("First")
        t2 = todo.add_todo("Second")
        items = todo.list_todos()
        ids = [t["id"] for t in items]
        assert ids.index(t1["id"]) < ids.index(t2["id"])

    def test_list_excludes_done_subtasks_by_default(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        # Mark parent done — cascades to child.
        todo.mark_done(parent["id"])
        items = todo.list_todos()
        ids = [t["id"] for t in items]
        assert parent["id"] not in ids
        assert child["id"] not in ids

    def test_done_child_excluded_pending_parent_remains(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        todo.mark_done(child["id"])
        items = todo.list_todos()
        ids = [t["id"] for t in items]
        assert child["id"] not in ids
        assert parent["id"] in ids

    def test_list_all_includes_done_subtasks(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        todo.mark_done(parent["id"])
        items = todo.list_todos(show_done=True)
        ids = [t["id"] for t in items]
        assert parent["id"] in ids
        assert child["id"] in ids


class TestMarkDoneCascades:
    def test_marking_parent_done_marks_child_done(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        todo.mark_done(parent["id"])
        assert todo.get_todo(child["id"])["done"] is True

    def test_marking_parent_done_marks_self_done(self):
        parent = todo.add_todo("Parent")
        todo.add_todo("Child", parent_id=parent["id"])
        todo.mark_done(parent["id"])
        assert todo.get_todo(parent["id"])["done"] is True

    def test_marking_parent_done_marks_grandchild_done(self):
        gp = todo.add_todo("Grandparent")
        parent = todo.add_todo("Parent", parent_id=gp["id"])
        child = todo.add_todo("Child", parent_id=parent["id"])
        todo.mark_done(gp["id"])
        assert todo.get_todo(child["id"])["done"] is True

    def test_marking_child_done_does_not_mark_parent_done(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        todo.mark_done(child["id"])
        assert todo.get_todo(parent["id"])["done"] is False

    def test_marking_child_done_does_not_affect_sibling(self):
        parent = todo.add_todo("Parent")
        c1 = todo.add_todo("Child 1", parent_id=parent["id"])
        c2 = todo.add_todo("Child 2", parent_id=parent["id"])
        todo.mark_done(c1["id"])
        assert todo.get_todo(c2["id"])["done"] is False

    def test_mark_done_nonexistent_raises(self):
        with pytest.raises(KeyError):
            todo.mark_done(999)


class TestCollectSubtreeIds:
    def test_single_item(self):
        parent = todo.add_todo("Parent")
        todos = todo.load_todos()
        ids = todo._collect_subtree_ids(todos, parent["id"])
        assert ids == {parent["id"]}

    def test_parent_and_child(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        todos = todo.load_todos()
        ids = todo._collect_subtree_ids(todos, parent["id"])
        assert parent["id"] in ids
        assert child["id"] in ids

    def test_child_only_returns_child(self):
        parent = todo.add_todo("Parent")
        child = todo.add_todo("Child", parent_id=parent["id"])
        todos = todo.load_todos()
        ids = todo._collect_subtree_ids(todos, child["id"])
        assert ids == {child["id"]}
        assert parent["id"] not in ids


class TestFormatterSubtasks:
    def test_top_level_todo_no_indent(self):
        item = {"id": 1, "title": "Top", "done": False, "tags": [], "parent_id": None}
        result = formatter.format_todo(item)
        assert result.startswith("[ ] #")

    def test_subtask_indented_in_list(self):
        parent = {"id": 1, "title": "Parent", "done": False, "tags": [], "parent_id": None}
        child = {"id": 2, "title": "Child", "done": False, "tags": [], "parent_id": 1}
        result = formatter.format_todo_list([parent, child])
        lines = result.split("\n")
        assert "  " in lines[1]

    def test_top_level_not_indented_in_list(self):
        item = {"id": 1, "title": "Top", "done": False, "tags": [], "parent_id": None}
        result = formatter.format_todo_list([item])
        assert result.startswith("[ ] #")

    def test_detail_shows_parent_field(self):
        child = {"id": 2, "title": "Child", "done": False, "tags": [],
                 "parent_id": 1, "created_at": "2026-01-01T00:00:00+00:00"}
        result = formatter.format_todo_detail(child)
        assert "Parent:  #1" in result

    def test_detail_no_parent_field_for_top_level(self):
        item = {"id": 1, "title": "Top", "done": False, "tags": [],
                "parent_id": None, "created_at": "2026-01-01T00:00:00+00:00"}
        result = formatter.format_todo_detail(item)
        assert "Parent:" not in result
