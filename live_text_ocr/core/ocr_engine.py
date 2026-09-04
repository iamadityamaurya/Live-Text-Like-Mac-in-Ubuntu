"""Tesseract OCR Engine wrapper using ctypes C-API and tessdata manager."""

import ctypes
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import List, Optional
from PIL import Image

from live_text_ocr.config import get_tessdata_dir


# Candidate paths for libtesseract shared library
LIBTESSERACT_PATHS = [
    "/usr/lib/x86_64-linux-gnu/libtesseract.so.5",
    "/usr/lib/x86_64-linux-gnu/libtesseract.so",
    "/usr/lib/aarch64-linux-gnu/libtesseract.so.5",
    "/usr/lib/aarch64-linux-gnu/libtesseract.so",
    "/usr/local/lib/libtesseract.so.5",
    "/usr/local/lib/libtesseract.so",
    "libtesseract.so.5",
    "libtesseract.so",
]

# Standard Tessdata fast repository
TESSDATA_FAST_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/{lang}.traineddata"


def ensure_language_data(lang: str = "eng") -> Path:
    """Ensure that the requested language traineddata exists; download if missing."""
    tessdata_dir = get_tessdata_dir()
    lang_file = tessdata_dir / f"{lang}.traineddata"
    
    # Also check system tessdata locations
    system_locations = [
        Path(f"/usr/share/tesseract-ocr/5/tessdata/{lang}.traineddata"),
        Path(f"/usr/share/tessdata/{lang}.traineddata"),
        Path(f"/usr/share/tesseract-ocr/4.00/tessdata/{lang}.traineddata"),
    ]
    for loc in system_locations:
        if loc.exists():
            return loc.parent

    if lang_file.exists() and lang_file.stat().st_size > 0:
        return tessdata_dir

    # Download traineddata
    url = TESSDATA_FAST_URL.format(lang=lang)
    print(f"Downloading language model for '{lang}' from {url}...")
    try:
        urllib.request.urlretrieve(url, str(lang_file))
        print(f"Successfully downloaded {lang}.traineddata to {lang_file}")
    except Exception as e:
        if lang_file.exists():
            lang_file.unlink()
        raise RuntimeError(f"Failed to download traineddata for language '{lang}': {e}")

    return tessdata_dir


class TesseractEngine:
    """High-performance in-process Tesseract OCR engine using ctypes."""

    def __init__(self, default_lang: str = "eng"):
        self.default_lang = default_lang
        self.lib = self._load_library()
        self._setup_function_signatures()

    def _load_library(self) -> ctypes.CDLL:
        """Find and load libtesseract shared library."""
        for path in LIBTESSERACT_PATHS:
            try:
                return ctypes.CDLL(path)
            except OSError:
                continue
        # Last resort: let OS loader find it
        try:
            return ctypes.CDLL("libtesseract.so")
        except OSError as e:
            raise RuntimeError(
                f"Could not load libtesseract.so. Ensure libtesseract5 is installed on Ubuntu: {e}"
            )

    def _setup_function_signatures(self) -> None:
        """Set up ctypes prototypes for Tesseract C API."""
        self.lib.TessBaseAPICreate.restype = ctypes.c_void_p
        self.lib.TessBaseAPICreate.argtypes = []

        self.lib.TessBaseAPIDelete.restype = None
        self.lib.TessBaseAPIDelete.argtypes = [ctypes.c_void_p]

        self.lib.TessBaseAPIInit3.restype = ctypes.c_int
        self.lib.TessBaseAPIInit3.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]

        self.lib.TessBaseAPISetPageSegMode.restype = None
        self.lib.TessBaseAPISetPageSegMode.argtypes = [ctypes.c_void_p, ctypes.c_int]

        self.lib.TessBaseAPISetImage.restype = None
        self.lib.TessBaseAPISetImage.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
        ]

        self.lib.TessBaseAPIGetUTF8Text.restype = ctypes.c_void_p
        self.lib.TessBaseAPIGetUTF8Text.argtypes = [ctypes.c_void_p]

        self.lib.TessDeleteText.restype = None
        self.lib.TessDeleteText.argtypes = [ctypes.c_void_p]

        self.lib.TessBaseAPIEnd.restype = None
        self.lib.TessBaseAPIEnd.argtypes = [ctypes.c_void_p]

        # Layout analysis / ResultIterator prototypes
        self.lib.TessBaseAPIRecognize.restype = ctypes.c_int
        self.lib.TessBaseAPIRecognize.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        self.lib.TessBaseAPIGetIterator.restype = ctypes.c_void_p
        self.lib.TessBaseAPIGetIterator.argtypes = [ctypes.c_void_p]

        self.lib.TessResultIteratorGetUTF8Text.restype = ctypes.c_void_p
        self.lib.TessResultIteratorGetUTF8Text.argtypes = [ctypes.c_void_p, ctypes.c_int]

        self.lib.TessPageIteratorBoundingBox.restype = ctypes.c_int
        self.lib.TessPageIteratorBoundingBox.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        ]

        self.lib.TessResultIteratorConfidence.restype = ctypes.c_float
        self.lib.TessResultIteratorConfidence.argtypes = [ctypes.c_void_p, ctypes.c_int]

        self.lib.TessPageIteratorNext.restype = ctypes.c_int
        self.lib.TessPageIteratorNext.argtypes = [ctypes.c_void_p, ctypes.c_int]

        self.lib.TessPageIteratorIsAtBeginningOf.restype = ctypes.c_int
        self.lib.TessPageIteratorIsAtBeginningOf.argtypes = [ctypes.c_void_p, ctypes.c_int]

        self.lib.TessPageIteratorDelete.restype = None
        self.lib.TessPageIteratorDelete.argtypes = [ctypes.c_void_p]

    def extract_text(
        self,
        image: Image.Image,
        lang: Optional[str] = None,
        psm: int = 6,
    ) -> str:
        """
        Extract plain text from a PIL Image instance.
        
        :param image: PIL Image object (RGB, L, etc.)
        :param lang: OCR language code ('eng', 'fra', 'deu', etc.)
        :param psm: Page segmentation mode (default 6 = uniform block of text, 3 = fully automatic)
        """
        target_lang = lang or self.default_lang
        tessdata_path = ensure_language_data(target_lang)

        api = self.lib.TessBaseAPICreate()
        if not api:
            raise RuntimeError("Failed to create TessBaseAPI instance")

        try:
            init_res = self.lib.TessBaseAPIInit3(
                api,
                str(tessdata_path).encode("utf-8"),
                target_lang.encode("utf-8"),
            )
            if init_res != 0:
                raise RuntimeError(
                    f"TessBaseAPIInit3 failed with code {init_res} for language '{target_lang}' and path '{tessdata_path}'"
                )

            self.lib.TessBaseAPISetPageSegMode(api, psm)

            # Ensure grayscale image for optimal byte packing
            gray_img = image.convert("L")
            img_bytes = gray_img.tobytes("raw", "L")
            width, height = gray_img.size

            self.lib.TessBaseAPISetImage(
                api,
                img_bytes,
                width,
                height,
                1,  # bytes_per_pixel
                width,  # bytes_per_line
            )

            text_ptr = self.lib.TessBaseAPIGetUTF8Text(api)
            if not text_ptr:
                return ""

            try:
                raw_bytes = ctypes.cast(text_ptr, ctypes.c_char_p).value
                text = raw_bytes.decode("utf-8", errors="replace") if raw_bytes else ""
            finally:
                self.lib.TessDeleteText(text_ptr)

            return self.clean_text(text)
        finally:
            self.lib.TessBaseAPIEnd(api)
            self.lib.TessBaseAPIDelete(api)

    def extract_layout(
        self,
        image: Image.Image,
        lang: Optional[str] = None,
        psm: int = 3,
        min_conf: float = 20.0,
    ) -> dict:
        """
        Extract detailed word and line bounding boxes for interactive Live Text overlay.
        
        Returns a dictionary containing:
          - 'words': list of dicts: {'text', 'box': (x, y, w, h), 'conf', 'line_idx', 'block_idx'}
          - 'lines': list of dicts: {'text', 'box': (x, y, w, h), 'line_idx', 'block_idx'}
          - 'full_text': full recognized string
        """
        target_lang = lang or self.default_lang
        tessdata_path = ensure_language_data(target_lang)

        api = self.lib.TessBaseAPICreate()
        if not api:
            raise RuntimeError("Failed to create TessBaseAPI instance")

        try:
            init_res = self.lib.TessBaseAPIInit3(
                api,
                str(tessdata_path).encode("utf-8"),
                target_lang.encode("utf-8"),
            )
            if init_res != 0:
                raise RuntimeError(
                    f"TessBaseAPIInit3 failed with code {init_res} for language '{target_lang}' and path '{tessdata_path}'"
                )

            self.lib.TessBaseAPISetPageSegMode(api, psm)

            gray_img = image.convert("L")
            img_bytes = gray_img.tobytes("raw", "L")
            width, height = gray_img.size

            self.lib.TessBaseAPISetImage(
                api,
                img_bytes,
                width,
                height,
                1,
                width,
            )

            self.lib.TessBaseAPIRecognize(api, None)
            it = self.lib.TessBaseAPIGetIterator(api)

            RIL_BLOCK = 0
            RIL_TEXTLINE = 2
            RIL_WORD = 3

            words = []
            lines = []
            current_line_idx = -1
            current_block_idx = -1

            if it:
                try:
                    while True:
                        if self.lib.TessPageIteratorIsAtBeginningOf(it, RIL_BLOCK):
                            current_block_idx += 1

                        if self.lib.TessPageIteratorIsAtBeginningOf(it, RIL_TEXTLINE):
                            current_line_idx += 1
                            line_ptr = self.lib.TessResultIteratorGetUTF8Text(it, RIL_TEXTLINE)
                            if line_ptr:
                                try:
                                    raw_l = ctypes.cast(line_ptr, ctypes.c_char_p).value
                                    l_text = raw_l.decode("utf-8", errors="replace").strip() if raw_l else ""
                                finally:
                                    self.lib.TessDeleteText(line_ptr)

                                ll, lt, lr, lb = ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
                                self.lib.TessPageIteratorBoundingBox(
                                    it, RIL_TEXTLINE,
                                    ctypes.byref(ll), ctypes.byref(lt), ctypes.byref(lr), ctypes.byref(lb)
                                )
                                if l_text:
                                    lines.append({
                                        "line_idx": current_line_idx,
                                        "text": l_text,
                                        "box": (ll.value, lt.value, lr.value - ll.value, lb.value - lt.value),
                                        "block_idx": current_block_idx,
                                    })

                        txt_ptr = self.lib.TessResultIteratorGetUTF8Text(it, RIL_WORD)
                        if txt_ptr:
                            try:
                                raw_w = ctypes.cast(txt_ptr, ctypes.c_char_p).value
                                word = raw_w.decode("utf-8", errors="replace").strip() if raw_w else ""
                            finally:
                                self.lib.TessDeleteText(txt_ptr)

                            if word:
                                wl, wt, wr, wb = ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
                                self.lib.TessPageIteratorBoundingBox(
                                    it, RIL_WORD,
                                    ctypes.byref(wl), ctypes.byref(wt), ctypes.byref(wr), ctypes.byref(wb)
                                )
                                conf = float(self.lib.TessResultIteratorConfidence(it, RIL_WORD))
                                if conf >= min_conf:
                                    words.append({
                                        "text": word,
                                        "box": (wl.value, wt.value, wr.value - wl.value, wb.value - wt.value),
                                        "conf": conf,
                                        "line_idx": current_line_idx,
                                        "block_idx": current_block_idx,
                                    })

                        if not self.lib.TessPageIteratorNext(it, RIL_WORD):
                            break
                finally:
                    self.lib.TessPageIteratorDelete(it)

            full_text = "\n".join(l["text"] for l in lines) if lines else " ".join(w["text"] for w in words)
            return {
                "words": words,
                "lines": lines,
                "full_text": full_text.strip(),
                "image_size": (width, height),
            }
        finally:
            self.lib.TessBaseAPIEnd(api)
            self.lib.TessBaseAPIDelete(api)

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove trailing spaces, null characters, and normalize line breaks."""
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines()]
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines).strip()

