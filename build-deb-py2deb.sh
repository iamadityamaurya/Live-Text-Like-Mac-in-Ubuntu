#!/usr/bin/env bash
set -e

# Build .deb packages for amd64 and arm64 using python-stdeb.
# This avoids needing debhelper/dh-python installed system-wide.
# Usage: ./build-deb-py2deb.sh [version]

VERSION="${1:-1.0.0}"
PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${PKG_DIR}/deb-build"
DIST_DIR="${PKG_DIR}/dist"

rm -rf "${BUILD_DIR}" "${DIST_DIR}"
mkdir -p "${BUILD_DIR}" "${DIST_DIR}"

STPYTHON="/tmp/opencode/deb-build-venv/bin/python3"

cd "${BUILD_DIR}"
"${STPYTHON}" -c "
import setuptools
try:
    import distutils.core
except ImportError:
    pass
try:
    import distutils.core as dc
except ImportError:
    import setuptools as dc
dc.run_setup('${PKG_DIR}/setup.py', script_args=[
    'sdist_dsc',
    '--dist-dir=${BUILD_DIR}/dsc',
    '--package=live-text-ocr',
    '--section=utils',
    '--priority=optional',
    '--maintainer=Aditya <your.email@example.com>',
    '--suite=unstable',
])
" 2>&1 | tail -30

# Locate generated source package
DSC=$(find "${BUILD_DIR}/dsc" -maxdepth 2 -name '*.dsc' | head -1)
if [ -z "${DSC}" ]; then
  echo "Error: .dsc file not generated"
  exit 1
fi

DSC_DIR=$(dirname "${DSC}")
SRC=$(basename "${DSC}" .dsc)

cd "${DSC_DIR}"

for arch in amd64 arm64; do
  echo ""
  echo "--- Building ${arch} ---"
  # Re-extract source for each arch
  rm -rf "live-text-ocr-${VERSION}"
  dpkg-source -x "${SRC}.dsc"

  # Inject debian packaging extras
  cp -r "${PKG_DIR}/debian" "live-text-ocr-${VERSION}/"
  sed -i "s/^Architecture:.*/Architecture: ${arch}/" "live-text-ocr-${VERSION}/debian/control"

  (cd "live-text-ocr-${VERSION}" && dpkg-buildpackage -us -uc -b -a"${arch}" -rfakeroot)
done

mv "${DSC_DIR}"/*.deb "${DIST_DIR}/" || true

echo ""
echo "=== Done ==="
ls -la "${DIST_DIR}/"
