#!/usr/bin/env bash
set -e

# Ensure session environment is available when launched from systemd / shortcuts
if [ -z "${WAYLAND_DISPLAY}" ] && [ -z "${DISPLAY}" ]; then
    # Try to pull environment from the active graphical session
    if command -v loginctl >/dev/null 2>&1; then
        ACTIVE_SESSION=$(loginctl show-seat seat0 -p ActiveSession --value 2>/dev/null || true)
        if [ -n "${ACTIVE_SESSION}" ]; then
            eval "$(loginctl show-environment "${ACTIVE_SESSION}" 2>/dev/null | grep -E '^(WAYLAND_DISPLAY|DISPLAY|XDG_SESSION_TYPE|XDG_CURRENT_DESKTOP|DBUS_SESSION_BUS_ADDRESS)=' | sed 's/^/export /')" || true
        fi
    fi
fi

export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export DISPLAY="${DISPLAY:-:0}"

exec /usr/bin/python3 -m live_text_ocr.cli "$@"
