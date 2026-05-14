"""Interactive REPL for the todo CLI."""

import sys

import formatter
import todo
import validator

try:
    import readline
    _READLINE_AVAILABLE = True
except ImportError:
    _READLINE_AVAILABLE = False

_COMMANDS = ["add", "list", "done", "delete", "show", "help", "quit", "exit"]
_ALIASES = {
    "a": "add",
    "l": "list",
    "d": "done",
    "x": "delete",
    "s": "show",
    "?": "help",
    "h": "help",
    "q": "quit",
}

_HELP_TEXT = """\
Commands:
  a <title>   add <title>    Add a new todo
  l           list           List pending todos
  l --all     list --all     List all todos (including done)
  d <id>      done <id>      Mark a todo as done
  x <id>      delete <id>    Delete a todo
  s <id>      show <id>      Show todo detail
  ?           help           Show this help
  q           quit           Exit interactive mode"""


def _completer(text: str, state: int):
    options = [c for c in _COMMANDS + list(_ALIASES) if c.startswith(text)]
    try:
        return options[state]
    except IndexError:
        return None


def _pending_count() -> int:
    return len(todo.list_todos(show_done=False))


def _prompt() -> str:
    n = _pending_count()
    return f"todo ({n} pending)> "


def handle_line(line: str) -> bool:
    """Process one input line. Returns True if the REPL should quit."""
    parts = line.strip().split(None, 1)
    if not parts:
        return False

    raw_cmd = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""
    cmd = _ALIASES.get(raw_cmd, raw_cmd)

    if cmd in ("quit", "exit"):
        return True

    if cmd == "help":
        print(_HELP_TEXT)
        return False

    if cmd == "add":
        if not rest:
            print("Usage: add <title>", file=sys.stderr)
            return False
        try:
            title = validator.validate_title(rest)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
        item = todo.add_todo(title)
        print(f"Added: {formatter.format_todo(item)}")
        return False

    if cmd == "list":
        show_all = "--all" in rest.split()
        items = todo.list_todos(show_done=show_all)
        print(formatter.format_todo_list(items))
        return False

    if cmd == "done":
        if not rest:
            print("Usage: done <id>", file=sys.stderr)
            return False
        try:
            todo_id = validator.validate_id(rest.strip())
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
        try:
            item = todo.mark_done(todo_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
        print(f"Marked done: {formatter.format_todo(item)}")
        return False

    if cmd == "delete":
        if not rest:
            print("Usage: delete <id>", file=sys.stderr)
            return False
        try:
            todo_id = validator.validate_id(rest.strip())
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
        try:
            item = todo.delete_todo(todo_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
        print(f"Deleted: {formatter.format_todo(item)}")
        return False

    if cmd == "show":
        if not rest:
            print("Usage: show <id>", file=sys.stderr)
            return False
        try:
            todo_id = validator.validate_id(rest.strip())
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
        item = todo.get_todo(todo_id)
        if item is None:
            print(f"Error: Todo #{todo_id} not found.", file=sys.stderr)
            return False
        print(formatter.format_todo_detail(item))
        return False

    print(f"Unknown command '{raw_cmd}'. Type 'help' for commands.", file=sys.stderr)
    return False


def run_repl() -> None:
    """Enter the interactive REPL loop."""
    if _READLINE_AVAILABLE:
        readline.set_completer(_completer)
        readline.parse_and_bind("tab: complete")

    print("Todo interactive mode. Type 'help' for commands, 'quit' to exit.")

    while True:
        try:
            line = input(_prompt())
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if handle_line(line):
            break
