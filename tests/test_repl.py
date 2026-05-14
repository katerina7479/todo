"""Tests for the interactive REPL (pb-35)."""

import pytest

import todo
import repl


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))


# ---------------------------------------------------------------------------
# Quit / exit signals
# ---------------------------------------------------------------------------

class TestQuitCommands:
    def test_q_returns_true(self):
        assert repl.handle_line("q") is True

    def test_quit_returns_true(self):
        assert repl.handle_line("quit") is True

    def test_exit_returns_true(self):
        assert repl.handle_line("exit") is True

    def test_quit_case_insensitive(self):
        assert repl.handle_line("QUIT") is True

    def test_q_with_whitespace(self):
        assert repl.handle_line("  q  ") is True


# ---------------------------------------------------------------------------
# Empty / whitespace input
# ---------------------------------------------------------------------------

class TestEmptyInput:
    def test_empty_string_returns_false(self):
        assert repl.handle_line("") is False

    def test_whitespace_only_returns_false(self):
        assert repl.handle_line("   ") is False


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

class TestHelpCommand:
    def test_help_returns_false(self, capsys):
        result = repl.handle_line("help")
        assert result is False

    def test_h_alias_shows_help(self, capsys):
        repl.handle_line("h")
        out = capsys.readouterr().out
        assert "add" in out

    def test_question_mark_shows_help(self, capsys):
        repl.handle_line("?")
        out = capsys.readouterr().out
        assert "quit" in out

    def test_help_text_lists_all_commands(self, capsys):
        repl.handle_line("help")
        out = capsys.readouterr().out
        for cmd in ("add", "list", "done", "delete", "show", "quit"):
            assert cmd in out


# ---------------------------------------------------------------------------
# add / a
# ---------------------------------------------------------------------------

class TestAddCommand:
    def test_add_creates_todo(self):
        repl.handle_line("add Buy milk")
        assert todo.get_todo(1) is not None
        assert todo.get_todo(1)["title"] == "Buy milk"

    def test_a_alias_creates_todo(self):
        repl.handle_line("a Write tests")
        assert todo.get_todo(1)["title"] == "Write tests"

    def test_add_prints_confirmation(self, capsys):
        repl.handle_line("add Buy eggs")
        out = capsys.readouterr().out
        assert "Added" in out
        assert "Buy eggs" in out

    def test_add_returns_false(self):
        assert repl.handle_line("add Something") is False

    def test_add_without_title_prints_error(self, capsys):
        repl.handle_line("add")
        err = capsys.readouterr().err
        assert "Usage" in err

    def test_add_without_title_returns_false(self):
        assert repl.handle_line("add") is False

    def test_add_multi_word_title(self):
        repl.handle_line("add Buy more coffee beans")
        assert todo.get_todo(1)["title"] == "Buy more coffee beans"


# ---------------------------------------------------------------------------
# list / l
# ---------------------------------------------------------------------------

class TestListCommand:
    def test_list_returns_false(self):
        assert repl.handle_line("list") is False

    def test_l_alias_returns_false(self):
        assert repl.handle_line("l") is False

    def test_list_shows_pending_todos(self, capsys):
        todo.add_todo("Pending task")
        repl.handle_line("list")
        out = capsys.readouterr().out
        assert "Pending task" in out

    def test_list_hides_done_by_default(self, capsys):
        t = todo.add_todo("Done task")
        todo.mark_done(t["id"])
        repl.handle_line("list")
        out = capsys.readouterr().out
        assert "Done task" not in out

    def test_list_all_shows_done(self, capsys):
        t = todo.add_todo("Done task")
        todo.mark_done(t["id"])
        repl.handle_line("list --all")
        out = capsys.readouterr().out
        assert "Done task" in out

    def test_l_all_alias(self, capsys):
        t = todo.add_todo("Done task")
        todo.mark_done(t["id"])
        repl.handle_line("l --all")
        out = capsys.readouterr().out
        assert "Done task" in out

    def test_list_empty_shows_no_todos_message(self, capsys):
        repl.handle_line("list")
        out = capsys.readouterr().out
        assert "No todos" in out


# ---------------------------------------------------------------------------
# done / d
# ---------------------------------------------------------------------------

class TestDoneCommand:
    def test_done_marks_todo_complete(self):
        t = todo.add_todo("Finish me")
        repl.handle_line(f"done {t['id']}")
        assert todo.get_todo(t["id"])["done"] is True

    def test_d_alias_marks_done(self):
        t = todo.add_todo("Finish me")
        repl.handle_line(f"d {t['id']}")
        assert todo.get_todo(t["id"])["done"] is True

    def test_done_prints_confirmation(self, capsys):
        t = todo.add_todo("Finish me")
        repl.handle_line(f"done {t['id']}")
        out = capsys.readouterr().out
        assert "Marked done" in out

    def test_done_returns_false(self):
        t = todo.add_todo("Task")
        assert repl.handle_line(f"done {t['id']}") is False

    def test_done_without_id_prints_error(self, capsys):
        repl.handle_line("done")
        err = capsys.readouterr().err
        assert "Usage" in err

    def test_done_nonexistent_id_prints_error(self, capsys):
        repl.handle_line("done 999")
        err = capsys.readouterr().err
        assert "Error" in err

    def test_done_invalid_id_prints_error(self, capsys):
        repl.handle_line("done abc")
        err = capsys.readouterr().err
        assert "Error" in err


# ---------------------------------------------------------------------------
# delete / x
# ---------------------------------------------------------------------------

class TestDeleteCommand:
    def test_delete_removes_todo(self):
        t = todo.add_todo("Delete me")
        repl.handle_line(f"delete {t['id']}")
        assert todo.get_todo(t["id"]) is None

    def test_x_alias_deletes(self):
        t = todo.add_todo("Delete me")
        repl.handle_line(f"x {t['id']}")
        assert todo.get_todo(t["id"]) is None

    def test_delete_prints_confirmation(self, capsys):
        t = todo.add_todo("Delete me")
        repl.handle_line(f"delete {t['id']}")
        out = capsys.readouterr().out
        assert "Deleted" in out

    def test_delete_returns_false(self):
        t = todo.add_todo("Task")
        assert repl.handle_line(f"delete {t['id']}") is False

    def test_delete_without_id_prints_error(self, capsys):
        repl.handle_line("delete")
        err = capsys.readouterr().err
        assert "Usage" in err

    def test_delete_nonexistent_id_prints_error(self, capsys):
        repl.handle_line("delete 999")
        err = capsys.readouterr().err
        assert "Error" in err


# ---------------------------------------------------------------------------
# show / s
# ---------------------------------------------------------------------------

class TestShowCommand:
    def test_show_displays_detail(self, capsys):
        t = todo.add_todo("Detailed task")
        repl.handle_line(f"show {t['id']}")
        out = capsys.readouterr().out
        assert "Detailed task" in out

    def test_s_alias_shows_detail(self, capsys):
        t = todo.add_todo("Detailed task")
        repl.handle_line(f"s {t['id']}")
        out = capsys.readouterr().out
        assert "Detailed task" in out

    def test_show_without_id_prints_error(self, capsys):
        repl.handle_line("show")
        err = capsys.readouterr().err
        assert "Usage" in err

    def test_show_nonexistent_id_prints_error(self, capsys):
        repl.handle_line("show 999")
        err = capsys.readouterr().err
        assert "Error" in err

    def test_show_returns_false(self):
        t = todo.add_todo("Task")
        assert repl.handle_line(f"show {t['id']}") is False


# ---------------------------------------------------------------------------
# Unknown command
# ---------------------------------------------------------------------------

class TestUnknownCommand:
    def test_unknown_command_prints_error(self, capsys):
        repl.handle_line("frobnicate")
        err = capsys.readouterr().err
        assert "Unknown command" in err
        assert "frobnicate" in err

    def test_unknown_command_returns_false(self):
        assert repl.handle_line("frobnicate") is False


# ---------------------------------------------------------------------------
# Prompt / pending count
# ---------------------------------------------------------------------------

class TestPromptAndCount:
    def test_pending_count_zero_when_empty(self):
        assert repl._pending_count() == 0

    def test_pending_count_reflects_added_todos(self):
        todo.add_todo("A")
        todo.add_todo("B")
        assert repl._pending_count() == 2

    def test_pending_count_excludes_done(self):
        t = todo.add_todo("Done")
        todo.add_todo("Pending")
        todo.mark_done(t["id"])
        assert repl._pending_count() == 1

    def test_prompt_contains_count(self):
        todo.add_todo("Task")
        prompt = repl._prompt()
        assert "1" in prompt
        assert "pending" in prompt


# ---------------------------------------------------------------------------
# run_repl integration (mocked input)
# ---------------------------------------------------------------------------

class TestRunRepl:
    def test_run_repl_exits_on_quit(self, monkeypatch, capsys):
        inputs = iter(["q"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        repl.run_repl()
        out = capsys.readouterr().out
        assert "interactive mode" in out.lower()

    def test_run_repl_exits_on_eof(self, monkeypatch, capsys):
        monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(EOFError))
        repl.run_repl()

    def test_run_repl_processes_commands_before_quit(self, monkeypatch):
        inputs = iter(["add Buy groceries", "q"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        repl.run_repl()
        assert todo.get_todo(1)["title"] == "Buy groceries"

    def test_run_repl_exits_on_keyboard_interrupt(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "builtins.input",
            lambda _: (_ for _ in ()).throw(KeyboardInterrupt),
        )
        repl.run_repl()
