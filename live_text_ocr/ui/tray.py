"""Native Ubuntu Top Bar System Tray Indicator for Live Text OCR."""

import sys
import threading
import time
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
)

from live_text_ocr.config import load_config
from live_text_ocr.core.capture import capture_selected_region, CaptureCancelled
from live_text_ocr.core.clipboard import copy_to_clipboard
from live_text_ocr.core.history import (
    clear_history,
    delete_history_entry,
    get_history,
    log_history_entry,
    toggle_pin_entry,
)
from live_text_ocr.core.notify import notify_error, notify_success
from live_text_ocr.core.ocr_engine import TesseractEngine
from live_text_ocr.core.preprocess import preprocess_image


def create_tray_icon() -> QIcon:
    """Create a crisp, monochrome Live Text scan icon matching GNOME top panel."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(230, 230, 230), 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    m = 7
    l = 13

    # Corner brackets
    painter.drawLine(m, m + l, m, m)
    painter.drawLine(m, m, m + l, m)

    painter.drawLine(64 - m - l, m, 64 - m, m)
    painter.drawLine(64 - m, m, 64 - m, m + l)

    painter.drawLine(m, 64 - m - l, m, 64 - m)
    painter.drawLine(m, 64 - m, m + l, 64 - m)

    painter.drawLine(64 - m - l, 64 - m, 64 - m, 64 - m)
    painter.drawLine(64 - m, 64 - m - l, 64 - m, 64 - m)

    painter.setFont(QFont("Ubuntu", 26, QFont.Weight.Bold))
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
            time.sleep(0.12)
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
        self.setToolTip("Live Text OCR — Click to capture screen text")
        self.menu = QMenu()
        self._apply_menu_style()
        self.menu.aboutToShow.connect(self._rebuild_menu)
        self.setContextMenu(self.menu)
        self._rebuild_menu()
        self.activated.connect(self._on_activated)

    def _apply_menu_style(self):
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #242424;
                color: #e8e8e8;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                padding: 6px;
                font-family: 'Ubuntu', 'Inter', -apple-system, sans-serif;
                font-size: 13px;
                min-width: 320px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 6px;
                margin: 1px 0px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.10);
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.08);
                margin: 5px 8px;
            }
        """)

    def _rebuild_menu(self):
        """Rebuild the native top-panel dropdown menu."""
        self.menu.clear()

        # 1. Capture Action (Top)
        action_capture = QAction("⛶   Capture Text Selection", self)
        action_capture.setFont(QFont("Ubuntu", 10, QFont.Weight.Bold))
        action_capture.triggered.connect(self.trigger_capture)
        self.menu.addAction(action_capture)

        self.menu.addSeparator()

        # 2. History Items (with direct Pin & Delete sub-actions)
        history = get_history()
        if not history:
            no_action = self.menu.addAction("    (No history clips yet)")
            no_action.setEnabled(False)
        else:
            for item in history[:10]:
                raw_text = item.get("text", "").replace("\n", " ").strip()
                preview = raw_text[:32] + "..." if len(raw_text) > 32 else raw_text
                is_pinned = item.get("pinned", False)

                prefix = "📌" if is_pinned else "📄"
                item_label = f"{prefix}   {preview}"

                # Create item submenu with Copy, Pin/Unpin, Delete actions
                item_menu = self.menu.addMenu(item_label)
                
                # Copy Action
                act_copy = item_menu.addAction("📋   Copy to Clipboard")
                act_copy.triggered.connect(lambda checked, t=item["text"]: self._copy_and_notify(t))

                # Pin / Unpin Action
                pin_text = "📍   Unpin from Top" if is_pinned else "📌   Pin to Top"
                act_pin = item_menu.addAction(pin_text)
                act_pin.triggered.connect(lambda checked, e_id=item["id"]: self._toggle_pin(e_id))

                # Delete Action
                act_del = item_menu.addAction("🗑️   Delete Clip")
                act_del.triggered.connect(lambda checked, e_id=item["id"]: self._delete_entry(e_id))

            self.menu.addSeparator()

            clear_act = self.menu.addAction("🧹   Clear All History")
            clear_act.triggered.connect(self._clear_history)

        self.menu.addSeparator()

        # 3. Quit Button (Bottom)
        action_quit = QAction("✕   Quit Live Text", self)
        action_quit.triggered.connect(QApplication.quit)
        self.menu.addAction(action_quit)

    def _copy_and_notify(self, text: str):
        copy_to_clipboard(text)
        notify_success(text)

    def _toggle_pin(self, entry_id: str):
        toggle_pin_entry(entry_id)
        self._rebuild_menu()

    def _delete_entry(self, entry_id: str):
        delete_history_entry(entry_id)
        self._rebuild_menu()

    def _clear_history(self):
        clear_history()
        self._rebuild_menu()
        notify_success("History cleared.")

    def _on_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.trigger_capture()

    def trigger_capture(self):
        """Run OCR capture in background thread."""
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
