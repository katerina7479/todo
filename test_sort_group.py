"""Tests for --sort-by and --group-by on the list command (pb-30)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import formatter
import todo as todo_module


class Base(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["TODO_FILE"] = str(Path(self._tmpdir.name) / "todos.json")

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        self._tmpdir.cleanup()

    def _run_list(self, argv):
        import main as main_mod
        parser = main_mod.build_parser()
        args = parser.parse_args(["list"] + argv)
        return args.func(args)


# ---------------------------------------------------------------------------
# sort_todos
# ---------------------------------------------------------------------------

class TestSortByTitle(Base):
    def test_sorts_ascending(self):
        todo_module.add_todo("Zebra")
        todo_module.add_todo("Apple")
        todo_module.add_todo("Mango")
        items = todo_module.list_todos()
        result = todo_module.sort_todos(items, "title")
        self.assertEqual([t["title"] for t in result], ["Apple", "Mango", "Zebra"])

    def test_case_insensitive(self):
        todo_module.add_todo("banana")
        todo_module.add_todo("Apple")
        items = todo_module.list_todos()
        result = todo_module.sort_todos(items, "title")
        self.assertEqual(result[0]["title"], "Apple")

    def test_stable_for_equal_keys(self):
        todo_module.add_todo("Same")
        todo_module.add_todo("Same")
        items = todo_module.list_todos()
        result = todo_module.sort_todos(items, "title")
        self.assertEqual([t["id"] for t in result], [1, 2])


class TestSortByCreatedAt(Base):
    def test_sorts_chronologically(self):
        todo_module.add_todo("First")
        todo_module.add_todo("Second")
        todo_module.add_todo("Third")
        items = todo_module.list_todos()
        result = todo_module.sort_todos(items, "created_at")
        self.assertEqual([t["title"] for t in result], ["First", "Second", "Third"])

    def test_missing_created_at_sorts_last(self):
        todo_module.add_todo("Normal")
        items = todo_module.list_todos()
        items.append({"id": 99, "title": "No date", "done": False, "tags": []})
        result = todo_module.sort_todos(items, "created_at")
        self.assertEqual(result[-1]["title"], "No date")


class TestSortByOptionalField(Base):
    def test_missing_priority_sorts_last(self):
        todo_module.add_todo("No priority")
        items = todo_module.list_todos()
        items[0]["priority"] = None
        extra = {"id": 2, "title": "Has priority", "done": False,
                 "tags": [], "priority": "high"}
        result = todo_module.sort_todos([items[0], extra], "priority")
        self.assertEqual(result[0]["title"], "Has priority")

    def test_missing_due_date_sorts_last(self):
        has_date = {"id": 1, "title": "Due soon", "done": False,
                    "tags": [], "due_date": "2026-01-01"}
        no_date = {"id": 2, "title": "No date", "done": False, "tags": []}
        result = todo_module.sort_todos([no_date, has_date], "due_date")
        self.assertEqual(result[0]["title"], "Due soon")
        self.assertEqual(result[1]["title"], "No date")


# ---------------------------------------------------------------------------
# group_todos
# ---------------------------------------------------------------------------

class TestGroupByTag(Base):
    def test_groups_by_each_tag(self):
        todo_module.add_todo("Work task", tags=["work"])
        todo_module.add_todo("Home task", tags=["home"])
        items = todo_module.list_todos()
        groups = dict(todo_module.group_todos(items, "tag"))
        self.assertIn("work", groups)
        self.assertIn("home", groups)
        self.assertEqual(groups["work"][0]["title"], "Work task")

    def test_multi_tag_todo_appears_in_each_group(self):
        todo_module.add_todo("Both", tags=["work", "urgent"])
        items = todo_module.list_todos()
        groups = dict(todo_module.group_todos(items, "tag"))
        self.assertIn("work", groups)
        self.assertIn("urgent", groups)
        self.assertEqual(len(groups["work"]), 1)
        self.assertEqual(len(groups["urgent"]), 1)

    def test_untagged_goes_to_no_tag(self):
        todo_module.add_todo("Untagged")
        items = todo_module.list_todos()
        groups = dict(todo_module.group_todos(items, "tag"))
        self.assertIn("(no tag)", groups)

    def test_groups_sorted_alphabetically(self):
        todo_module.add_todo("Z task", tags=["zebra"])
        todo_module.add_todo("A task", tags=["apple"])
        items = todo_module.list_todos()
        labels = [label for label, _ in todo_module.group_todos(items, "tag")]
        self.assertEqual(labels, sorted(labels))

    def test_empty_list_returns_no_groups(self):
        groups = todo_module.group_todos([], "tag")
        self.assertEqual(groups, [])


class TestGroupByOptionalField(Base):
    def test_group_by_priority(self):
        high = {"id": 1, "title": "High", "done": False, "tags": [], "priority": "high"}
        low = {"id": 2, "title": "Low", "done": False, "tags": [], "priority": "low"}
        groups = dict(todo_module.group_todos([high, low], "priority"))
        self.assertIn("high", groups)
        self.assertIn("low", groups)

    def test_missing_priority_goes_to_none(self):
        todo_module.add_todo("No priority")
        items = todo_module.list_todos()
        groups = dict(todo_module.group_todos(items, "priority"))
        self.assertIn("(none)", groups)

    def test_group_by_due_date(self):
        a = {"id": 1, "title": "A", "done": False, "tags": [], "due_date": "2026-06-01"}
        b = {"id": 2, "title": "B", "done": False, "tags": []}
        groups = dict(todo_module.group_todos([a, b], "due_date"))
        self.assertIn("2026-06-01", groups)
        self.assertIn("(none)", groups)


# ---------------------------------------------------------------------------
# format_todo_groups
# ---------------------------------------------------------------------------

class TestFormatTodoGroups(Base):
    def test_empty_returns_no_todos(self):
        self.assertEqual(formatter.format_todo_groups([]), "No todos found.")

    def test_header_per_group(self):
        groups = [
            ("work", [{"id": 1, "title": "Task", "done": False, "tags": []}]),
            ("home", [{"id": 2, "title": "Chore", "done": False, "tags": []}]),
        ]
        output = formatter.format_todo_groups(groups)
        self.assertIn("=== work ===", output)
        self.assertIn("=== home ===", output)
        self.assertIn("Task", output)
        self.assertIn("Chore", output)

    def test_groups_separated_by_blank_line(self):
        groups = [
            ("a", [{"id": 1, "title": "T1", "done": False, "tags": []}]),
            ("b", [{"id": 2, "title": "T2", "done": False, "tags": []}]),
        ]
        output = formatter.format_todo_groups(groups)
        self.assertIn("\n\n", output)


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestListCLI(Base):
    def test_sort_by_title_flag(self):
        todo_module.add_todo("Zebra")
        todo_module.add_todo("Apple")
        # just verify it runs without error
        result = self._run_list(["--sort-by", "title"])
        self.assertEqual(result, 0)

    def test_group_by_tag_flag(self):
        todo_module.add_todo("Task", tags=["work"])
        result = self._run_list(["--group-by", "tag"])
        self.assertEqual(result, 0)

    def test_sort_and_group_combined(self):
        todo_module.add_todo("Zebra", tags=["work"])
        todo_module.add_todo("Apple", tags=["work"])
        result = self._run_list(["--sort-by", "title", "--group-by", "tag"])
        self.assertEqual(result, 0)

    def test_no_flags_unchanged(self):
        todo_module.add_todo("Task")
        result = self._run_list([])
        self.assertEqual(result, 0)

    def test_invalid_sort_by_rejected(self):
        parser = __import__("main").build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["list", "--sort-by", "invalid"])

    def test_invalid_group_by_rejected(self):
        parser = __import__("main").build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["list", "--group-by", "invalid"])


if __name__ == "__main__":
    unittest.main()
