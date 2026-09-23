#!/usr/bin/env bash
set -e

# Build .deb packages for amd64 and arm64
# Usage: ./build-deb.sh [version]

VERSION="${1:-1.0.0}"
PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${PKG_DIR}/deb-build"

echo "=== Building live-text-ocr ${VERSION} for amd64 and arm64 ==="

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

for arch in amd64 arm64; do
  echo ""
  echo "--- Building ${arch} ---"
  WORK="${BUILD_DIR}/${arch}"
  mkdir -p "${WORK}"
  cp -r "${PKG_DIR}/live_text_ocr" "${PKG_DIR}/setup.py" "${WORK}/"
  cp -r "${PKG_DIR}/debian" "${WORK}/"

  # Update Architecture and any arch-specific paths in control
  sed -i "s/^Architecture:.*/Architecture: ${arch}/" "${WORK}/debian/control"

  # fakeroot + dpkg-buildpackage for the target arch
  (cd "${WORK}" && \
    dpkg-buildpackage -us -uc -b -a"${arch}" -rfakeroot)

done

mkdir -p "${PKG_DIR}/dist"
mv "${BUILD_DIR}"/*.deb "${PKG_DIR}/dist/" || true

echo ""
echo "=== Done ==="
ls -la "${PKG_DIR}/dist/"
