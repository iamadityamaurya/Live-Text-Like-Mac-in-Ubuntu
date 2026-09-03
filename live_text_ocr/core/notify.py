"""Desktop notification helper."""

import subprocess
from live_text_ocr.core.session import check_tool


def send_notification(
    title: str,
    message: str,
    expire_time_ms: int = 3000,
    icon: str = "edit-copy",
    urgency: str = "low",
) -> None:
    """Send a desktop notification via notify-send."""
    notify_send = check_tool("notify-send")
    if not notify_send:
        return

    cmd = [
        notify_send,
        "-a", "Live Text OCR",
        "-t", str(expire_time_ms),
        "-i", icon,
        "-u", urgency,
        title,
        message,
    ]
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception:
        pass


def notify_success(text: str, max_chars: int = 45, expire_time_ms: int = 3000) -> None:
    """Notify user that text was successfully extracted and copied."""
    first_line = text.splitlines()[0] if text else ""
    if len(first_line) > max_chars:
        preview = first_line[:max_chars].strip() + "..."
    else:
        preview = first_line

    if len(text.splitlines()) > 1:
        preview += f" (+{len(text.splitlines()) - 1} more lines)"

    send_notification(
        title="Copied to Clipboard",
        message=f'"{preview}"',
        expire_time_ms=expire_time_ms,
        icon="edit-copy",
        urgency="low",
    )


def notify_error(message: str) -> None:
    """Notify user of an OCR or capture error."""
    send_notification(
        title="Live Text OCR",
        message=message,
        expire_time_ms=4000,
        icon="dialog-warning",
        urgency="normal",
    )
