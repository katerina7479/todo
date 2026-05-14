import json
import os
from pathlib import Path


DEFAULT_STORAGE_DIR = Path.home() / ".todo"
DEFAULT_STORAGE_FILE = DEFAULT_STORAGE_DIR / "todos.json"


class Config:
    def __init__(self, storage_path: Path = DEFAULT_STORAGE_FILE):
        self.storage_path = Path(storage_path)

    @classmethod
    def load(cls, config_file: Path) -> "Config":
        if not config_file.exists():
            return cls()
        with open(config_file) as f:
            data = json.load(f)
        return cls(storage_path=Path(data.get("storage_path", DEFAULT_STORAGE_FILE)))

    def save(self, config_file: Path) -> None:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump({"storage_path": str(self.storage_path)}, f, indent=2)

    def ensure_storage_dir(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
