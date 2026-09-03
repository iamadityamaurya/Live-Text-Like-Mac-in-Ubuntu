"""Native Ubuntu Top Bar System Tray Indicator for Live Text OCR."""

import sys
import threading
import time
from typing import Optional

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
)

from live_text_ocr.config import load_config
from live_text_ocr.core.capture import capture_selected_region, CaptureCancelled
from live_text_ocr.core.clipboard import copy_to_clipboard
from live_text_ocr.core.history import get_history, log_history_entry
from live_text_ocr.core.notify import notify_error, notify_success
from live_text_ocr.core.ocr_engine import TesseractEngine
from live_text_ocr.core.preprocess import preprocess_image


def format_time_ago(timestamp: int) -> str:
    """Format timestamp into human-readable relative time (e.g., '5m ago', '1h ago')."""
    if not timestamp:
        return ""
    diff = max(0, int(time.time()) - timestamp)
    if diff < 60:
        return "just now"
    elif diff < 3600:
        return f"{diff // 60}m ago"
    elif diff < 86400:
        return f"{diff // 3600}h ago"
    else:
        return f"{diff // 86400}d ago"


def create_tray_icon() -> QIcon:
    """Create a crisp, modern vector-style OCR icon for the Ubuntu top panel."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Rounded background badge
    painter.setBrush(QColor(53, 132, 228))  # Ubuntu Blue
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 14, 14)

    # Text 'T' / OCR symbol
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Ubuntu", 30, QFont.Weight.Black)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    painter.end()

    return QIcon(pixmap)


class TrayCaptureWorker(QObject):
    finished = pyqtSignal(bool, str)

    def run(self):
        config = load_config()
        lang = config.get("ocr_language", "eng")
        psm = config.get("psm_mode", 6)

        try:
            time.sleep(0.1)
            image = capture_selected_region()
            if not image:
                self.finished.emit(True, "")
                return

            preprocess_cfg = config.get("preprocess", {})
            if preprocess_cfg.get("enabled", True):
                processed_img = preprocess_image(
                    image,
                    upscale_factor=preprocess_cfg.get("upscale_factor", 2.0),
                    auto_invert=preprocess_cfg.get("auto_invert", True),
                    enhance_contrast=preprocess_cfg.get("enhance_contrast", True),
                    binarize=preprocess_cfg.get("binarize", False),
                )
            else:
                processed_img = image

            engine = TesseractEngine(default_lang=lang)
            text = engine.extract_text(processed_img, lang=lang, psm=psm)
            if not text:
                text = engine.extract_text(image, lang=lang, psm=3)

            if not text:
                notify_error("No text detected in selected region.")
                self.finished.emit(True, "")
                return

            copy_to_clipboard(text)
            log_history_entry(text)

            notify_cfg = config.get("notifications", {})
            if notify_cfg.get("enabled", True):
                notify_success(
                    text,
                    max_chars=notify_cfg.get("preview_max_chars", 45),
                    expire_time_ms=notify_cfg.get("expire_time_ms", 3000),
                )

            self.finished.emit(True, text)
        except CaptureCancelled:
            self.finished.emit(True, "")
        except Exception as e:
            notify_error(f"OCR Error: {e}")
            self.finished.emit(False, str(e))


class LiveTextTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        icon = create_tray_icon()
        super().__init__(icon, parent)
        self.setToolTip("Live Text OCR - Click to Capture Screen Region")
        self.menu = QMenu()
        self._apply_menu_style()
        self.menu.aboutToShow.connect(self._rebuild_menu)
        self.setContextMenu(self.menu)
        self._rebuild_menu()
        self.activated.connect(self._on_activated)

    def _apply_menu_style(self):
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #24283b;
                color: #c0caf5;
                border: 1px solid #414868;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Ubuntu', sans-serif;
                font-size: 13px;
                min-width: 280px;
            }
            QMenu::item {
                padding: 7px 18px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: #3584e4;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #414868;
                margin: 4px 6px;
            }
        """)

    def _rebuild_menu(self):
        """Rebuild the menu directly with Capture, Direct History items, and Quit."""
        self.menu.clear()

        # 1. Capture Button (Top)
        action_capture = QAction("📸  Capture Region (Live Text)", self)
        action_capture.setFont(QFont("Ubuntu", 10, QFont.Weight.Bold))
        action_capture.triggered.connect(self.trigger_capture)
        self.menu.addAction(action_capture)

        self.menu.addSeparator()

        # 2. History Clips Directly in Menu
        history = get_history()
        if not history:
            no_action = self.menu.addAction("  (No clips recorded yet)")
            no_action.setEnabled(False)
        else:
            for item in history[:10]:
                text = item.get("text", "").replace("\n", " ").strip()
                preview = text[:32] + "..." if len(text) > 32 else text
                time_ago = format_time_ago(item.get("timestamp", 0))
                
                # Right-aligned time string spacing
                display_label = f"{preview:<35}  {time_ago}"
                act = self.menu.addAction(f"📄  {display_label}")
                # Bind click to re-copy
                act.triggered.connect(lambda checked, t=item["text"]: self._copy_and_notify(t))

        self.menu.addSeparator()

        # 3. Quit Button (Bottom)
        action_quit = QAction("❌  Quit Live Text", self)
        action_quit.triggered.connect(QApplication.quit)
        self.menu.addAction(action_quit)

    def _copy_and_notify(self, text: str):
        copy_to_clipboard(text)
        notify_success(text)

    def _on_activated(self, reason):
        # Left click triggers capture directly
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.trigger_capture()

    def trigger_capture(self):
        """Run OCR capture in a background thread."""
        self.worker = TrayCaptureWorker()
        self.thread = threading.Thread(target=self.worker.run, daemon=True)
        self.thread.start()


def start_tray():
    """Start the top panel tray indicator daemon."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = LiveTextTrayIcon()
    tray.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    start_tray()
