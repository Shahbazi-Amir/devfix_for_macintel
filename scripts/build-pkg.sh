#!/bin/bash
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
VERSION=$(cat "$ROOT/VERSION")
OUT="${1:-$ROOT/dist}"
PKGROOT="$ROOT/build/pkgroot"
PKG="$OUT/DevFix-$VERSION.pkg"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "Error: .pkg creation requires macOS (pkgbuild)." >&2
  exit 1
fi
command -v pkgbuild >/dev/null 2>&1 || { echo "Error: pkgbuild not found." >&2; exit 1; }

rm -rf "$PKGROOT"
mkdir -p "$PKGROOT/usr/local/bin" "$PKGROOT/usr/local/share/man/man1" "$OUT"
install -m 0755 "$ROOT/bin/devfix" "$PKGROOT/usr/local/bin/devfix"
install -m 0644 "$ROOT/man/devfix.1" "$PKGROOT/usr/local/share/man/man1/devfix.1"

pkgbuild \
  --root "$PKGROOT" \
  --identifier "io.github.shahbazi-amir.devfix" \
  --version "$VERSION" \
  --install-location / \
  "$PKG"

"$ROOT/scripts/build-dist.sh" "$OUT"

if command -v shasum >/dev/null 2>&1; then
  (
    cd "$OUT"
    shasum -a 256 "DevFix-$VERSION.pkg" "DevFix-$VERSION.tar.gz" > SHA256SUMS
  )
fi

echo "Built $PKG"
echo "Note: this package is unsigned unless you sign it separately with an Apple Developer ID Installer certificate."
