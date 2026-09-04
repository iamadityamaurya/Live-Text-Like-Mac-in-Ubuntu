"""In-memory and portal screen region capture pipeline for Wayland and X11."""

import io
import os
import random
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional
from PIL import Image

from live_text_ocr.core.session import get_session_type, check_tool


class CaptureCancelled(Exception):
    """Raised when user cancels region selection (e.g., presses Escape)."""
    pass


def capture_selected_region() -> Optional[Image.Image]:
    """
    Prompt user to select a rectangular region on screen and return the captured image in memory.
    Returns None or raises CaptureCancelled if user cancels.
    """
    session = get_session_type()

    if session == "wayland":
        # On GNOME Wayland, portal is primary because slurp requires wlr-layer-shell
        try:
            return _capture_portal(interactive=True)
        except Exception as portal_err:
            # Fallback to slurp + grim (works on Sway / Hyprland / wlroots)
            try:
                return _capture_wayland_slurp()
            except Exception:
                raise portal_err
    else:
        return _capture_x11()


def capture_fullscreen() -> Optional[Image.Image]:
    """
    Capture the entire screen image in memory for Live Text interactive overlay.
    """
    session = get_session_type()

    if session == "wayland":
        try:
            return _capture_portal(interactive=False)
        except Exception:
            # Fallback to grim full screen if supported
            try:
                grim_bin = check_tool("grim")
                if grim_bin:
                    proc = subprocess.run([grim_bin, "-"], capture_output=True, check=True)
                    return Image.open(io.BytesIO(proc.stdout)).copy()
            except Exception:
                pass
            return _capture_qt_fallback()
    else:
        # X11 full screen capture
        maim_bin = check_tool("maim")
        scrot_bin = check_tool("scrot")
        if maim_bin:
            proc = subprocess.run([maim_bin, "-u"], capture_output=True, check=False)
            if proc.returncode == 0:
                return Image.open(io.BytesIO(proc.stdout)).copy()
        if scrot_bin:
            proc = subprocess.run([scrot_bin, "-o", "/dev/stdout"], capture_output=True, check=False)
            if proc.returncode == 0:
                return Image.open(io.BytesIO(proc.stdout)).copy()
        return _capture_qt_fallback()


def _capture_qt_fallback() -> Optional[Image.Image]:
    """Fallback full screen capture using PyQt6 screen grab."""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QGuiApplication
        from PyQt6.QtCore import QBuffer, QIODevice
        
        app = QApplication.instance() or QApplication([])
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return None
        pixmap = screen.grabWindow(0)
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.ReadWrite)
        pixmap.save(buffer, "PNG")
        return Image.open(io.BytesIO(buffer.data().data())).copy()
    except Exception as e:
        raise RuntimeError(f"Screen capture failed: {e}")


def _capture_portal(interactive: bool = True) -> Optional[Image.Image]:
    """Capture screen area on Wayland using standard XDG Desktop Portal."""
    try:
        import gi
        gi.require_version("Gio", "2.0")
        gi.require_version("GLib", "2.0")
        from gi.repository import Gio, GLib
    except ImportError as e:
        raise RuntimeError(f"PyGObject (gi.repository) is required for Wayland portal capture: {e}")

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    loop = GLib.MainLoop()
    result_data = {"code": 1, "uri": None}

    token = f"livetext_{random.randint(100000, 999999)}"
    sender = bus.get_unique_name().replace(".", "_").lstrip(":")
    handle_path = f"/org/freedesktop/portal/desktop/request/{sender}/{token}"

    def on_response(connection, sender_name, object_path, interface_name, signal_name, parameters, user_data):
        if signal_name == "Response":
            try:
                code, results = parameters.unpack()
                result_data["code"] = code
                if code == 0 and "uri" in results:
                    result_data["uri"] = results["uri"]
            finally:
                loop.quit()

    sub_id = bus.signal_subscribe(
        "org.freedesktop.portal.Desktop",
        "org.freedesktop.portal.Request",
        "Response",
        handle_path,
        None,
        Gio.DBusSignalFlags.NONE,
        on_response,
        None,
    )

    try:
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            "org.freedesktop.portal.Screenshot",
            None,
        )

        options = {
            "handle_token": GLib.Variant("s", token),
            "interactive": GLib.Variant("b", interactive),
        }

        proxy.call_sync(
            "Screenshot",
            GLib.Variant("(sa{sv})", ("", options)),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

        # Wait for user to interact with the screenshot selector (timeout 120s)
        timeout_id = GLib.timeout_add_seconds(120, loop.quit)
        loop.run()
        GLib.source_remove(timeout_id)
    finally:
        bus.signal_unsubscribe(sub_id)

    if result_data["code"] != 0 or not result_data["uri"]:
        raise CaptureCancelled("Region selection cancelled by user.")

    # Parse URI and load image
    parsed_url = urllib.parse.urlparse(result_data["uri"])
    file_path = urllib.parse.unquote(parsed_url.path)
    if not os.path.exists(file_path):
        raise RuntimeError(f"Captured screenshot file does not exist: {file_path}")

    try:
        with open(file_path, "rb") as f:
            image = Image.open(io.BytesIO(f.read()))
            image.load()
            return image.copy()
    finally:
        # If it was saved in /tmp or .cache or non-Pictures temp, clean it up
        if "/tmp/" in file_path or "/.cache/" in file_path:
            try:
                os.remove(file_path)
            except OSError:
                pass


def _capture_wayland_slurp() -> Optional[Image.Image]:
    """Capture selected screen area on wlroots-based Wayland using slurp and grim."""
    slurp_bin = check_tool("slurp")
    grim_bin = check_tool("grim")

    if not slurp_bin or not grim_bin:
        raise RuntimeError("Wayland screen capture requires 'slurp' and 'grim'.")

    slurp_cmd = [
        slurp_bin,
        "-b", "#00000055",
        "-c", "#3584e4",
        "-s", "#3584e422",
        "-w", "2",
    ]

    slurp_proc = subprocess.run(
        slurp_cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if slurp_proc.returncode != 0:
        raise CaptureCancelled("Region selection cancelled by user.")

    geometry = slurp_proc.stdout.strip()
    if not geometry:
        raise CaptureCancelled("No region selected.")

    grim_cmd = [grim_bin, "-g", geometry, "-"]
    grim_proc = subprocess.run(
        grim_cmd,
        capture_output=True,
        check=True,
    )

    png_bytes = grim_proc.stdout
    if not png_bytes:
        raise RuntimeError("Captured image data is empty.")

    image = Image.open(io.BytesIO(png_bytes))
    return image.copy()


def _capture_x11() -> Optional[Image.Image]:
    """Capture selected screen area on X11 using maim or scrot."""
    maim_bin = check_tool("maim")
    scrot_bin = check_tool("scrot")

    if maim_bin:
        proc = subprocess.run(
            [maim_bin, "-s", "-u"],
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise CaptureCancelled("Region selection cancelled.")
        return Image.open(io.BytesIO(proc.stdout)).copy()

    elif scrot_bin:
        proc = subprocess.run(
            [scrot_bin, "-s", "-o", "/dev/stdout"],
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise CaptureCancelled("Region selection cancelled.")
        return Image.open(io.BytesIO(proc.stdout)).copy()
    else:
        raise RuntimeError("X11 screen capture requires 'maim' or 'scrot'.")
