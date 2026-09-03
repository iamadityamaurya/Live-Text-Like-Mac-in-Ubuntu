"""Configuration manager for Live Text OCR."""

import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "shortcut": "<Super><Shift>o",
    "ocr_language": "eng",
    "psm_mode": 6,  # Single uniform block of text
    "preprocess": {
        "enabled": True,
        "upscale_factor": 2.0,
        "auto_invert": True,
        "enhance_contrast": True,
        "binarize": True,
    },
    "notifications": {
        "enabled": True,
        "preview_max_chars": 45,
        "expire_time_ms": 3000,
    },
    "history": {
        "enabled": True,
        "max_entries": 50,
    },
    "clipboard": {
        "trim_whitespace": True,
        "preserve_linebreaks": True,
        "strip_trailing_newlines": True,
    },
}

CONFIG_DIR = Path(os.path.expanduser("~/.config/live-text-ocr"))
CONFIG_FILE = CONFIG_DIR / "config.json"
DATA_DIR = Path(os.path.expanduser("~/.local/share/live-text-ocr"))
TESSDATA_DIR = Path(os.path.expanduser("~/.local/share/tessdata"))


def get_tessdata_dir() -> Path:
    """Return the primary tessdata directory."""
    TESSDATA_DIR.mkdir(parents=True, exist_ok=True)
    return TESSDATA_DIR


def get_data_dir() -> Path:
    """Return the application data directory."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def load_config() -> Dict[str, Any]:
    """Load configuration from disk or return defaults."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        # Deep merge with defaults to ensure all keys exist
        config = DEFAULT_CONFIG.copy()
        for k, v in user_config.items():
            if isinstance(v, dict) and k in config and isinstance(config[k], dict):
                config[k] = {**config[k], **v}
            else:
                config[k] = v
        return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
