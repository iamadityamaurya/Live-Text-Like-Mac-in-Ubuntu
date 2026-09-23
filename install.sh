#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
TARGET_BIN="$BIN_DIR/live-text-ocr"

echo "=== Installing Live Text OCR for Ubuntu ==="

# 1. Ensure bin directory exists
mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"

# 2. Create launcher wrapper in ~/.local/bin
cat <<EOF > "$TARGET_BIN"
#!/usr/bin/env bash
export WAYLAND_DISPLAY="\${WAYLAND_DISPLAY:-wayland-0}"
export DISPLAY="\${DISPLAY:-:0}"
export PATH="\$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:\$PATH"
export PYTHONPATH="$SCRIPT_DIR:\$PYTHONPATH"
exec /usr/bin/python3 -m live_text_ocr.cli "\$@"
EOF

chmod +x "$TARGET_BIN"
echo "✅ Launcher installed at $TARGET_BIN"

# 3. Create Desktop Entries & Autostart
cat <<EOF > "$APP_DIR/live-text-ocr.desktop"
[Desktop Entry]
Name=Live Text OCR (Top Panel Indicator)
Comment=macOS Live Text–style screen OCR utility in Ubuntu top panel
Exec=$TARGET_BIN tray
Icon=edit-copy
Terminal=false
Type=Application
Categories=Utility;
Keywords=OCR;Screenshot;LiveText;Clipboard;Tray;Panel;
EOF
chmod +x "$APP_DIR/live-text-ocr.desktop"

# Create autostart entry so it is always present in the top bar on login
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cp "$APP_DIR/live-text-ocr.desktop" "$AUTOSTART_DIR/live-text-ocr.desktop"

# Create and enable systemd user service for background persistence
SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"
cat <<EOF > "$SYSTEMD_DIR/live-text-ocr.service"
[Unit]
Description=Live Text OCR Tray Indicator
After=graphical-session.target

[Service]
Type=simple
ExecStart=$TARGET_BIN tray
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload || true
systemctl --user enable live-text-ocr.service || true
systemctl --user restart live-text-ocr.service || true
echo "✅ Autostart & systemd background service configured"

# 4. Download / verify Tesseract language model
echo "Checking language models..."
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from live_text_ocr.core.ocr_engine import ensure_language_data
ensure_language_data('eng')
"

# 5. Register GNOME Global Shortcuts (Super+Shift+C capture, Super+Shift+O overlay)
echo "Configuring GNOME global shortcuts (<Super><Shift>c capture, <Super><Shift>o overlay)..."
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from live_text_ocr.keybindings import register_gnome_shortcut_by_name
ok1 = register_gnome_shortcut_by_name('Live Text OCR', '$TARGET_BIN capture', '<Super><Shift>c')
ok2 = register_gnome_shortcut_by_name('Live Text OCR Overlay', '$TARGET_BIN live', '<Super><Shift>o')
print('Capture shortcut:', 'ok' if ok1 else 'failed')
if not ok1:
    import sys
    sys.exit(1)
print('Overlay shortcut:', 'ok' if ok2 else 'failed')
if not ok2:
    import sys
    sys.exit(1)
"

echo ""
echo "🎉 Installation complete!"
echo "Press [Super + Shift + C] to capture a region or [Super + Shift + O] to open the overlay."
