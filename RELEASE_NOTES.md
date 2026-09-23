# Live Text OCR v1.0.0

First packaged release of **Live Text OCR for Ubuntu** — a native, lightweight macOS Live Text–style OCR utility for Linux.

## What's included

- **`.deb` packages** for both `amd64` and `arm64`
- **Interactive Live Text overlay** — full-screen word selection with hover, click, and drag marquee
- **Top-panel tray indicator** with clipboard history, pin, and delete controls
- **Global shortcuts** `Super + Shift + C` for capture, `Super + Shift + O` for overlay
- **QR & barcode scanning** via `live-text-ocr qr`
- **Local OCR** using `libtesseract5` via in-process `ctypes`
- **Wayland and X11 support** with automatic capture backend selection
- **Offline operation** — no cloud, no uploads

## Install

Download the `.deb` for your architecture and install with apt. All dependencies are pulled in automatically.

```bash
# amd64
sudo apt install ./live-text-ocr_1.0.0-1_amd64.deb

# arm64
sudo apt install ./live-text-ocr_1.0.0-1_arm64.deb
```

After install, the GNOME shortcuts `Super + Shift + C` (capture) and `Super + Shift + O` (overlay) are registered, autostart is enabled, and the systemd user service is ready.

## Quick start

```bash
live-text-ocr tray      # start the top-panel indicator
live-text-ocr live      # launch the interactive overlay
live-text-ocr capture   # select a region and copy text
live-text-ocr qr        # scan a QR code or barcode
live-text-ocr history   # view recent clips
```

## System requirements

- Ubuntu 22.04+ (or compatible Debian-based distribution)
- GNOME / Wayland or X11 session
- Dependencies handled by apt: `python3-pil`, `python3-pyqt6`, `libtesseract5`, `libzbar0`, `grim`, `slurp`, `wl-clipboard`, `libnotify-bin`, `xclip` or `xsel`

## Assets

| File | Architecture | Size |
|------|--------------|------|
| `live-text-ocr_1.0.0-1_amd64.deb` | x86_64 | ~75 KB package, dependencies installed via apt |
| `live-text-ocr_1.0.0-1_arm64.deb` | ARM64 | ~75 KB package, dependencies installed via apt |

## Notes

- The `.deb` package does not bundle the English OCR model; it is downloaded on first run or during package installation.
- This is the first packaged release. Feedback and bug reports are welcome on GitHub Issues.
