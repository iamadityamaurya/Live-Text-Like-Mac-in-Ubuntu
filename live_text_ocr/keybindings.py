"""GNOME global keybinding configuration helper."""

import ast
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from live_text_ocr.config import load_config
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
        if not val or val == "@as []" or val == "[]":
            return []
        if val.startswith("@as "):
            val = val[4:].strip()
        # Parse gsettings list format
        parsed = ast.literal_eval(val)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def get_current_shortcut(name: str = "Live Text OCR") -> Optional[str]:
    """Return the current GNOME shortcut binding for this app, if any."""
    for b_path in get_gnome_custom_bindings():
        try:
            b_name = subprocess.run(
                ["gsettings", "get", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{b_path}", "name"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip().strip("'\"")
            if b_name == name:
                binding = subprocess.run(
                    ["gsettings", "get", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{b_path}", "binding"],
                    capture_output=True,
                    text=True,
                    check=False,
                ).stdout.strip().strip("'\"")
                return binding
        except Exception:
            continue
    return None


def register_gnome_shortcut_by_name(
    name: str,
    command_path: str,
    binding: str,
) -> bool:
    """Register a named GNOME global shortcut, replacing any existing binding with the same name."""
    if not check_tool("gsettings"):
        return False

    existing_bindings = get_gnome_custom_bindings()
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
        index = 0
        while True:
            candidate = f"/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{index}/"
            if candidate not in existing_bindings:
                target_path = candidate
                break
            index += 1
        existing_bindings.append(target_path)

    schema = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{target_path}"
    try:
        # Ensure the path exists in the array before setting fields
        subprocess.run(
            ["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", str(existing_bindings)],
            check=True,
            capture_output=True,
        )
        subprocess.run(["gsettings", "set", schema, "name", name], check=True, capture_output=True)
        subprocess.run(["gsettings", "set", schema, "command", command_path], check=True, capture_output=True)
        subprocess.run(["gsettings", "set", schema, "binding", binding], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"gsettings error: {e.stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"register shortcut error: {e}", file=sys.stderr)
        return False


def register_gnome_shortcut(
    command_path: str,
    binding: Optional[str] = None,
    name: str = "Live Text OCR",
) -> Tuple[bool, str]:
    """Register or update a GNOME global shortcut."""
    default_binding = "<Super><Shift>c" if name == "Live Text OCR" else "<Super><Shift>o"
    binding = binding or default_binding
    ok = register_gnome_shortcut_by_name(name, command_path, binding)
    if ok:
        return True, binding

    if not check_tool("gsettings"):
        return False, "gsettings command not found. GNOME desktop environment is required."
    return False, "Failed to register shortcut"


def binding_to_display(binding: str) -> str:
    """Convert a gsettings binding string to a human readable shortcut."""
    if not binding:
        return "None"
    parts = binding.replace("<", " ").replace(">", " ").strip().split()
    return " + ".join(p.title() if not p.startswith("Shift") else "Shift" for p in parts)

