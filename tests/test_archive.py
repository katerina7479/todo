"""Tests for the archive feature (pb-29)."""

import pytest

import todo
import formatter


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))
    monkeypatch.setenv("TODO_ARCHIVE_FILE", str(tmp_path / "archive.json"))


class TestArchiveDone:
    def test_archive_returns_count_of_moved_todos(self):
        todo.add_todo("Keep")
        t = todo.add_todo("Done one")
        todo.mark_done(t["id"])
        assert todo.archive_done() == 1

    def test_archive_moves_done_items_out_of_active_store(self):
        t = todo.add_todo("Finish me")
        todo.mark_done(t["id"])
        todo.archive_done()
        assert todo.get_todo(t["id"]) is None

    def test_archive_leaves_pending_items_in_active_store(self):
        keep = todo.add_todo("Keep me")
        done = todo.add_todo("Done")
        todo.mark_done(done["id"])
        todo.archive_done()
        assert todo.get_todo(keep["id"]) is not None

    def test_archive_with_no_done_returns_zero(self):
        todo.add_todo("Pending")
        assert todo.archive_done() == 0

    def test_archive_with_no_done_leaves_store_unchanged(self):
        t = todo.add_todo("Pending")
        todo.archive_done()
        assert todo.get_todo(t["id"]) is not None

    def test_archive_multiple_done_items(self):
        for i in range(3):
            t = todo.add_todo(f"Task {i}")
            todo.mark_done(t["id"])
        todo.add_todo("Pending")
        count = todo.archive_done()
        assert count == 3
        assert len(todo.list_todos(show_done=True)) == 1

    def test_archive_is_idempotent_on_second_call(self):
        t = todo.add_todo("Done")
        todo.mark_done(t["id"])
        todo.archive_done()
        assert todo.archive_done() == 0

    def test_archived_items_appear_in_load_archived(self):
        t = todo.add_todo("Done")
        todo.mark_done(t["id"])
        todo.archive_done()
        archived = todo.load_archived()
        assert any(a["id"] == t["id"] for a in archived)

    def test_archived_items_accumulate_across_calls(self):
        t1 = todo.add_todo("First")
        todo.mark_done(t1["id"])
        todo.archive_done()
        t2 = todo.add_todo("Second")
        todo.mark_done(t2["id"])
        todo.archive_done()
        archived = todo.load_archived()
        ids = [a["id"] for a in archived]
        assert t1["id"] in ids
        assert t2["id"] in ids

    def test_archived_items_have_archived_flag(self):
        t = todo.add_todo("Done")
        todo.mark_done(t["id"])
        todo.archive_done()
        archived = todo.load_archived()
        assert all(a.get("archived") is True for a in archived)


class TestLoadArchived:
    def test_load_archived_empty_when_no_archive_file(self):
        assert todo.load_archived() == []

    def test_load_archived_returns_previously_archived(self):
        t = todo.add_todo("Done")
        todo.mark_done(t["id"])
        todo.archive_done()
        result = todo.load_archived()
        assert len(result) == 1
        assert result[0]["title"] == "Done"


class TestListTodosWithArchived:
    def test_list_does_not_include_archived_by_default(self):
        t = todo.add_todo("Done")
        todo.mark_done(t["id"])
        todo.archive_done()
        items = todo.list_todos(show_done=True)
        ids = [i["id"] for i in items]
        assert t["id"] not in ids

    def test_list_include_archived_appends_archived_items(self):
        t = todo.add_todo("Done")
        todo.mark_done(t["id"])
        todo.archive_done()
        items = todo.list_todos(include_archived=True)
        ids = [i["id"] for i in items]
        assert t["id"] in ids

    def test_list_include_archived_keeps_pending_items(self):
        pending = todo.add_todo("Pending")
        done = todo.add_todo("Done")
        todo.mark_done(done["id"])
        todo.archive_done()
        items = todo.list_todos(include_archived=True)
        ids = [i["id"] for i in items]
        assert pending["id"] in ids

    def test_list_include_archived_with_tag_filter(self):
        t1 = todo.add_todo("Tagged done", tags=["work"])
        t2 = todo.add_todo("Untagged done")
        todo.mark_done(t1["id"])
        todo.mark_done(t2["id"])
        todo.archive_done()
        items = todo.list_todos(tag="work", include_archived=True)
        ids = [i["id"] for i in items]
        assert t1["id"] in ids
        assert t2["id"] not in ids


class TestSearchTodosWithArchived:
    def test_search_does_not_include_archived_by_default(self):
        t = todo.add_todo("Archived item")
        todo.mark_done(t["id"])
        todo.archive_done()
        results = todo.search_todos("archived")
        assert not any(r["id"] == t["id"] for r in results)

    def test_search_include_archived_finds_archived_items(self):
        t = todo.add_todo("Special done task")
        todo.mark_done(t["id"])
        todo.archive_done()
        results = todo.search_todos("special", include_archived=True)
        assert any(r["id"] == t["id"] for r in results)

    def test_search_include_archived_still_finds_active_items(self):
        active = todo.add_todo("Active special task")
        done = todo.add_todo("Done special task")
        todo.mark_done(done["id"])
        todo.archive_done()
        results = todo.search_todos("special", include_archived=True)
        ids = [r["id"] for r in results]
        assert active["id"] in ids
        assert done["id"] in ids


class TestFormatterArchived:
    def test_format_todo_shows_archived_label(self):
        item = {"id": 1, "title": "Old task", "done": True, "tags": [], "archived": True}
        result = formatter.format_todo(item)
        assert "[archived]" in result
        assert "Old task" in result

    def test_format_todo_no_archived_label_for_active(self):
        item = {"id": 1, "title": "Active", "done": False, "tags": []}
        result = formatter.format_todo(item)
        assert "[archived]" not in result

    def test_format_todo_detail_shows_archived_status(self):
        item = {
            "id": 1, "title": "Old", "done": True, "tags": [],
            "archived": True, "created_at": "2026-01-01T00:00:00+00:00",
        }
        result = formatter.format_todo_detail(item)
        assert "Status:  archived" in result
