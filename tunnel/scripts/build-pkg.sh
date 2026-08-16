#!/bin/bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")/../.." && pwd)
VERSION=$(cat "$ROOT/tunnel/VERSION")
BUILD="$ROOT/build/tunnel"
WORK="$BUILD/pkgwork"
VENDOR="$BUILD/vendor/tor"
PAYLOAD="$WORK/pkgroot"
SCRIPTS="$WORK/pkgscripts"
OUT="$BUILD/DevFixTunnel-${VERSION}-macos-x86_64.pkg"

rm -rf "$WORK"
mkdir -p "$BUILD" "$WORK"
if [ ! -x "$VENDOR/tor" ] || [ ! -x "$VENDOR/pluggable_transports/lyrebird" ] || [ ! -f "$VENDOR/geoip" ] || [ ! -f "$VENDOR/geoip6" ]; then
  /bin/bash "$ROOT/tunnel/scripts/fetch-tor-bundle.sh" "$VENDOR"
fi

mkdir -p "$PAYLOAD/usr/local/bin" "$PAYLOAD/usr/local/libexec/devfix-tunnel" "$PAYLOAD/usr/local/share/devfix-tunnel" "$PAYLOAD/Library/LaunchDaemons" "$SCRIPTS"
install -m 755 "$ROOT/tunnel/cli/devfix-tunnel" "$PAYLOAD/usr/local/bin/devfix-tunnel"
install -m 755 "$ROOT/tunnel/scripts/devfix-tunnel-chrome.sh" "$PAYLOAD/usr/local/bin/devfix-tunnel-chrome"
install -m 755 "$ROOT/tunnel/libexec/devfix-tunnel-guardian" "$PAYLOAD/usr/local/libexec/devfix-tunnel/devfix-tunnel-guardian"
cp -R "$VENDOR" "$PAYLOAD/usr/local/libexec/devfix-tunnel/tor"
chmod -R a+rX "$PAYLOAD/usr/local/libexec/devfix-tunnel/tor"
python3 "$ROOT/tunnel/scripts/generate-runtime-catalog.py" \
  "$VENDOR/pluggable_transports/pt_config.json" \
  "$PAYLOAD/usr/local/share/devfix-tunnel/transports.tsv"
install -m 644 "$ROOT/tunnel/launchd/com.devfix.tunnel.recovery.plist" "$PAYLOAD/Library/LaunchDaemons/com.devfix.tunnel.recovery.plist"
install -m 644 "$ROOT/tunnel/README.md" "$PAYLOAD/usr/local/share/devfix-tunnel/README.md"
install -m 644 "$ROOT/docs/tunnel/SECURITY_MODEL.md" "$PAYLOAD/usr/local/share/devfix-tunnel/SECURITY_MODEL.md"
install -m 755 "$ROOT/tunnel/uninstall.sh" "$PAYLOAD/usr/local/share/devfix-tunnel/uninstall.sh"
install -m 755 "$ROOT/tunnel/pkg/preinstall" "$SCRIPTS/preinstall"
install -m 755 "$ROOT/tunnel/pkg/postinstall" "$SCRIPTS/postinstall"
pkgbuild --root "$PAYLOAD" --scripts "$SCRIPTS" --identifier "com.devfix.tunnel" --version "$VERSION" --install-location "/" "$OUT"
echo "$OUT"
