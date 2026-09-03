"""Main CLI command dispatcher for Live Text OCR."""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw

from live_text_ocr.config import load_config, save_config, get_tessdata_dir
from live_text_ocr.core.capture import capture_selected_region, CaptureCancelled
from live_text_ocr.core.clipboard import copy_to_clipboard
from live_text_ocr.core.history import get_history, clear_history, log_history_entry
from live_text_ocr.core.notify import notify_success, notify_error
from live_text_ocr.core.ocr_engine import TesseractEngine, ensure_language_data
from live_text_ocr.core.preprocess import preprocess_image
from live_text_ocr.core.session import inspect_environment
from live_text_ocr.keybindings import register_gnome_shortcut


def cmd_capture(args: argparse.Namespace) -> int:
    """Perform one interactive screen capture and OCR."""
    config = load_config()
    lang = args.lang or config.get("ocr_language", "eng")
    psm = args.psm or config.get("psm_mode", 6)

    try:
        # 1. Capture interactive region
        image = capture_selected_region()
        if not image:
            return 0

        # 2. Preprocess image
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

        # 3. Perform OCR
        engine = TesseractEngine(default_lang=lang)
        text = engine.extract_text(processed_img, lang=lang, psm=psm)

        if not text:
            # Fallback retry without binarization/inversion or with auto PSM if no text found
            text = engine.extract_text(image, lang=lang, psm=3)

        if not text:
            if config.get("notifications", {}).get("enabled", True):
                notify_error("No text detected in selected region.")
            return 0

        # 4. Copy to Clipboard
        copied = copy_to_clipboard(text)
        if not copied:
            notify_error("Failed to copy extracted text to clipboard.")
            return 1

        # 5. Log History
        log_history_entry(text)

        # 6. Show Notification
        if config.get("notifications", {}).get("enabled", True):
            notify_cfg = config.get("notifications", {})
            notify_success(
                text,
                max_chars=notify_cfg.get("preview_max_chars", 45),
                expire_time_ms=notify_cfg.get("expire_time_ms", 3000),
            )

        print(f"Extracted ({len(text)} chars):\n{text}")
        return 0

    except CaptureCancelled:
        # Silent exit on normal user escape/cancel
        return 0
    except Exception as e:
        notify_error(f"OCR Error: {str(e)}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_test(args: argparse.Namespace) -> int:
    """Run an OCR test on a generated synthetic image or a given image file."""
    config = load_config()
    lang = args.lang or config.get("ocr_language", "eng")

    if args.file:
        img_path = Path(args.file)
        if not img_path.exists():
            print(f"File not found: {img_path}", file=sys.stderr)
            return 1
        img = Image.open(img_path)
        print(f"Loaded image: {img_path} ({img.size[0]}x{img.size[1]})")
    else:
        # Generate synthetic test image mimicking a video slide
        test_text = "ROS 2 Navigation Stack"
        img = Image.new("RGB", (450, 120), color=(30, 30, 35))
        draw = ImageDraw.Draw(img)
        draw.text((25, 45), test_text, fill=(240, 240, 240))
        print(f"Created synthetic test slide image with text: '{test_text}'")

    processed = preprocess_image(img, upscale_factor=2.0, auto_invert=True, enhance_contrast=True)
    engine = TesseractEngine(default_lang=lang)
    extracted = engine.extract_text(processed, lang=lang, psm=6)

    print(f"\n--- OCR Result ---")
    print(f"Recognized: {repr(extracted)}")
    if not args.file and extracted == "ROS 2 Navigation Stack":
        print("✅ SUCCESS: Exact text match!")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    """Display or manage recent clipboard OCR history."""
    if args.clear:
        clear_history()
        print("OCR history cleared.")
        return 0

    history = get_history()
    if not history:
        print("No OCR history recorded yet.")
        return 0

    limit = args.limit or len(history)
    print(f"--- Recent OCR Clips (showing {min(limit, len(history))}) ---")
    for i, item in enumerate(history[:limit], 1):
        preview = item["text"].replace("\n", " ")
        if len(preview) > 60:
            preview = preview[:57] + "..."
        print(f"[{i}] {item['time_str']} ({item['char_count']} chars): {preview}")
    return 0


def cmd_download_lang(args: argparse.Namespace) -> int:
    """Download a new Tesseract language model."""
    lang = args.language.strip().lower()
    try:
        tessdata_dir = ensure_language_data(lang)
        print(f"Language '{lang}' is ready at: {tessdata_dir}")
        return 0
    except Exception as e:
        print(f"Error downloading language '{lang}': {e}", file=sys.stderr)
        return 1


def cmd_setup_shortcut(args: argparse.Namespace) -> int:
    """Register the GNOME global shortcut."""
    binding = args.binding or "<Super><Shift>o"
    exec_path = args.command or "live-text-ocr capture"
    
    # Check if live-text-ocr is in ~/.local/bin/
    local_bin = Path.home() / ".local/bin/live-text-ocr"
    if local_bin.exists():
        exec_path = str(local_bin) + " capture"

    success, msg = register_gnome_shortcut(exec_path, binding=binding)
    if success:
        print(f"✅ {msg}")
        return 0
    else:
        print(f"❌ {msg}", file=sys.stderr)
        return 1


def cmd_tray(args: argparse.Namespace) -> int:
    """Launch the top-panel system tray indicator."""
    from live_text_ocr.ui.tray import start_tray
    start_tray()
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Display environment, session, and tool diagnostic info."""
    env = inspect_environment()
    print("=== Live Text OCR System Diagnostics ===")
    print(f"Session Type:      {env['session_type']}")
    print(f"Desktop:           {env['desktop']}")
    print(f"Tessdata Dir:      {get_tessdata_dir()}")
    print("\nTools Available:")
    for tool, path in env["tools"].items():
        status = f"✅ {path}" if path else "❌ Not found"
        print(f"  - {tool:12}: {status}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="live-text-ocr",
        description="macOS Live Text–style OCR utility for Ubuntu",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    # tray subcommand (top panel icon)
    p_tray = subparsers.add_parser("tray", aliases=["panel", "indicator"], help="Launch Ubuntu top-panel tray indicator")
    p_tray.set_defaults(func=cmd_tray)

    # capture subcommand
    p_cap = subparsers.add_parser("capture", help="Trigger region selection and OCR to clipboard")
    p_cap.add_argument("--lang", "-l", help="OCR language code (default from config or 'eng')")
    p_cap.add_argument("--psm", type=int, help="Page segmentation mode (default 6)")
    p_cap.set_defaults(func=cmd_capture)

    # test subcommand
    p_test = subparsers.add_parser("test", help="Test OCR extraction on synthetic or existing image")
    p_test.add_argument("--file", "-f", help="Image file path to test")
    p_test.add_argument("--lang", "-l", default="eng", help="OCR language")
    p_test.set_defaults(func=cmd_test)

    # history subcommand
    p_hist = subparsers.add_parser("history", help="View or clear OCR history")
    p_hist.add_argument("--limit", "-n", type=int, default=10, help="Number of items to show")
    p_hist.add_argument("--clear", action="store_true", help="Clear all history")
    p_hist.set_defaults(func=cmd_history)

    # download-lang subcommand
    p_lang = subparsers.add_parser("download-lang", help="Download a Tesseract language model")
    p_lang.add_argument("language", help="Language code (e.g. deu, fra, spa, jpn, chi_sim)")
    p_lang.set_defaults(func=cmd_download_lang)

    # setup-shortcut subcommand
    p_sc = subparsers.add_parser("setup-shortcut", help="Register GNOME global shortcut")
    p_sc.add_argument("--binding", default="<Super><Shift>o", help="Keybinding (default: <Super><Shift>o)")
    p_sc.add_argument("--command", help="Command to run on shortcut")
    p_sc.set_defaults(func=cmd_setup_shortcut)

    # info subcommand
    p_info = subparsers.add_parser("info", help="Show system environment and tool info")
    p_info.set_defaults(func=cmd_info)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        # Default to capture if no subcommand provided
        return cmd_capture(argparse.Namespace(lang=None, psm=None))

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
