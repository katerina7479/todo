"""Tests for the completions subcommand (pb-33)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import completions as completions_mod
import todo as todo_module


class CompletionsBase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["TODO_FILE"] = str(Path(self._tmpdir.name) / "todos.json")

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        self._tmpdir.cleanup()

    def _run(self, argv):
        import main as main_mod
        parser = main_mod.build_parser()
        args = parser.parse_args(argv)
        return args.func(args)


# ---------------------------------------------------------------------------
# Dynamic helpers
# ---------------------------------------------------------------------------

class TestGetIds(CompletionsBase):
    def test_empty_store(self):
        self.assertEqual(completions_mod.get_ids(), [])

    def test_returns_all_ids_as_strings(self):
        todo_module.add_todo("A")
        todo_module.add_todo("B")
        self.assertEqual(completions_mod.get_ids(), ["1", "2"])

    def test_includes_done_todos(self):
        todo_module.add_todo("Task")
        todo_module.mark_done(1)
        self.assertIn("1", completions_mod.get_ids())

    def test_ids_match_store_order(self):
        todo_module.add_todo("First")
        todo_module.add_todo("Second")
        todo_module.add_todo("Third")
        self.assertEqual(completions_mod.get_ids(), ["1", "2", "3"])


class TestGetTags(CompletionsBase):
    def test_empty_store(self):
        self.assertEqual(completions_mod.get_tags(), [])

    def test_returns_unique_sorted_tags(self):
        todo_module.add_todo("A", tags=["work", "urgent"])
        todo_module.add_todo("B", tags=["home", "work"])
        self.assertEqual(completions_mod.get_tags(), ["home", "urgent", "work"])

    def test_deduplicates_tags(self):
        todo_module.add_todo("A", tags=["work"])
        todo_module.add_todo("B", tags=["work"])
        self.assertEqual(completions_mod.get_tags(), ["work"])

    def test_no_tags_returns_empty(self):
        todo_module.add_todo("Untagged")
        self.assertEqual(completions_mod.get_tags(), [])


# ---------------------------------------------------------------------------
# Script content
# ---------------------------------------------------------------------------

class TestBashScript(CompletionsBase):
    def setUp(self):
        super().setUp()
        self._script = completions_mod.bash_script()

    def test_contains_complete_directive(self):
        self.assertIn("complete -F _todo_completions todo", self._script)

    def test_contains_all_subcommands(self):
        for cmd in ("add", "list", "done", "delete", "show", "search", "completions"):
            self.assertIn(cmd, self._script)

    def test_references_list_ids(self):
        self.assertIn("--list-ids", self._script)

    def test_references_list_tags(self):
        self.assertIn("--list-tags", self._script)

    def test_custom_prog_name(self):
        script = completions_mod.bash_script(prog="mytodo")
        self.assertIn("complete -F _todo_completions mytodo", script)
        self.assertIn("mytodo completions --list-ids", script)

    def test_id_completion_for_done(self):
        self.assertIn("done|delete|show", self._script)

    def test_tag_completion_for_list(self):
        self.assertIn("--tag", self._script)


class TestZshScript(CompletionsBase):
    def setUp(self):
        super().setUp()
        self._script = completions_mod.zsh_script()

    def test_contains_compdef(self):
        self.assertIn("#compdef todo", self._script)

    def test_contains_all_subcommands(self):
        for cmd in ("add", "list", "done", "delete", "show", "search", "completions"):
            self.assertIn(cmd, self._script)

    def test_references_list_ids(self):
        self.assertIn("--list-ids", self._script)

    def test_references_list_tags(self):
        self.assertIn("--list-tags", self._script)

    def test_custom_prog_name(self):
        script = completions_mod.zsh_script(prog="mytodo")
        self.assertIn("#compdef mytodo", script)
        self.assertIn("mytodo completions --list-ids", script)


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestCompletionsCLI(CompletionsBase):
    def test_bash_subcommand_exits_zero(self):
        result = self._run(["completions", "bash"])
        self.assertEqual(result, 0)

    def test_zsh_subcommand_exits_zero(self):
        result = self._run(["completions", "zsh"])
        self.assertEqual(result, 0)

    def test_no_shell_returns_error(self):
        result = self._run(["completions"])
        self.assertEqual(result, 1)

    def test_list_ids_flag(self):
        todo_module.add_todo("Task")
        result = self._run(["completions", "--list-ids"])
        self.assertEqual(result, 0)

    def test_list_tags_flag(self):
        todo_module.add_todo("Task", tags=["work"])
        result = self._run(["completions", "--list-tags"])
        self.assertEqual(result, 0)

    def test_list_ids_takes_priority_over_shell(self):
        todo_module.add_todo("X")
        # --list-ids should work even when shell positional is provided
        result = self._run(["completions", "bash", "--list-ids"])
        self.assertEqual(result, 0)

    def test_invalid_shell_rejected(self):
        with self.assertRaises(SystemExit):
            import main as main_mod
            main_mod.build_parser().parse_args(["completions", "fish"])


if __name__ == "__main__":
    unittest.main()
