# Live Text OCR for Ubuntu

A lightweight, native macOS Live Text–style OCR utility for Ubuntu (Wayland and X11). Select any region on your screen—including paused videos in Brave/Chrome, PDFs, slides, or images—and instantly copy the recognized text to your clipboard.

![Live Text OCR](https://img.shields.io/badge/Platform-Ubuntu%20%7C%20Linux-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)
![Wayland & X11](https://img.shields.io/badge/Display-Wayland%20%26%20X11-green?style=flat-square)

---

## ⚡ Features

* **macOS Live Text Experience**: Select a screen region $\rightarrow$ Instant OCR $\rightarrow$ Automatically copied to clipboard (`Ctrl+V` ready).
* **Native Ubuntu Top-Panel Indicator**: Sits directly in your top bar with a clean direct history menu.
* **Global Keyboard Shortcut**: Press `Super + Shift + O` anywhere.
* **Video Frame Preprocessing**: Auto-enhances contrast and handles dark-mode slides/videos with auto-inversion for near-100% OCR accuracy.
* **Zero Disk Writes**: In-memory pixel streaming directly into the local Tesseract OCR engine.
* **No Root Required**: Connects to native `libtesseract` without needing `sudo` access to run or download languages.
* **Clipboard History**: Lists recent OCR clips directly in the top-panel menu for quick re-copying.

---

## 🚀 Quick Install

Run the one-line installer from the repository root:

```bash
./install.sh
```

This will:
1. Create the executable launcher at `~/.local/bin/live-text-ocr`.
2. Add desktop launcher and autostart entries.
3. Download the default English OCR model (`eng.traineddata`).
4. Register the global keyboard shortcut (`Super + Shift + O`) in GNOME Settings.

---

## 🖥️ System Dependencies

Ensure the following standard system packages are installed on Ubuntu:

```bash
sudo apt update
sudo apt install -y libtesseract5 python3-pil python3-pyqt6
```

---

## 📖 Usage

### 1. Top Panel Indicator (Recommended)
* **Left-Click** the **`[T]`** icon in your top bar to trigger screen capture.
* **Right-Click** the **`[T]`** icon to view recent history clips or exit.

### 2. Global Shortcut
* Press **`Super + Shift + O`** anywhere on your screen.
* Drag a box over the desired text and release.

### 3. CLI Commands

```bash
# Start top-panel tray indicator
live-text-ocr tray

# Trigger a single screen selection and OCR
live-text-ocr capture

# View recent history clips
live-text-ocr history

# Clear OCR history
live-text-ocr history --clear

# Download additional Tesseract languages (e.g. German, French, Spanish, Japanese)
live-text-ocr download-lang deu
live-text-ocr download-lang fra
live-text-ocr download-lang spa
live-text-ocr download-lang jpn

# System diagnostics
live-text-ocr info
```

---

## ⚙️ Configuration

Configuration is stored at `~/.config/live-text-ocr/config.json`:

```json
{
  "shortcut": "<Super><Shift>o",
  "ocr_language": "eng",
  "psm_mode": 6,
  "preprocess": {
    "enabled": true,
    "upscale_factor": 2.0,
    "auto_invert": true,
    "enhance_contrast": true,
    "binarize": false
  },
  "notifications": {
    "enabled": true,
    "preview_max_chars": 45,
    "expire_time_ms": 3000
  },
  "history": {
    "enabled": true,
    "max_entries": 50
  }
}
```

---

## 📄 License

MIT License. Free for personal and commercial use.
