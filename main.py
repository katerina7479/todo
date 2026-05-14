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
    repeat = None
    if args.repeat:
        try:
            repeat = validator.validate_repeat(args.repeat)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    item = todo.add_todo(title, due_date=args.due_date or None, repeat=repeat)
    formatter.print_todo_added(item)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    items = todo.list_todos(show_done=args.all)
    formatter.print_todo_list(items)
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    try:
        todo_id = validator.validate_id(args.id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    try:
        item, next_occurrence = todo.mark_done(todo_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    formatter.print_todo_done(item, next_occurrence)
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
    formatter.print_todo_deleted(item)
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
    formatter.print_todo_detail(item)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A simple command-line todo manager.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    p_add = sub.add_parser("add", help="Add a new todo item.")
    p_add.add_argument("title", nargs="+", help="Title of the todo item.")
    p_add.add_argument(
        "--due-date",
        dest="due_date",
        default=None,
        metavar="YYYY-MM-DD",
        help="Due date for the todo.",
    )
    p_add.add_argument(
        "--repeat",
        default=None,
        metavar="SCHEDULE",
        help="Repeat schedule: daily, weekly, monthly, or custom:N (every N days).",
    )
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List todo items.")
    p_list.add_argument("--all", action="store_true", help="Include completed todos.")
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="Mark a todo as done.")
    p_done.add_argument("id", help="ID of the todo to mark done.")
    p_done.set_defaults(func=cmd_done)

    p_del = sub.add_parser("delete", help="Delete a todo item.")
    p_del.add_argument("id", help="ID of the todo to delete.")
    p_del.set_defaults(func=cmd_delete)

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
