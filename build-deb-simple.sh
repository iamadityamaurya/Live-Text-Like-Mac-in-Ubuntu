#!/usr/bin/env bash
set -e

# Build .deb packages for amd64 and arm64 without debhelper.
# This creates a simple binary package directly.
# Usage: ./build-deb-simple.sh [version]

VERSION="${1:-1.0.0}"
PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${PKG_DIR}/deb-build-simple"
DIST_DIR="${PKG_DIR}/dist"

rm -rf "${BUILD_DIR}" "${DIST_DIR}"
mkdir -p "${BUILD_DIR}" "${DIST_DIR}"

for arch in amd64 arm64; do
  echo ""
  echo "--- Building ${arch} ---"
  PKG="${BUILD_DIR}/${arch}/live-text-ocr_${VERSION}-1_${arch}"
  mkdir -p "${PKG}/usr/lib/python3/dist-packages" \
           "${PKG}/usr/bin" \
           "${PKG}/usr/share/applications" \
           "${PKG}/usr/share/live-text-ocr" \
           "${PKG}/usr/lib/systemd/user" \
           "${PKG}/DEBIAN"

  cp -r "${PKG_DIR}/live_text_ocr" "${PKG}/usr/lib/python3/dist-packages/"
  cp "${PKG_DIR}/debian/live-text-ocr.sh" "${PKG}/usr/bin/live-text-ocr"
  chmod 0755 "${PKG}/usr/bin/live-text-ocr"
  cp "${PKG_DIR}/debian/live-text-ocr.desktop" "${PKG}/usr/share/applications/"
  cp "${PKG_DIR}/debian/live-text-ocr.service" "${PKG}/usr/lib/systemd/user/"
  cp "${PKG_DIR}/debian/gnome-shortcut.ini" "${PKG}/usr/share/live-text-ocr/"
  cp "${PKG_DIR}/debian/postinst-user-setup.sh" "${PKG}/usr/share/live-text-ocr/postinst-user-setup.sh"
  chmod 0755 "${PKG}/usr/share/live-text-ocr/postinst-user-setup.sh"

  cat > "${PKG}/DEBIAN/control" <<EOF
Package: live-text-ocr
Version: ${VERSION}-1
Section: utils
Priority: optional
Architecture: ${arch}
Depends: python3, python3-pil, python3-pyqt6, libtesseract5, libzbar0, grim, slurp, wl-clipboard, libnotify-bin, xclip | xsel, gir1.2-glib-2.0
Maintainer: Aditya <your.email@example.com>
Description: macOS Live Text-style OCR utility for Ubuntu
 Select any rectangular region on your screen and instantly
 extract and copy the text to your clipboard.
EOF

  cp "${PKG_DIR}/debian/postinst" "${PKG}/DEBIAN/postinst"
  chmod 0755 "${PKG}/DEBIAN/postinst"

  dpkg-deb --build "${PKG}" "${DIST_DIR}/live-text-ocr_${VERSION}-1_${arch}.deb"
done

echo ""
echo "=== Done ==="
ls -la "${DIST_DIR}/"
