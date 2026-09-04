# Live Text OCR for Ubuntu

A native, lightweight macOS Live Text–style OCR utility designed for Ubuntu (Wayland and X11). Select any rectangular region anywhere on your screen—including paused videos in browsers (Brave, Chrome, Firefox), PDFs, slides, images, or terminals—and instantly extract and copy the text to your clipboard.

![Platform](https://img.shields.io/badge/Platform-Ubuntu%20%7C%20Linux-orange?style=flat-square)
![Display](https://img.shields.io/badge/Display-Wayland%20%26%20X11-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

---

## ✨ Features

* **macOS Live Text Experience**: `Select Screen Region → Local OCR → Copied to Clipboard` (`Ctrl+V` ready in milliseconds).
* **Native Ubuntu Top-Panel Indicator**: Elegant monochrome `[ T ]` icon in your top bar that seamlessly matches your GNOME panel theme.
* **Direct History Access**: View recent text clips directly in the top-bar dropdown.
* **Pin & Delete Controls**: Pin favorite/frequent clips to the top or delete individual entries.
* **Global Keyboard Shortcut**: Press `Super + Shift + O` anywhere on your desktop.
* **Video Frame Preprocessing**: Auto-enhances contrast and detects dark slides/videos (auto-inverting them for near-100% Tesseract OCR accuracy).
* **Zero Disk Writes**: In-memory pixel capture and streaming directly into the local OCR engine without saving temporary screenshots.
* **No Root Required**: Interacts directly with Ubuntu's native `libtesseract.so.5` C-API without requiring `sudo` to run or download language packs.
* **Auto-Start & Background Persistence**: Runs as a resilient `systemd --user` service that automatically starts on login and auto-recovers if closed.

---

## 📦 System Prerequisites

Before running the installer, ensure standard system dependencies are installed on Ubuntu:

```bash
sudo apt update
sudo apt install -y libtesseract5 python3-pil python3-pyqt6 grim slurp wl-clipboard libnotify-bin
```

---

## 🚀 Installation

Clone the repository and run the one-step installer:

```bash
git clone https://github.com/your-username/copy_paste.git
cd copy_paste
./install.sh
```

### What the Installer Does Automatically:
1. **Installs Launcher**: Creates the executable wrapper at `~/.local/bin/live-text-ocr`.
2. **Downloads OCR Model**: Downloads and caches `eng.traineddata` in `~/.local/share/tessdata/`.
3. **Binds Global Shortcut**: Registers `Super + Shift + O` in GNOME Settings via `gsettings`.
4. **Creates Desktop Entry**: Adds `Live Text OCR` to your Ubuntu Applications menu.
5. **Configures Autostart**: Installs `~/.config/autostart/live-text-ocr.desktop` for graphical login.
6. **Enables systemd Service**: Configures and starts `live-text-ocr.service` via `systemctl --user` so it runs continuously in the background.

---

## 📖 How to Use

### 1. Top Panel Indicator (Recommended)
* **Left-Click** the **`[ T ]`** icon in your top bar:
  * Instantly triggers the screen region selection tool.
  * Drag a box over any text and release.
  * Text is automatically copied to clipboard and a desktop notification appears.
* **Dropdown Menu**:
  * **`⛶ Capture Text Selection`**: Trigger OCR screen capture.
  * **Recent History Clips**: Click any clip to re-copy it.
  * **`📌 Pin / Unpin Clip`**: Pin important clips so they stay at the top.
  * **`🗑️ Delete Clip`**: Delete a specific clip from history.
  * **`🧹 Clear All History`**: Clears unpinned clips.
  * **`✕ Quit Live Text`**: Close the indicator.

### 2. Global Keyboard Shortcut
* Press **`Super + Shift + O`** anywhere on your desktop.
* Drag a box over any text on your screen.
* Press **`Ctrl + V`** anywhere to paste.

---

## 🖥️ Command-Line Interface (CLI)

```bash
# Start the top-panel tray indicator daemon (default)
live-text-ocr tray

# Trigger an immediate interactive screen capture
live-text-ocr capture

# View recent OCR history in terminal
live-text-ocr history

# Clear all OCR history
live-text-ocr history --clear

# Run self-test on a test image
live-text-ocr test

# Download additional Tesseract language packs
live-text-ocr download-lang deu   # German
live-text-ocr download-lang fra   # French
live-text-ocr download-lang spa   # Spanish
live-text-ocr download-lang jpn   # Japanese
live-text-ocr download-lang chi_sim # Simplified Chinese

# Re-register GNOME global shortcut
live-text-ocr setup-shortcut

# Display system diagnostics (session type, display server, tools)
live-text-ocr info
```

---

## ⚙️ Background Service Management

Live Text OCR runs as a background user service managed by systemd:

```bash
# Check service status
systemctl --user status live-text-ocr.service

# Restart the service
systemctl --user restart live-text-ocr.service

# Stop the service
systemctl --user stop live-text-ocr.service

# Disable autostart
systemctl --user disable live-text-ocr.service
```

---

## 🔧 Configuration

Settings are saved in `~/.config/live-text-ocr/config.json`:

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
  },
  "clipboard": {
    "trim_whitespace": true,
    "preserve_linebreaks": true,
    "strip_trailing_newlines": true
  }
}
```

---

## 🏗️ Architecture & Technology Stack

```
live_text_ocr/
├── cli.py               # Main CLI command dispatcher
├── config.py            # Configuration loader & path manager
├── keybindings.py       # GNOME keybinding manager via gsettings
├── ui/
│   └── tray.py          # Top-panel indicator with direct history view
└── core/
    ├── session.py       # Wayland / X11 display session detection
    ├── capture.py       # XDG Desktop Portal & in-memory capture
    ├── preprocess.py    # Grayscale, upscale, contrast boost, & auto-inversion
    ├── ocr_engine.py    # In-process ctypes wrapper for libtesseract.so.5
    ├── clipboard.py     # Wayland (wl-copy) & X11 (xclip) clipboard sync
    ├── notify.py        # Desktop notification dispatcher (notify-send)
    └── history.py       # History storage with pin/delete management
```

---

## 📄 License

Distributed under the MIT License. Free for personal and commercial use.
