"""Clipboard capture history logger and manager."""

import json
import time
from typing import Any, Dict, List

from live_text_ocr.config import get_data_dir, load_config

HISTORY_FILE = get_data_dir() / "history.json"


def log_history_entry(text: str) -> None:
    """Append a newly extracted text entry to the history file."""
    config = load_config()
    if not config.get("history", {}).get("enabled", True):
        return

    max_entries = config.get("history", {}).get("max_entries", 50)
    history = get_history()

    entry = {
        "timestamp": int(time.time()),
        "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
        "char_count": len(text),
        "line_count": len(text.splitlines()),
        "text": text,
    }

    # Prepend new entry
    history.insert(0, entry)
    history = history[:max_entries]

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_history() -> List[Dict[str, Any]]:
    """Retrieve all history items."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def clear_history() -> None:
    """Clear all history items."""
    if HISTORY_FILE.exists():
        try:
            HISTORY_FILE.unlink()
        except Exception:
            pass
