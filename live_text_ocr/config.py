"""Configuration manager for Live Text OCR."""

import json
import os
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "ocr_language": "eng",
    "psm_mode": 6,
    "theme": "dark",
    "preprocess": {
        "enabled": True,
        "upscale_factor": 2.0,
        "auto_invert": True,
        "enhance_contrast": True,
        "binarize": False,
    },
    "notifications": {
        "enabled": True,
        "preview_max_chars": 45,
        "expire_time_ms": 3000,
    },
    "history": {
        "max_items": 50,
        "persist": True,
    },
    "overlay": {
        "highlight_color": "#3584e4",
        "highlight_opacity": 0.35,
        "border_color": "#78aeed",
        "show_confidence": False,
    }
}


def get_config_dir() -> Path:
    """Return XDG config path for live-text-ocr."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_config) if xdg_config else Path.home() / ".config"
    config_dir = base / "live-text-ocr"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """Return XDG data path for live-text-ocr."""
    xdg_data = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data) if xdg_data else Path.home() / ".local/share"
    data_dir = base / "live-text-ocr"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_cache_dir() -> Path:
    """Return XDG cache path for live-text-ocr."""
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg_cache) if xdg_cache else Path.home() / ".cache"
    cache_dir = base / "live-text-ocr"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_tessdata_dir() -> Path:
    """Return directory where downloaded .traineddata language models are stored."""
    tessdata_dir = get_config_dir() / "tessdata"
    tessdata_dir.mkdir(parents=True, exist_ok=True)
    return tessdata_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def load_config() -> Dict[str, Any]:
    """Load configuration from disk, falling back to defaults for missing keys."""
    cfg_path = get_config_path()
    config = dict(DEFAULT_CONFIG)
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                # Deep merge top-level dictionaries
                for k, v in user_cfg.items():
                    if isinstance(v, dict) and isinstance(config.get(k), dict):
                        config[k].update(v)
                    else:
                        config[k] = v
        except Exception:
            pass
    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to disk."""
    cfg_path = get_config_path()
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
