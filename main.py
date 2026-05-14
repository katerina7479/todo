#!/usr/bin/env python3
"""Todo CLI — entry point."""

import argparse
import sys

import formatter
import todo
import validator


def cmd_add(args: argparse.Namespace) -> int:
    try:
        title = validator.validate_title(" ".join(args.title))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    item = todo.add_todo(title)
    print(f"Added: {formatter.format_todo(item)}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    items = todo.list_todos(show_done=args.all)
    print(formatter.format_todo_list(items))
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    try:
        todo_id = validator.validate_id(args.id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    try:
        item = todo.mark_done(todo_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Marked done: {formatter.format_todo(item)}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    try:
        todo_id = validator.validate_id(args.id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    try:
        item = todo.delete_todo(todo_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Deleted: {formatter.format_todo(item)}")
    return 0


def cmd_edit(args: argparse.Namespace) -> int:
    try:
        todo_id = validator.validate_id(args.id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    kwargs: dict = {}
    if args.title is not None:
        try:
            kwargs["title"] = validator.validate_title(" ".join(args.title))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    if args.priority is not None:
        try:
            kwargs["priority"] = validator.validate_priority(args.priority)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    if args.due_date is not None:
        try:
            kwargs["due_date"] = validator.validate_due_date(args.due_date)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    if args.tags is not None:
        try:
            kwargs["tags"] = validator.validate_tags(args.tags)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    if not kwargs:
        print("Error: at least one field to update must be specified.", file=sys.stderr)
        return 1

    try:
        item = todo.update_todo(todo_id, **kwargs)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Updated: {formatter.format_todo(item)}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    try:
        todo_id = validator.validate_id(args.id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    item = todo.get_todo(todo_id)
    if item is None:
        print(f"Error: Todo #{todo_id} not found.", file=sys.stderr)
        return 1
    print(formatter.format_todo_detail(item))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A simple command-line todo manager.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # add
    p_add = sub.add_parser("add", help="Add a new todo item.")
    p_add.add_argument("title", nargs="+", help="Title of the todo item.")
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = sub.add_parser("list", help="List todo items.")
    p_list.add_argument(
        "--all", action="store_true", help="Include completed todos."
    )
    p_list.set_defaults(func=cmd_list)

    # done
    p_done = sub.add_parser("done", help="Mark a todo as done.")
    p_done.add_argument("id", help="ID of the todo to mark done.")
    p_done.set_defaults(func=cmd_done)

    # delete
    p_del = sub.add_parser("delete", help="Delete a todo item.")
    p_del.add_argument("id", help="ID of the todo to delete.")
    p_del.set_defaults(func=cmd_delete)

    # edit
    p_edit = sub.add_parser("edit", help="Modify an existing todo item.")
    p_edit.add_argument("id", help="ID of the todo to edit.")
    p_edit.add_argument("--title", nargs="+", default=None, help="New title.")
    p_edit.add_argument("--priority", default=None, metavar="low/medium/high", help="Priority level.")
    p_edit.add_argument("--due-date", dest="due_date", default=None, metavar="YYYY-MM-DD", help="Due date.")
    p_edit.add_argument("--tags", default=None, metavar="tag1,tag2", help="Comma-separated tags.")
    p_edit.set_defaults(func=cmd_edit)

    # show
    p_show = sub.add_parser("show", help="Show detail for a todo item.")
    p_show.add_argument("id", help="ID of the todo to show.")
    p_show.set_defaults(func=cmd_show)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
