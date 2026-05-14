"""Tests for import/export functionality."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

import importexport
import todo as todo_module


class ExportImportBase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._store = Path(self._tmpdir.name) / "todos.json"
        os.environ["TODO_FILE"] = str(self._store)

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        self._tmpdir.cleanup()

    def _seed(self, *titles):
        for title in titles:
            todo_module.add_todo(title)


class TestExportJSON(ExportImportBase):
    def test_exports_all_todos(self):
        self._seed("Alpha", "Beta")
        out = Path(self._tmpdir.name) / "out.json"
        count = importexport.export_todos(out)
        self.assertEqual(count, 2)
        data = json.loads(out.read_text())
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "Alpha")
        self.assertEqual(data[1]["title"], "Beta")

    def test_exports_empty_store(self):
        out = Path(self._tmpdir.name) / "out.json"
        count = importexport.export_todos(out)
        self.assertEqual(count, 0)
        self.assertEqual(json.loads(out.read_text()), [])

    def test_format_inferred_from_extension(self):
        self._seed("X")
        out = Path(self._tmpdir.name) / "todos.json"
        importexport.export_todos(out)
        data = json.loads(out.read_text())
        self.assertIsInstance(data, list)

    def test_explicit_format_overrides_extension(self):
        self._seed("X")
        out = Path(self._tmpdir.name) / "todos.txt"
        importexport.export_todos(out, fmt="json")
        data = json.loads(out.read_text())
        self.assertIsInstance(data, list)


class TestExportCSV(ExportImportBase):
    def _read_csv_rows(self, path: Path):
        import csv
        with path.open(newline="") as f:
            return list(csv.DictReader(f))

    def test_exports_csv(self):
        self._seed("Alpha", "Beta")
        todo_module.mark_done(1)
        out = Path(self._tmpdir.name) / "out.csv"
        count = importexport.export_todos(out)
        self.assertEqual(count, 2)
        rows = self._read_csv_rows(out)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], "Alpha")
        self.assertEqual(rows[0]["done"], "True")
        self.assertEqual(rows[1]["title"], "Beta")
        self.assertEqual(rows[1]["done"], "False")

    def test_tags_serialised_comma_separated(self):
        todo_module.add_todo("Tagged", tags=["a", "b"])
        out = Path(self._tmpdir.name) / "out.csv"
        importexport.export_todos(out)
        rows = self._read_csv_rows(out)
        self.assertEqual(rows[0]["tags"], "a,b")

    def test_empty_tags(self):
        self._seed("No tags")
        out = Path(self._tmpdir.name) / "out.csv"
        importexport.export_todos(out)
        rows = self._read_csv_rows(out)
        self.assertEqual(rows[0]["tags"], "")


class TestImportJSON(ExportImportBase):
    def _write_json(self, items: list) -> Path:
        path = Path(self._tmpdir.name) / "import.json"
        path.write_text(json.dumps(items))
        return path

    def test_imports_new_todos(self):
        path = self._write_json([
            {"id": 1, "title": "Foo", "done": False, "created_at": "", "tags": []},
            {"id": 2, "title": "Bar", "done": True, "created_at": "", "tags": ["x"]},
        ])
        imported, skipped = importexport.import_todos(path)
        self.assertEqual(imported, 2)
        self.assertEqual(skipped, 0)
        todos = todo_module.load_todos()
        self.assertEqual(len(todos), 2)

    def test_skips_duplicate_ids(self):
        self._seed("Existing")  # id=1
        path = self._write_json([
            {"id": 1, "title": "Should be skipped", "done": False, "created_at": "", "tags": []},
            {"id": 2, "title": "New one", "done": False, "created_at": "", "tags": []},
        ])
        imported, skipped = importexport.import_todos(path)
        self.assertEqual(imported, 1)
        self.assertEqual(skipped, 1)
        todos = todo_module.load_todos()
        titles = [t["title"] for t in todos]
        self.assertIn("Existing", titles)
        self.assertIn("New one", titles)
        self.assertNotIn("Should be skipped", titles)

    def test_updates_next_id(self):
        path = self._write_json([
            {"id": 99, "title": "High ID", "done": False, "created_at": "", "tags": []},
        ])
        importexport.import_todos(path)
        new = todo_module.add_todo("After import")
        self.assertEqual(new["id"], 100)

    def test_rejects_non_array(self):
        path = Path(self._tmpdir.name) / "bad.json"
        path.write_text(json.dumps({"id": 1, "title": "oops"}))
        with self.assertRaises(ValueError):
            importexport.import_todos(path)

    def test_rejects_missing_id(self):
        path = self._write_json([{"title": "No id"}])
        with self.assertRaises(ValueError):
            importexport.import_todos(path)


class TestImportCSV(ExportImportBase):
    def _write_csv(self, rows: list[dict]) -> Path:
        import csv
        path = Path(self._tmpdir.name) / "import.csv"
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["id", "title", "done", "created_at", "tags"]
            )
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_imports_csv(self):
        path = self._write_csv([
            {"id": 1, "title": "Task A", "done": "False", "created_at": "", "tags": ""},
            {"id": 2, "title": "Task B", "done": "True", "created_at": "", "tags": "x,y"},
        ])
        imported, skipped = importexport.import_todos(path)
        self.assertEqual(imported, 2)
        todos = todo_module.load_todos()
        self.assertEqual(todos[1]["tags"], ["x", "y"])
        self.assertTrue(todos[1]["done"])

    def test_skips_duplicate_ids_csv(self):
        self._seed("Original")  # id=1
        path = self._write_csv([
            {"id": 1, "title": "Dup", "done": "False", "created_at": "", "tags": ""},
        ])
        imported, skipped = importexport.import_todos(path)
        self.assertEqual(imported, 0)
        self.assertEqual(skipped, 1)

    def test_csv_done_variations(self):
        path = self._write_csv([
            {"id": 1, "title": "T1", "done": "true", "created_at": "", "tags": ""},
            {"id": 2, "title": "T2", "done": "1", "created_at": "", "tags": ""},
            {"id": 3, "title": "T3", "done": "yes", "created_at": "", "tags": ""},
            {"id": 4, "title": "T4", "done": "False", "created_at": "", "tags": ""},
        ])
        importexport.import_todos(path)
        todos = {t["id"]: t for t in todo_module.load_todos()}
        self.assertTrue(todos[1]["done"])
        self.assertTrue(todos[2]["done"])
        self.assertTrue(todos[3]["done"])
        self.assertFalse(todos[4]["done"])


class TestRoundTrip(ExportImportBase):
    def test_json_roundtrip(self):
        todo_module.add_todo("Alpha", tags=["a"])
        todo_module.add_todo("Beta")
        todo_module.mark_done(2)
        export_path = Path(self._tmpdir.name) / "rt.json"
        importexport.export_todos(export_path)

        # Import into a fresh store
        new_store = Path(self._tmpdir.name) / "new.json"
        os.environ["TODO_FILE"] = str(new_store)
        importexport.import_todos(export_path)
        todos = todo_module.load_todos()
        self.assertEqual(len(todos), 2)
        t1 = next(t for t in todos if t["id"] == 1)
        self.assertEqual(t1["title"], "Alpha")
        self.assertEqual(t1["tags"], ["a"])
        t2 = next(t for t in todos if t["id"] == 2)
        self.assertTrue(t2["done"])

    def test_csv_roundtrip(self):
        todo_module.add_todo("Alpha", tags=["x", "y"])
        export_path = Path(self._tmpdir.name) / "rt.csv"
        importexport.export_todos(export_path)

        new_store = Path(self._tmpdir.name) / "new.json"
        os.environ["TODO_FILE"] = str(new_store)
        importexport.import_todos(export_path)
        todos = todo_module.load_todos()
        self.assertEqual(todos[0]["title"], "Alpha")
        self.assertEqual(todos[0]["tags"], ["x", "y"])


if __name__ == "__main__":
    unittest.main()
