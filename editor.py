"""Open $EDITOR for multi-line text input."""

import os
import subprocess
import tempfile
from pathlib import Path


def open_editor(initial: str = "") -> str:
    """Open $EDITOR with optional initial content; return the saved text."""
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vi"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(initial)
        tmp = Path(f.name)
    try:
        subprocess.run([editor, str(tmp)], check=True)
        return tmp.read_text(encoding="utf-8")
    finally:
        tmp.unlink(missing_ok=True)
