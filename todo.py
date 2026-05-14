import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from config import Config


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Todo:
    title: str
    id: int = 0
    done: bool = False
    priority: str = "medium"
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Todo":
        return cls(
            id=data["id"],
            title=data["title"],
            done=data.get("done", False),
            priority=data.get("priority", "medium"),
            created_at=data.get("created_at", _now_iso()),
        )


class TodoStore:
    def __init__(self, config: Config):
        self.config = config

    def _load(self) -> tuple[List[Todo], int]:
        if not self.config.storage_path.exists():
            return [], 0
        with open(self.config.storage_path) as f:
            data = json.load(f)
        todos = [Todo.from_dict(item) for item in data.get("todos", [])]
        counter = data.get("counter", 0)
        return todos, counter

    def _save(self, todos: List[Todo], counter: int) -> None:
        self.config.ensure_storage_dir()
        with open(self.config.storage_path, "w") as f:
            json.dump({"counter": counter, "todos": [t.to_dict() for t in todos]}, f, indent=2)

    def add(self, title: str, priority: str = "medium") -> Todo:
        todos, counter = self._load()
        counter += 1
        todo = Todo(id=counter, title=title, priority=priority)
        todos.append(todo)
        self._save(todos, counter)
        return todo

    def list(self, show_done: bool = False) -> List[Todo]:
        todos, _ = self._load()
        if not show_done:
            todos = [t for t in todos if not t.done]
        return todos

    def get(self, todo_id: int) -> Optional[Todo]:
        todos, _ = self._load()
        for todo in todos:
            if todo.id == todo_id:
                return todo
        return None

    def complete(self, todo_id: int) -> Optional[Todo]:
        todos, counter = self._load()
        for todo in todos:
            if todo.id == todo_id:
                todo.done = True
                self._save(todos, counter)
                return todo
        return None

    def delete(self, todo_id: int) -> bool:
        todos, counter = self._load()
        original_count = len(todos)
        todos = [t for t in todos if t.id != todo_id]
        if len(todos) == original_count:
            return False
        self._save(todos, counter)
        return True
