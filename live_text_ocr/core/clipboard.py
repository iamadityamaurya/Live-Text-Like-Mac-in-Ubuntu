"""System clipboard dispatcher for Wayland and X11."""

import subprocess
from live_text_ocr.core.session import get_session_type, check_tool


def copy_to_clipboard(text: str) -> bool:
    """Copy text directly to the system clipboard across Wayland and X11."""
    if not text:
        return False

    session = get_session_type()

    # Try Wayland clipboard first if on Wayland
    if session == "wayland" or check_tool("wl-copy"):
        wl_copy = check_tool("wl-copy")
        if wl_copy:
            try:
                # Spawn wl-copy in a new session to avoid blocking
                subprocess.Popen(
                    [wl_copy, "--type", "text/plain;charset=utf-8", text],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
            except Exception:
                pass

    # Try X11 xclip
    xclip = check_tool("xclip")
    if xclip:
        try:
            proc = subprocess.Popen(
                [xclip, "-selection", "clipboard"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.communicate(input=text.encode("utf-8"), timeout=2)
            return True
        except Exception:
            pass

    # Try X11 xsel
    xsel = check_tool("xsel")
    if xsel:
        try:
            proc = subprocess.Popen(
                [xsel, "-b", "-i"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.communicate(input=text.encode("utf-8"), timeout=2)
            return True
        except Exception:
            pass

    return False
