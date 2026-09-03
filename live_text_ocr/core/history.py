"""Clipboard capture history logger and manager with pinning and deletion."""

import json
import time
import uuid
from typing import Any, Dict, List

from live_text_ocr.config import get_data_dir, load_config

HISTORY_FILE = get_data_dir() / "history.json"


def log_history_entry(text: str) -> None:
    """Append a newly extracted text entry to the history file."""
    if not text or not text.strip():
        return

    config = load_config()
    if not config.get("history", {}).get("enabled", True):
        return

    max_entries = config.get("history", {}).get("max_entries", 50)
    raw_history = _read_raw_history()

    # Don't add consecutive identical duplicate entries
    if raw_history and raw_history[0].get("text", "").strip() == text.strip():
        return

    entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": int(time.time()),
        "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
        "char_count": len(text),
        "line_count": len(text.splitlines()),
        "pinned": False,
        "text": text,
    }

    # Prepend new entry
    raw_history.insert(0, entry)
    
    # Keep max unpinned entries, preserve all pinned
    pinned = [item for item in raw_history if item.get("pinned", False)]
    unpinned = [item for item in raw_history if not item.get("pinned", False)]
    raw_history = pinned + unpinned[:max_entries]

    _save_raw_history(raw_history)


def get_history() -> List[Dict[str, Any]]:
    """Retrieve all history items, with pinned items prioritized at the top."""
    raw = _read_raw_history()
    # Migration helper for older history without IDs
    modified = False
    for item in raw:
        if "id" not in item:
            item["id"] = str(uuid.uuid4())[:8]
            modified = True
        if "pinned" not in item:
            item["pinned"] = False
            modified = True
    if modified:
        _save_raw_history(raw)

    pinned = [item for item in raw if item.get("pinned", False)]
    unpinned = [item for item in raw if not item.get("pinned", False)]
    # Sort pinned by timestamp desc, unpinned by timestamp desc
    pinned.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    unpinned.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return pinned + unpinned


def toggle_pin_entry(entry_id: str) -> bool:
    """Toggle the pinned status of a history entry."""
    raw = _read_raw_history()
    for item in raw:
        if item.get("id") == entry_id:
            item["pinned"] = not item.get("pinned", False)
            _save_raw_history(raw)
            return item["pinned"]
    return False


def delete_history_entry(entry_id: str) -> None:
    """Delete a single history entry by ID."""
    raw = _read_raw_history()
    raw = [item for item in raw if item.get("id") != entry_id]
    _save_raw_history(raw)


def clear_history() -> None:
    """Clear all unpinned history items."""
    raw = _read_raw_history()
    pinned_only = [item for item in raw if item.get("pinned", False)]
    _save_raw_history(pinned_only)


def _read_raw_history() -> List[Dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_raw_history(data: List[Dict[str, Any]]) -> None:
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
