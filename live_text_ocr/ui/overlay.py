"""Interactive macOS-style Live Text Screen Overlay for Linux with QR & Barcode detection."""

import io
import sys
import urllib.parse
import webbrowser
from typing import Any, Dict, List, Optional, Set, Tuple
from PIL import Image

from PyQt6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QIcon,
    QImage,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from live_text_ocr.config import load_config
from live_text_ocr.core.clipboard import copy_to_clipboard
from live_text_ocr.core.history import log_history_entry
from live_text_ocr.core.notify import notify_success


def pil_to_qpixmap(pil_image: Image.Image) -> QPixmap:
    """Convert a PIL Image to a QPixmap with high fidelity."""
    if pil_image.mode != "RGBA":
        pil_image = pil_image.convert("RGBA")
    data = pil_image.tobytes("raw", "RGBA")
    qimg = QImage(
        data,
        pil_image.size[0],
        pil_image.size[1],
        QImage.Format.Format_RGBA8888,
    )
    return QPixmap.fromImage(qimg)


class FloatingToolbar(QWidget):
    """Floating Glassmorphism Action Toolbar for selected text or QR/Barcode."""

    copy_requested = pyqtSignal()
    select_all_requested = pyqtSignal()
    search_requested = pyqtSignal()
    translate_requested = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Status / count badge
        self.lbl_status = QLabel("0 selected")
        self.lbl_status.setStyleSheet("""
            QLabel {
                color: #8bb4f7;
                font-family: 'Ubuntu', 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding-right: 6px;
            }
        """)
        layout.addWidget(self.lbl_status)

        # Copy Button
        self.btn_copy = self._create_btn("📋  Copy", self.copy_requested.emit, primary=True)
        self.btn_copy.setToolTip("Copy selected text or code to clipboard (Enter / Ctrl+C)")
        layout.addWidget(self.btn_copy)

        # Select All Button
        self.btn_all = self._create_btn("📑  Select All", self.select_all_requested.emit)
        self.btn_all.setToolTip("Select all detected text on screen (Ctrl+A)")
        layout.addWidget(self.btn_all)

        # Web Search / Open URL Button
        self.btn_search = self._create_btn("🔍  Search", self.search_requested.emit)
        self.btn_search.setToolTip("Search on Google or open URL in browser")
        layout.addWidget(self.btn_search)

        # Translate Button
        self.btn_trans = self._create_btn("🌐  Translate", self.translate_requested.emit)
        self.btn_trans.setToolTip("Translate selected text")
        layout.addWidget(self.btn_trans)

        # Close Button
        self.btn_close = self._create_btn("✕", self.close_requested.emit, close=True)
        self.btn_close.setToolTip("Close Live Text overlay (Esc)")
        layout.addWidget(self.btn_close)

        self.setStyleSheet("""
            FloatingToolbar {
                background-color: rgba(26, 26, 30, 0.94);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 14px;
            }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

    def _create_btn(self, text: str, callback, primary: bool = False, close: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)

        if primary:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3584e4;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-family: 'Ubuntu', 'Inter', sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #4a90e8;
                }
                QPushButton:pressed {
                    background-color: #2a6ec2;
                }
            """)
        elif close:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #e0e0e0;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-family: 'Ubuntu', 'Inter', sans-serif;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(220, 53, 69, 0.85);
                    color: #ffffff;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #e6e6e6;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-family: 'Ubuntu', 'Inter', sans-serif;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.16);
                    color: #ffffff;
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.05);
                }
            """)
        return btn

    def update_status(self, text: str, has_selection: bool = True, is_url: bool = False):
        self.lbl_status.setText(text)
        self.btn_copy.setEnabled(has_selection)
        self.btn_search.setEnabled(has_selection)
        self.btn_trans.setEnabled(has_selection)
        if is_url:
            self.btn_search.setText("🔗  Open URL")
        else:
            self.btn_search.setText("🔍  Search")


class LiveTextOverlayWindow(QWidget):
    """Full-screen interactive macOS-style Live Text recognition overlay with QR/Barcode support."""

    def __init__(self, screenshot: Image.Image, layout_data: Dict[str, Any]):
        super().__init__()
        self.screenshot_img = screenshot
        self.layout_data = layout_data
        self.words: List[Dict[str, Any]] = layout_data.get("words", [])
        self.lines: List[Dict[str, Any]] = layout_data.get("lines", [])
        self.barcodes: List[Dict[str, Any]] = layout_data.get("barcodes", [])
        self.img_width, self.img_height = screenshot.size

        self.selected_indices: Set[int] = set()
        self.hovered_index: Optional[int] = None
        self.selected_barcode_idx: Optional[int] = None
        self.hovered_barcode_idx: Optional[int] = None

        self.is_dragging: bool = False
        self.drag_start: Optional[QPoint] = None
        self.drag_current: Optional[QPoint] = None

        self.background_pixmap = pil_to_qpixmap(screenshot)

        self._setup_window()
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.showFullScreen()

    def _setup_ui(self):
        self.toolbar = FloatingToolbar(self)
        self.toolbar.copy_requested.connect(self.copy_selection)
        self.toolbar.select_all_requested.connect(self.select_all)
        self.toolbar.search_requested.connect(self.search_selection)
        self.toolbar.translate_requested.connect(self.translate_selection)
        self.toolbar.close_requested.connect(self.close)

        self.toolbar.adjustSize()
        self._reposition_toolbar()
        self.toolbar.update_status("Hover or Drag text", has_selection=False)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.close)
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, self.copy_selection)
        QShortcut(QKeySequence(Qt.Key.Key_Enter), self, self.copy_selection)
        QShortcut(QKeySequence.StandardKey.Copy, self, self.copy_selection)
        QShortcut(QKeySequence.StandardKey.SelectAll, self, self.select_all)

    def _reposition_toolbar(self):
        tb_w = self.toolbar.sizeHint().width()
        tb_h = self.toolbar.sizeHint().height()
        x = max(20, (self.width() - tb_w) // 2)
        y = 28
        self.toolbar.setGeometry(x, y, tb_w, tb_h)

    def _get_scale(self) -> Tuple[float, float]:
        w = max(1, self.width())
        h = max(1, self.height())
        scale_x = w / self.img_width
        scale_y = h / self.img_height
        return scale_x, scale_y

    def _word_rect_on_screen(self, word_box: Tuple[int, int, int, int]) -> QRectF:
        scale_x, scale_y = self._get_scale()
        bx, by, bw, bh = word_box
        pad_x = 2
        pad_y = 2
        return QRectF(
            bx * scale_x - pad_x,
            by * scale_y - pad_y,
            bw * scale_x + (pad_x * 2),
            bh * scale_y + (pad_y * 2),
        )

    def _barcode_rect_on_screen(self, box: Tuple[int, int, int, int]) -> QRectF:
        scale_x, scale_y = self._get_scale()
        bx, by, bw, bh = box
        pad = 6
        return QRectF(
            bx * scale_x - pad,
            by * scale_y - pad,
            bw * scale_x + (pad * 2),
            bh * scale_y + (pad * 2),
        )

    def _find_word_at_pos(self, pos: QPoint) -> Optional[int]:
        for i, word in enumerate(self.words):
            rect = self._word_rect_on_screen(word["box"])
            expanded = rect.adjusted(-4, -4, 4, 4)
            if expanded.contains(QPointF(pos)):
                return i
        return None

    def _find_barcode_at_pos(self, pos: QPoint) -> Optional[int]:
        for i, b in enumerate(self.barcodes):
            rect = self._barcode_rect_on_screen(b["box"])
            if rect.contains(QPointF(pos)):
                return i
        return None

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. Background Screenshot
        painter.drawPixmap(self.rect(), self.background_pixmap)

        # 2. Subtle Dark Scrim
        scrim_color = QColor(10, 12, 16, 80)
        painter.fillRect(self.rect(), scrim_color)

        # 3. Draw Barcodes & QR Codes (Emerald Glow)
        for i, b in enumerate(self.barcodes):
            rect = self._barcode_rect_on_screen(b["box"])
            is_sel = i == self.selected_barcode_idx
            is_hov = i == self.hovered_barcode_idx

            path = QPainterPath()
            path.addRoundedRect(rect, 8.0, 8.0)

            if is_sel:
                fill_color = QColor(46, 194, 126, 170)
                border_color = QColor(255, 255, 255, 245)
                pen_w = 2.2
            elif is_hov:
                fill_color = QColor(46, 194, 126, 100)
                border_color = QColor(87, 227, 137, 240)
                pen_w = 2.0
            else:
                fill_color = QColor(46, 194, 126, 35)
                border_color = QColor(46, 194, 126, 180)
                pen_w = 1.4

            painter.fillPath(path, QBrush(fill_color))
            painter.setPen(QPen(border_color, pen_w))
            painter.drawPath(path)

            # Badge on top of Barcode
            tag_text = f"📱 {b['type_name']}" if "QR" in b["type_name"].upper() else f"📊 {b['type_name']}"
            tag_rect = QRectF(rect.x() + 4, rect.y() - 22, max(90, len(tag_text) * 7.5), 20)
            if tag_rect.y() < 10:
                tag_rect.moveTop(rect.y() + 6)

            tag_path = QPainterPath()
            tag_path.addRoundedRect(tag_rect, 4.0, 4.0)
            painter.fillPath(tag_path, QBrush(QColor(20, 20, 24, 225)))
            painter.setPen(QPen(QColor(46, 194, 126, 220), 1.0))
            painter.drawPath(tag_path)

            painter.setFont(QFont("Ubuntu", 9, QFont.Weight.Bold))
            painter.setPen(QColor(240, 255, 245))
            painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, tag_text)

        # 4. Draw Detected Text Elements (Accent Blue)
        for i, word in enumerate(self.words):
            rect = self._word_rect_on_screen(word["box"])
            is_selected = i in self.selected_indices
            is_hovered = i == self.hovered_index

            path = QPainterPath()
            path.addRoundedRect(rect, 4.0, 4.0)

            if is_selected:
                fill_color = QColor(53, 132, 228, 175)
                border_color = QColor(255, 255, 255, 240)
                painter.fillPath(path, QBrush(fill_color))
                painter.setPen(QPen(border_color, 1.6))
                painter.drawPath(path)
            elif is_hovered:
                fill_color = QColor(53, 132, 228, 110)
                border_color = QColor(120, 174, 237, 230)
                painter.fillPath(path, QBrush(fill_color))
                painter.setPen(QPen(border_color, 1.8, Qt.PenStyle.SolidLine))
                painter.drawPath(path)
            else:
                fill_color = QColor(53, 132, 228, 25)
                border_color = QColor(120, 174, 237, 85)
                painter.fillPath(path, QBrush(fill_color))
                painter.setPen(QPen(border_color, 1.0, Qt.PenStyle.SolidLine))
                painter.drawPath(path)

        # 5. Draw Drag Selection Marquee
        if self.is_dragging and self.drag_start and self.drag_current:
            drag_rect = QRect(self.drag_start, self.drag_current).normalized()
            painter.setPen(QPen(QColor(120, 174, 237, 220), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(QColor(53, 132, 228, 45)))
            painter.drawRoundedRect(drag_rect, 6, 6)

        # 6. Bottom-Right Live Text Badge
        self._draw_live_text_badge(painter)

    def _draw_live_text_badge(self, painter: QPainter):
        """Draw macOS-style Live Text indicator badge in bottom right corner."""
        badge_w, badge_h = 190, 36
        x = self.width() - badge_w - 24
        y = self.height() - badge_h - 24
        badge_rect = QRectF(x, y, badge_w, badge_h)

        path = QPainterPath()
        path.addRoundedRect(badge_rect, 18, 18)

        painter.fillPath(path, QBrush(QColor(24, 24, 28, 220)))
        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.0))
        painter.drawPath(path)

        count_str = f"{len(self.words)} words"
        if self.barcodes:
            count_str += f" • {len(self.barcodes)} codes"

        painter.setFont(QFont("Ubuntu", 11, QFont.Weight.DemiBold))
        painter.setPen(QColor(240, 240, 240))
        text = f"Live Text • {count_str}"
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, text)

    # --- Mouse Event Handlers ---

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.pos()

        if self.is_dragging:
            self.drag_current = pos
            drag_rect = QRect(self.drag_start, self.drag_current).normalized()
            new_selection = set()
            for i, word in enumerate(self.words):
                w_rect = self._word_rect_on_screen(word["box"]).toRect()
                if drag_rect.intersects(w_rect):
                    new_selection.add(i)

            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.selected_indices.update(new_selection)
            else:
                self.selected_indices = new_selection

            self.selected_barcode_idx = None
            count = len(self.selected_indices)
            self.toolbar.update_status(f"{count} words", has_selection=count > 0)
            self.update()
            return

        # Check barcode hover
        hov_bar = self._find_barcode_at_pos(pos)
        if hov_bar != self.hovered_barcode_idx:
            self.hovered_barcode_idx = hov_bar
            if hov_bar is not None:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.update()

        if hov_bar is not None:
            return

        # Check word hover
        hovered = self._find_word_at_pos(pos)
        if hovered != self.hovered_index:
            self.hovered_index = hovered
            if hovered is not None:
                self.setCursor(Qt.CursorShape.IBeamCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()

            # Check if clicked on a barcode
            clicked_bar = self._find_barcode_at_pos(pos)
            if clicked_bar is not None:
                self.selected_barcode_idx = clicked_bar
                self.selected_indices.clear()
                b = self.barcodes[clicked_bar]
                is_url = b.get("category") == "url"
                preview = b["data"][:25] + "..." if len(b["data"]) > 25 else b["data"]
                self.toolbar.update_status(f"[{b['type_name']}] {preview}", has_selection=True, is_url=is_url)
                self.update()
                return

            # Check if clicked on a word
            clicked_word = self._find_word_at_pos(pos)
            if clicked_word is not None:
                self.selected_barcode_idx = None
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    if clicked_word in self.selected_indices:
                        self.selected_indices.remove(clicked_word)
                    else:
                        self.selected_indices.add(clicked_word)
                else:
                    self.selected_indices = {clicked_word}

                count = len(self.selected_indices)
                self.toolbar.update_status(f"{count} words", has_selection=count > 0)
                self.update()
            else:
                # Start drag selection marquee
                self.selected_barcode_idx = None
                self.is_dragging = True
                self.drag_start = pos
                self.drag_current = pos
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self.selected_indices.clear()
                    self.toolbar.update_status("Hover or Drag text", has_selection=False)
                self.update()

        elif event.button() == Qt.MouseButton.RightButton:
            if self.selected_indices or self.selected_barcode_idx is not None:
                self.selected_indices.clear()
                self.selected_barcode_idx = None
                self.toolbar.update_status("Hover or Drag text", has_selection=False)
                self.update()
            else:
                self.close()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.drag_start = None
            self.drag_current = None
            count = len(self.selected_indices)
            self.toolbar.update_status(f"{count} words", has_selection=count > 0)
            self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double click directly copies clicked item or opens URL."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            clicked_bar = self._find_barcode_at_pos(pos)
            if clicked_bar is not None:
                self.selected_barcode_idx = clicked_bar
                self.selected_indices.clear()
                b = self.barcodes[clicked_bar]
                if b.get("category") == "url":
                    webbrowser.open(b["data"])
                self.copy_selection()
                return

            clicked_word = self._find_word_at_pos(pos)
            if clicked_word is not None:
                target_line = self.words[clicked_word].get("line_idx", -1)
                if target_line != -1:
                    line_words = [
                        i for i, w in enumerate(self.words) if w.get("line_idx") == target_line
                    ]
                    self.selected_indices = set(line_words)
                else:
                    self.selected_indices = {clicked_word}
                self.copy_selection()

    # --- Actions ---

    def get_selected_text(self) -> str:
        """Extract text from selected barcode or word indices."""
        if self.selected_barcode_idx is not None and self.selected_barcode_idx < len(self.barcodes):
            return self.barcodes[self.selected_barcode_idx]["data"]

        if not self.selected_indices:
            if self.barcodes:
                return self.barcodes[0]["data"]
            return self.layout_data.get("full_text", "")

        sorted_indices = sorted(self.selected_indices)
        words_selected = [self.words[i] for i in sorted_indices]

        lines_dict: Dict[int, List[str]] = {}
        for w in words_selected:
            l_idx = w.get("line_idx", 0)
            if l_idx not in lines_dict:
                lines_dict[l_idx] = []
            lines_dict[l_idx].append(w["text"])

        result_lines = []
        for l_idx in sorted(lines_dict.keys()):
            result_lines.append(" ".join(lines_dict[l_idx]))

        return "\n".join(result_lines).strip()

    def copy_selection(self):
        """Copy selected text / code to clipboard and close overlay."""
        text = self.get_selected_text()
        if not text:
            self.close()
            return

        copy_to_clipboard(text)
        log_history_entry(text)

        config = load_config()
        if config.get("notifications", {}).get("enabled", True):
            if self.selected_barcode_idx is not None:
                b = self.barcodes[self.selected_barcode_idx]
                icon = "📱" if "QR" in b["type_name"].upper() else "📊"
                notify_success(f"{icon} [{b['type_name']}] {text}")
            else:
                notify_success(text)

        self.close()

    def select_all(self):
        """Select all detected words on screen."""
        self.selected_barcode_idx = None
        self.selected_indices = set(range(len(self.words)))
        count = len(self.selected_indices)
        self.toolbar.update_status(f"{count} words", has_selection=count > 0)
        self.update()

    def search_selection(self):
        """Search selected text on Google or open URL."""
        text = self.get_selected_text()
        if text:
            if text.startswith("http://") or text.startswith("https://"):
                webbrowser.open(text)
            else:
                url = f"https://www.google.com/search?q={urllib.parse.quote(text)}"
                webbrowser.open(url)
            self.close()

    def translate_selection(self):
        """Open Google Translate with selected text."""
        text = self.get_selected_text()
        if text:
            url = f"https://translate.google.com/?sl=auto&tl=en&text={urllib.parse.quote(text)}&op=translate"
            webbrowser.open(url)
            self.close()


def launch_live_overlay(screenshot: Optional[Image.Image] = None, lang: str = "eng", psm: int = 3):
    """Launch the interactive Live Text overlay session with OCR and QR/Barcode scanning."""
    from live_text_ocr.core.capture import capture_fullscreen
    from live_text_ocr.core.ocr_engine import TesseractEngine
    from live_text_ocr.core.barcode import detect_barcodes

    app = QApplication.instance() or QApplication(sys.argv)

    if screenshot is None:
        screenshot = capture_fullscreen()
        if not screenshot:
            print("Failed to capture screen.")
            return 1

    engine = TesseractEngine(default_lang=lang)
    layout = engine.extract_layout(screenshot, lang=lang, psm=psm)

    # Scan for QR & Barcodes
    barcodes = detect_barcodes(screenshot)
    layout["barcodes"] = [b.to_dict() for b in barcodes]

    overlay = LiveTextOverlayWindow(screenshot, layout)
    overlay.show()
    return app.exec()
