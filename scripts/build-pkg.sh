#!/bin/bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=$(cat "$ROOT/VERSION")
DIST="$ROOT/dist"
BUILD="$ROOT/build"
PKGROOT="$BUILD/pkgroot"
PKGSCRIPTS="$BUILD/pkg-scripts"
VENDOR="$BUILD/vendor/tor"

"$ROOT/scripts/build-dist.sh"
rm -rf "$PKGROOT" "$PKGSCRIPTS"
mkdir -p "$PKGROOT/usr/local/bin" "$PKGROOT/usr/local/libexec/devfix" "$PKGROOT/usr/local/share/man/man1" "$PKGROOT/usr/local/share/devfix" "$PKGSCRIPTS"
cp "$ROOT/bin/devfix" "$PKGROOT/usr/local/bin/devfix"
cp -R "$VENDOR" "$PKGROOT/usr/local/libexec/devfix/tor"
chmod -R a+rX "$PKGROOT/usr/local/libexec/devfix/tor"
cp "$ROOT/man/devfix.1" "$PKGROOT/usr/local/share/man/man1/devfix.1"
cp "$ROOT/README.md" "$ROOT/SECURITY.md" "$ROOT/THIRD_PARTY_NOTICES.md" "$ROOT/LICENSE" "$ROOT/uninstall.sh" "$PKGROOT/usr/local/share/devfix/"
chmod 755 "$PKGROOT/usr/local/bin/devfix" "$PKGROOT/usr/local/share/devfix/uninstall.sh"
chmod 755 "$PKGROOT/usr/local/libexec/devfix/tor/tor" "$PKGROOT/usr/local/libexec/devfix/tor/pluggable_transports/lyrebird"

cat > "$PKGSCRIPTS/postinstall" <<'POSTINSTALL'
#!/bin/bash
set -eu
TOR=/usr/local/libexec/devfix/tor/tor
LYREBIRD=/usr/local/libexec/devfix/tor/pluggable_transports/lyrebird
DEVFIX=/usr/local/bin/devfix
chmod -R a+rX /usr/local/libexec/devfix/tor
chmod 755 "$DEVFIX" "$TOR" "$LYREBIRD"
test -x "$DEVFIX"
test -x "$TOR"
test -x "$LYREBIRD"
exit 0
POSTINSTALL
chmod 755 "$PKGSCRIPTS/postinstall"

command -v pkgbuild >/dev/null 2>&1 || { echo "pkgbuild is required; run on macOS" >&2; exit 1; }
pkgbuild --root "$PKGROOT" --scripts "$PKGSCRIPTS" --identifier io.github.shahbazi-amir.devfix \
  --version "$VERSION" --install-location / --ownership recommended \
  "$DIST/DevFix-${VERSION}-macos-x86_64.pkg"

if command -v shasum >/dev/null 2>&1; then
  (cd "$DIST" && shasum -a 256 "DevFix-${VERSION}-macos-x86_64.pkg" "DevFix-${VERSION}-macos-x86_64.tar.gz" > SHA256SUMS)
else
  (cd "$DIST" && sha256sum "DevFix-${VERSION}-macos-x86_64.pkg" "DevFix-${VERSION}-macos-x86_64.tar.gz" > SHA256SUMS)
fi

echo "Built package and checksums in $DIST"
