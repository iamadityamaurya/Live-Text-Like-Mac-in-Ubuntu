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
echo "✅ Autostart & Desktop entry created"

# 4. Download / verify Tesseract language model
echo "Checking language models..."
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from live_text_ocr.core.ocr_engine import ensure_language_data
ensure_language_data('eng')
"

# 5. Register GNOME Global Shortcut (Super+Shift+O)
echo "Configuring GNOME global shortcut (<Super><Shift>o)..."
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from live_text_ocr.keybindings import register_gnome_shortcut
ok, msg = register_gnome_shortcut('$TARGET_BIN capture', '<Super><Shift>o')
print('Shortcut result:', msg)
"

echo ""
echo "🎉 Installation complete!"
echo "Press [Super + Shift + O] anywhere to select screen text and copy to clipboard."
