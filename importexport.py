"""Import and export todos in JSON and CSV formats."""

import csv
import io
import json
from pathlib import Path
from typing import Optional

import todo as todo_module


def _detect_format(path: Path, explicit: Optional[str]) -> str:
    if explicit:
        return explicit.lower()
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    return "json"


def export_todos(path: Path, fmt: Optional[str] = None) -> int:
    """Write all todos to *path* in the given format. Returns count written."""
    fmt = _detect_format(path, fmt)
    items = todo_module.load_todos()

    if fmt == "csv":
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "title", "done", "created_at", "tags"],
            )
            writer.writeheader()
            for item in items:
                writer.writerow({
                    "id": item["id"],
                    "title": item["title"],
                    "done": item["done"],
                    "created_at": item.get("created_at", ""),
                    "tags": ",".join(item.get("tags", [])),
                })
    else:
        with path.open("w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    return len(items)


def import_todos(path: Path, fmt: Optional[str] = None) -> tuple[int, int]:
    """Read todos from *path* and merge into the store, skipping duplicates by ID.

    Returns (imported_count, skipped_count).
    """
    fmt = _detect_format(path, fmt)

    if fmt == "csv":
        incoming = _read_csv(path)
    else:
        incoming = _read_json(path)

    data = todo_module._load_raw()
    existing_ids = {t["id"] for t in data["todos"]}

    imported = 0
    skipped = 0
    for item in incoming:
        if item["id"] in existing_ids:
            skipped += 1
            continue
        data["todos"].append(item)
        existing_ids.add(item["id"])
        if item["id"] >= data["next_id"]:
            data["next_id"] = item["id"] + 1
        imported += 1

    todo_module._save_raw(data)
    return imported, skipped


def _read_json(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError("JSON import file must contain a top-level array.")
    result = []
    for item in items:
        result.append(_normalise(item))
    return result


def _read_csv(path: Path) -> list[dict]:
    result = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            result.append(_normalise_csv(row))
    return result


def _normalise(item: dict) -> dict:
    """Validate and normalise a todo dict from JSON."""
    if "id" not in item:
        raise ValueError(f"Todo entry missing 'id' field: {item!r}")
    return {
        "id": int(item["id"]),
        "title": str(item.get("title", "")),
        "done": bool(item.get("done", False)),
        "created_at": str(item.get("created_at", "")),
        "tags": list(item.get("tags", [])),
    }


def _normalise_csv(row: dict) -> dict:
    """Convert a CSV row into a todo dict."""
    if "id" not in row or not row["id"]:
        raise ValueError(f"CSV row missing 'id': {row!r}")
    tags_raw = row.get("tags", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
    done_raw = row.get("done", "False")
    done = done_raw.strip().lower() in ("true", "1", "yes")
    return {
        "id": int(row["id"]),
        "title": str(row.get("title", "")),
        "done": done,
        "created_at": str(row.get("created_at", "")),
        "tags": tags,
    }
