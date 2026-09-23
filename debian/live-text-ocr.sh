#!/usr/bin/env bash
set -e

export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export DISPLAY="${DISPLAY:-:0}"

exec /usr/bin/python3 -m live_text_ocr.cli "$@"
