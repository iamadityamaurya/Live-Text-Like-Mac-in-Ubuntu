"""Linux session and environment detection (Wayland / X11)."""

import os
import shutil
from typing import Dict, Optional


def get_session_type() -> str:
    """Return 'wayland', 'x11', or 'unknown'."""
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session_type in ("wayland", "x11"):
        return session_type

    # Fallback checks
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def check_tool(name: str) -> Optional[str]:
    """Check if a CLI executable exists in PATH."""
    return shutil.which(name)


def inspect_environment() -> Dict[str, any]:
    """Inspect the desktop environment and available tools."""
    session = get_session_type()
    tools = {
        "grim": check_tool("grim"),
        "slurp": check_tool("slurp"),
        "maim": check_tool("maim"),
        "scrot": check_tool("scrot"),
        "wl-copy": check_tool("wl-copy"),
        "wl-paste": check_tool("wl-paste"),
        "xclip": check_tool("xclip"),
        "xsel": check_tool("xsel"),
        "notify-send": check_tool("notify-send"),
    }
    return {
        "session_type": session,
        "desktop": os.environ.get("XDG_CURRENT_DESKTOP", "unknown"),
        "tools": tools,
        "is_wayland": session == "wayland",
        "is_x11": session == "x11",
    }
