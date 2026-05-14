#!/usr/bin/env python3
"""Todo CLI — entry point."""

import argparse
import sys

import completions as completions_mod
import formatter
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


def cmd_completions(args: argparse.Namespace) -> int:
    if args.list_ids:
        print("\n".join(completions_mod.get_ids()))
        return 0
    if args.list_tags:
        print("\n".join(completions_mod.get_tags()))
        return 0
    shell = getattr(args, "shell", None)
    if shell == "bash":
        print(completions_mod.bash_script())
    elif shell == "zsh":
        print(completions_mod.zsh_script())
    else:
        print("Error: specify a shell: bash or zsh", file=sys.stderr)
        return 1
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

    # completions
    p_comp = sub.add_parser(
        "completions",
        help="Output shell completion script (bash or zsh).",
    )
    p_comp.add_argument(
        "shell", nargs="?", choices=["bash", "zsh"],
        help="Shell to generate completion script for.",
    )
    p_comp.add_argument(
        "--list-ids", action="store_true",
        help="Print all todo IDs, one per line (used by completion scripts).",
    )
    p_comp.add_argument(
        "--list-tags", action="store_true",
        help="Print all tag names, one per line (used by completion scripts).",
    )
    p_comp.set_defaults(func=cmd_completions)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
