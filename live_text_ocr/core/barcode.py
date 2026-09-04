"""In-process Barcode and QR Code scanner using ctypes binding to libzbar.so.0."""

import ctypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image


LIBZBAR_PATHS = [
    "libzbar.so.0",
    "libzbar.so",
    "/usr/lib/x86_64-linux-gnu/libzbar.so.0",
    "/usr/lib/x86_64-linux-gnu/libzbar.so",
    "/usr/lib/aarch64-linux-gnu/libzbar.so.0",
    "/usr/lib/aarch64-linux-gnu/libzbar.so",
    "/usr/local/lib/libzbar.so.0",
    "/usr/local/lib/libzbar.so",
]


def _fourcc(a: str, b: str, c: str, d: str) -> int:
    return ord(a) | (ord(b) << 8) | (ord(c) << 16) | (ord(d) << 24)


@dataclass
class BarcodeItem:
    data: str
    type_name: str
    box: Tuple[int, int, int, int]  # (x, y, w, h)
    polygon: List[Tuple[int, int]]
    category: str  # 'url', 'wifi', 'email', 'otp', 'text', 'barcode'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": self.data,
            "type_name": self.type_name,
            "box": self.box,
            "polygon": self.polygon,
            "category": self.category,
        }


class BarcodeEngine:
    """High-performance in-process Barcode and QR Code decoder using libzbar."""

    def __init__(self):
        self.lib = self._load_library()
        self._setup_prototypes()

    def _load_library(self) -> ctypes.CDLL:
        for path in LIBZBAR_PATHS:
            try:
                return ctypes.CDLL(path)
            except OSError:
                continue
        try:
            return ctypes.CDLL("libzbar.so.0")
        except OSError as e:
            raise RuntimeError(f"Could not load libzbar.so.0: {e}")

    def _setup_prototypes(self):
        # Scanner functions
        self.lib.zbar_image_scanner_create.restype = ctypes.c_void_p
        self.lib.zbar_image_scanner_create.argtypes = []

        self.lib.zbar_image_scanner_destroy.restype = None
        self.lib.zbar_image_scanner_destroy.argtypes = [ctypes.c_void_p]

        self.lib.zbar_image_scanner_set_config.restype = ctypes.c_int
        self.lib.zbar_image_scanner_set_config.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
        ]

        # Image functions
        self.lib.zbar_image_create.restype = ctypes.c_void_p
        self.lib.zbar_image_create.argtypes = []

        self.lib.zbar_image_destroy.restype = None
        self.lib.zbar_image_destroy.argtypes = [ctypes.c_void_p]

        self.lib.zbar_image_set_format.restype = None
        self.lib.zbar_image_set_format.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

        self.lib.zbar_image_set_size.restype = None
        self.lib.zbar_image_set_size.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]

        self.lib.zbar_image_set_data.restype = None
        self.lib.zbar_image_set_data.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_void_p,
        ]

        # Scan & Symbol functions
        self.lib.zbar_scan_image.restype = ctypes.c_int
        self.lib.zbar_scan_image.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        self.lib.zbar_image_first_symbol.restype = ctypes.c_void_p
        self.lib.zbar_image_first_symbol.argtypes = [ctypes.c_void_p]

        self.lib.zbar_symbol_next.restype = ctypes.c_void_p
        self.lib.zbar_symbol_next.argtypes = [ctypes.c_void_p]

        self.lib.zbar_symbol_get_data.restype = ctypes.c_char_p
        self.lib.zbar_symbol_get_data.argtypes = [ctypes.c_void_p]

        self.lib.zbar_symbol_get_type.restype = ctypes.c_int
        self.lib.zbar_symbol_get_type.argtypes = [ctypes.c_void_p]

        self.lib.zbar_get_symbol_name.restype = ctypes.c_char_p
        self.lib.zbar_get_symbol_name.argtypes = [ctypes.c_int]

        self.lib.zbar_symbol_get_loc_size.restype = ctypes.c_uint
        self.lib.zbar_symbol_get_loc_size.argtypes = [ctypes.c_void_p]

        self.lib.zbar_symbol_get_loc_x.restype = ctypes.c_int
        self.lib.zbar_symbol_get_loc_x.argtypes = [ctypes.c_void_p, ctypes.c_uint]

        self.lib.zbar_symbol_get_loc_y.restype = ctypes.c_int
        self.lib.zbar_symbol_get_loc_y.argtypes = [ctypes.c_void_p, ctypes.c_uint]

    def detect(self, image: Image.Image) -> List[BarcodeItem]:
        """
        Scan a PIL Image for any QR codes or 1D/2D barcodes.
        Returns a list of BarcodeItem objects.
        """
        gray = image.convert("L")
        width, height = gray.size
        raw_bytes = gray.tobytes("raw", "L")
        c_buf = (ctypes.c_ubyte * len(raw_bytes)).from_buffer_copy(raw_bytes)

        scanner = self.lib.zbar_image_scanner_create()
        if not scanner:
            return []

        try:
            # Enable all symbologies (ZBAR_NONE=0, ZBAR_CFG_ENABLE=0, val=1)
            self.lib.zbar_image_scanner_set_config(scanner, 0, 0, 1)

            zimg = self.lib.zbar_image_create()
            if not zimg:
                return []

            try:
                # Set format Y800 (grayscale)
                self.lib.zbar_image_set_format(zimg, _fourcc("Y", "8", "0", "0"))
                self.lib.zbar_image_set_size(zimg, width, height)
                self.lib.zbar_image_set_data(zimg, ctypes.cast(c_buf, ctypes.c_void_p), len(raw_bytes), None)

                num_symbols = self.lib.zbar_scan_image(scanner, zimg)
                if num_symbols <= 0:
                    return []

                results: List[BarcodeItem] = []
                sym = self.lib.zbar_image_first_symbol(zimg)

                while sym:
                    raw_data = self.lib.zbar_symbol_get_data(sym)
                    data_str = raw_data.decode("utf-8", errors="replace") if raw_data else ""

                    type_id = self.lib.zbar_symbol_get_type(sym)
                    type_name_ptr = self.lib.zbar_get_symbol_name(type_id)
                    type_name = type_name_ptr.decode("utf-8") if type_name_ptr else "Unknown"

                    # Get polygon corners & bounding box
                    loc_size = self.lib.zbar_symbol_get_loc_size(sym)
                    polygon: List[Tuple[int, int]] = []
                    xs: List[int] = []
                    ys: List[int] = []

                    for i in range(loc_size):
                        x = int(self.lib.zbar_symbol_get_loc_x(sym, i))
                        y = int(self.lib.zbar_symbol_get_loc_y(sym, i))
                        polygon.append((x, y))
                        xs.append(x)
                        ys.append(y)

                    if xs and ys:
                        min_x, max_x = min(xs), max(xs)
                        min_y, max_y = min(ys), max(ys)
                        box = (min_x, min_y, max_x - min_x, max_y - min_y)
                    else:
                        box = (0, 0, width, height)

                    category = self._classify_content(data_str, type_name)

                    if data_str:
                        results.append(
                            BarcodeItem(
                                data=data_str,
                                type_name=type_name,
                                box=box,
                                polygon=polygon,
                                category=category,
                            )
                        )

                    sym = self.lib.zbar_symbol_next(sym)

                return results
            finally:
                self.lib.zbar_image_destroy(zimg)
        finally:
            self.lib.zbar_image_scanner_destroy(scanner)

    @staticmethod
    def _classify_content(data: str, type_name: str) -> str:
        """Classify decoded payload for smart UI actions and notifications."""
        s = data.strip()
        if re.match(r"^https?://[^\s]+$", s, re.IGNORECASE):
            return "url"
        if s.startswith("WIFI:"):
            return "wifi"
        if s.startswith("mailto:") or re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", s):
            return "email"
        if s.startswith("otpauth://"):
            return "otp"
        if "QR" in type_name.upper():
            return "text"
        return "barcode"


_global_engine: Optional[BarcodeEngine] = None


def detect_barcodes(image: Image.Image) -> List[BarcodeItem]:
    """Convenience helper to detect barcodes and QR codes from a PIL image."""
    global _global_engine
    if _global_engine is None:
        try:
            _global_engine = BarcodeEngine()
        except Exception:
            return []
    return _global_engine.detect(image)
