"""Tests for the notes field feature (pb-27)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))

import formatter
import todo as todo_module


class NotesBase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._store = Path(self._tmpdir.name) / "todos.json"
        os.environ["TODO_FILE"] = str(self._store)

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        self._tmpdir.cleanup()


class TestAddTodoWithNotes(NotesBase):
    def test_notes_stored_when_provided(self):
        item = todo_module.add_todo("Buy milk", notes="Get 2%.\nCheck expiry.")
        self.assertEqual(item["notes"], "Get 2%.\nCheck expiry.")

    def test_notes_empty_by_default(self):
        item = todo_module.add_todo("Simple task")
        self.assertEqual(item["notes"], "")

    def test_notes_persisted(self):
        todo_module.add_todo("Task A", notes="Some notes here.")
        loaded = todo_module.get_todo(1)
        self.assertEqual(loaded["notes"], "Some notes here.")

    def test_notes_multiline(self):
        notes = "Line one\nLine two\nLine three"
        todo_module.add_todo("Multi", notes=notes)
        self.assertEqual(todo_module.get_todo(1)["notes"], notes)


class TestUpdateNotes(NotesBase):
    def test_update_sets_new_notes(self):
        todo_module.add_todo("Task")
        updated = todo_module.update_notes(1, "New notes text.")
        self.assertEqual(updated["notes"], "New notes text.")

    def test_update_persists(self):
        todo_module.add_todo("Task")
        todo_module.update_notes(1, "Persisted notes.")
        self.assertEqual(todo_module.get_todo(1)["notes"], "Persisted notes.")

    def test_update_overwrites_existing_notes(self):
        todo_module.add_todo("Task", notes="Old notes.")
        todo_module.update_notes(1, "New notes.")
        self.assertEqual(todo_module.get_todo(1)["notes"], "New notes.")

    def test_update_missing_id_raises(self):
        with self.assertRaises(ValueError):
            todo_module.update_notes(99, "Anything")

    def test_update_clears_notes_with_empty_string(self):
        todo_module.add_todo("Task", notes="Some notes.")
        todo_module.update_notes(1, "")
        self.assertEqual(todo_module.get_todo(1)["notes"], "")


class TestFormatTodoDetail(NotesBase):
    def test_show_omits_notes_section_when_empty(self):
        todo_module.add_todo("No notes task")
        item = todo_module.get_todo(1)
        detail = formatter.format_todo_detail(item)
        self.assertNotIn("Notes:", detail)

    def test_show_displays_notes_when_present(self):
        todo_module.add_todo("Task", notes="Important detail.")
        item = todo_module.get_todo(1)
        detail = formatter.format_todo_detail(item)
        self.assertIn("Notes:", detail)
        self.assertIn("Important detail.", detail)

    def test_show_displays_multiline_notes(self):
        todo_module.add_todo("Task", notes="Line 1\nLine 2")
        item = todo_module.get_todo(1)
        detail = formatter.format_todo_detail(item)
        self.assertIn("Line 1", detail)
        self.assertIn("Line 2", detail)

    def test_show_omits_notes_for_legacy_todo_without_field(self):
        """Todos created before notes field was added should not break show."""
        todo_module.add_todo("Old task")
        item = todo_module.get_todo(1)
        item.pop("notes", None)  # simulate legacy record
        detail = formatter.format_todo_detail(item)
        self.assertNotIn("Notes:", detail)


class TestEditorIntegration(NotesBase):
    """Test that cmd_add and cmd_edit correctly invoke the editor module."""

    def _run_cmd(self, argv):
        import main as main_mod
        parser = main_mod.build_parser()
        args = parser.parse_args(argv)
        return args.func(args)

    def test_add_without_notes_flag_skips_editor(self):
        with mock.patch("editor.open_editor") as mock_editor:
            self._run_cmd(["add", "Task without notes"])
        mock_editor.assert_not_called()
        item = todo_module.get_todo(1)
        self.assertEqual(item["notes"], "")

    def test_add_with_notes_flag_calls_editor(self):
        with mock.patch("editor.open_editor", return_value="Editor content.") as mock_editor:
            self._run_cmd(["add", "Task with notes", "--notes"])
        mock_editor.assert_called_once_with()
        item = todo_module.get_todo(1)
        self.assertEqual(item["notes"], "Editor content.")

    def test_edit_notes_calls_editor_with_existing_notes(self):
        todo_module.add_todo("Existing task", notes="Original notes.")
        with mock.patch("editor.open_editor", return_value="Updated notes.") as mock_editor:
            self._run_cmd(["edit", "1", "--notes"])
        mock_editor.assert_called_once_with(initial="Original notes.")
        self.assertEqual(todo_module.get_todo(1)["notes"], "Updated notes.")

    def test_edit_without_notes_flag_returns_error(self):
        todo_module.add_todo("Task")
        result = self._run_cmd(["edit", "1"])
        self.assertEqual(result, 1)

    def test_edit_nonexistent_id_returns_error(self):
        with mock.patch("editor.open_editor", return_value="Notes"):
            result = self._run_cmd(["edit", "99", "--notes"])
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
