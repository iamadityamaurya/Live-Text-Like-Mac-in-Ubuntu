#!/bin/sh
# Run as the installing user to register GNOME shortcuts and enable systemd service.

set -e

BASE="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
EXISTING=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings 2>/dev/null || true)
PATHS="${EXISTING}"

case "${EXISTING}" in
  *"${BASE}/custom-live-text-ocr/"*)
    ;;
  *"@as []"*|*"[]"*)
    PATHS="['${BASE}/custom-live-text-ocr/']"
    ;;
  *)
    PATHS=$(python3 -c "import ast,sys; v=ast.literal_eval(sys.argv[1].lstrip('@as ')); v=[p for p in v if 'custom-live-text-ocr' not in p]; v.append('${BASE}/custom-live-text-ocr/'); print(str(v))" "${EXISTING}")
    ;;
esac

OVERLAY="${BASE}/custom-live-text-ocr-overlay/"
if ! echo "${PATHS}" | grep -q "${OVERLAY}"; then
  PATHS=$(python3 -c "import ast,sys; v=ast.literal_eval(sys.argv[1].lstrip('@as ')); v.append('${OVERLAY}'); print(str(v))" "${EXISTING}")
fi

gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "${PATHS}" || true

gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${BASE}/custom-live-text-ocr/ name 'Live Text OCR' || true
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${BASE}/custom-live-text-ocr/ command '/usr/bin/live-text-ocr capture' || true
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${BASE}/custom-live-text-ocr/ binding '<Ctrl><Shift>c' || true

gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${OVERLAY} name 'Live Text OCR Overlay' || true
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${OVERLAY} command '/usr/bin/live-text-ocr live' || true
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${OVERLAY} binding '<Ctrl><Shift>l' || true

systemctl --user daemon-reload || true
systemctl --user enable live-text-ocr.service || true
systemctl --user restart live-text-ocr.service || true
