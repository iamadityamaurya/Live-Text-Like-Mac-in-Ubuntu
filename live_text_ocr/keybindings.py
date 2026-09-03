"""GNOME global keybinding configuration helper."""

import ast
import shutil
import subprocess
from pathlib import Path
from typing import Tuple

from live_text_ocr.core.session import check_tool


def get_gnome_custom_bindings() -> list:
    """Get current list of custom keybindings paths from gsettings."""
    try:
        res = subprocess.run(
            [
                "gsettings",
                "get",
                "org.gnome.settings-daemon.plugins.media-keys",
                "custom-keybindings",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        val = res.stdout.strip()
        if val == "@as []" or not val:
            return []
        # Parse gsettings list format
        return ast.literal_eval(val)
    except Exception:
        return []


def register_gnome_shortcut(
    command_path: str,
    binding: str = "<Super><Shift>o",
    name: str = "Live Text OCR",
) -> Tuple[bool, str]:
    """Register or update the global shortcut in GNOME settings."""
    if not check_tool("gsettings"):
        return False, "gsettings command not found. GNOME desktop environment is required."

    existing_bindings = get_gnome_custom_bindings()
    
    # Check if our custom keybinding already exists
    target_path = None
    for b_path in existing_bindings:
        try:
            b_name = subprocess.run(
                ["gsettings", "get", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{b_path}", "name"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip().strip("'\"")
            if b_name == name:
                target_path = b_path
                break
        except Exception:
            continue

    if not target_path:
        # Find next available index
        index = 0
        while True:
            candidate = f"/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{index}/"
            if candidate not in existing_bindings:
                target_path = candidate
                break
            index += 1
        existing_bindings.append(target_path)

    # Apply configuration
    schema = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{target_path}"
    try:
        subprocess.run(["gsettings", "set", schema, "name", f"'{name}'"], check=True)
        subprocess.run(["gsettings", "set", schema, "command", f"'{command_path}'"], check=True)
        subprocess.run(["gsettings", "set", schema, "binding", f"'{binding}'"], check=True)

        # Update keybindings array
        bindings_str = str(existing_bindings)
        subprocess.run(
            ["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", bindings_str],
            check=True,
        )
        return True, f"Shortcut {binding} successfully registered to command: {command_path}"
    except Exception as e:
        return False, f"Failed to register shortcut: {e}"
