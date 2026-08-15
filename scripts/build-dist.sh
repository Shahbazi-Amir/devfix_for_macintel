#!/bin/bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=$(cat "$ROOT/VERSION")
DIST="$ROOT/dist"
BUILD="$ROOT/build"
VENDOR="$BUILD/vendor/tor"
PORTABLE="$BUILD/portable/DevFix-${VERSION}"

rm -rf "$DIST" "$BUILD/portable"
mkdir -p "$DIST" "$PORTABLE/bin" "$PORTABLE/libexec/devfix" "$PORTABLE/share/man/man1" "$PORTABLE/share/devfix"

"$ROOT/scripts/fetch-tor-bundle.sh" "$VENDOR"
cp "$ROOT/bin/devfix" "$PORTABLE/bin/devfix"
cp -R "$VENDOR" "$PORTABLE/libexec/devfix/tor"
cp "$ROOT/man/devfix.1" "$PORTABLE/share/man/man1/devfix.1"
cp "$ROOT/README.md" "$ROOT/SECURITY.md" "$ROOT/THIRD_PARTY_NOTICES.md" "$ROOT/LICENSE" "$PORTABLE/share/devfix/"
cp "$ROOT/install.sh" "$ROOT/uninstall.sh" "$PORTABLE/"
cp "$ROOT/uninstall.sh" "$PORTABLE/share/devfix/uninstall.sh"
chmod +x "$PORTABLE/bin/devfix" "$PORTABLE/install.sh" "$PORTABLE/uninstall.sh"

tar -czf "$DIST/DevFix-${VERSION}-macos-x86_64.tar.gz" -C "$BUILD/portable" "DevFix-${VERSION}"
echo "Built $DIST/DevFix-${VERSION}-macos-x86_64.tar.gz"
