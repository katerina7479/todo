#!/usr/bin/env python3
"""Todo CLI — entry point."""

import argparse
import sys

import formatter
import repl
import todo
import validator


def cmd_add(args: argparse.Namespace) -> int:
    try:
        title = validator.validate_title(" ".join(args.title))
        tags = validator.validate_tags(args.tags or "")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    item = todo.add_todo(title, tags=tags)
    print(f"Added: {formatter.format_todo(item)}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    items = todo.list_todos(show_done=args.all, tag=args.tag)
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


def cmd_search(args: argparse.Namespace) -> int:
    items = todo.search_todos(args.query)
    print(formatter.format_todo_list(items))
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


def cmd_interactive(args: argparse.Namespace) -> int:
    repl.run_repl()
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
    p_add.add_argument(
        "--tags", metavar="TAGS",
        help="Comma-separated tags (e.g. 'work,urgent').",
    )
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = sub.add_parser("list", help="List todo items.")
    p_list.add_argument(
        "--all", action="store_true", help="Include completed todos."
    )
    p_list.add_argument(
        "--tag", metavar="TAG",
        help="Filter to todos that have this tag.",
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

    # show
    p_show = sub.add_parser("show", help="Show detail for a todo item.")
    p_show.add_argument("id", help="ID of the todo to show.")
    p_show.set_defaults(func=cmd_show)

    # search
    p_search = sub.add_parser("search", help="Search todos by title or tag.")
    p_search.add_argument("query", help="Substring to search for (case-insensitive).")
    p_search.set_defaults(func=cmd_search)

    # interactive
    p_interactive = sub.add_parser("interactive", help="Enter interactive REPL mode.")
    p_interactive.set_defaults(func=cmd_interactive)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
