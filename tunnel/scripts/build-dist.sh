#!/bin/bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")/../.." && pwd)
VERSION=$(cat "$ROOT/tunnel/VERSION")
BUILD="$ROOT/build/tunnel"
WORK="$BUILD/distwork"
VENDOR="$BUILD/vendor/tor"
STAGE="$WORK/DevFixTunnel-${VERSION}-portable"
OUT="$BUILD/DevFixTunnel-${VERSION}-macos-x86_64.tar.gz"

rm -rf "$WORK"
mkdir -p "$BUILD" "$WORK"
if [ ! -x "$VENDOR/tor" ] || [ ! -x "$VENDOR/pluggable_transports/lyrebird" ] || [ ! -f "$VENDOR/geoip" ] || [ ! -f "$VENDOR/geoip6" ]; then
  /bin/bash "$ROOT/tunnel/scripts/fetch-tor-bundle.sh" "$VENDOR"
fi

mkdir -p "$STAGE/bin" "$STAGE/libexec/tor" "$STAGE/share" "$STAGE/launchd"
install -m 755 "$ROOT/tunnel/cli/devfix-tunnel" "$STAGE/bin/devfix-tunnel"
install -m 755 "$ROOT/tunnel/scripts/devfix-tunnel-chrome.sh" "$STAGE/bin/devfix-tunnel-chrome"
install -m 755 "$ROOT/tunnel/libexec/devfix-tunnel-guardian" "$STAGE/libexec/devfix-tunnel-guardian"
cp -R "$VENDOR/." "$STAGE/libexec/tor/"
python3 "$ROOT/tunnel/scripts/generate-runtime-catalog.py" \
  "$VENDOR/pluggable_transports/pt_config.json" \
  "$STAGE/share/transports.tsv"
install -m 644 "$ROOT/tunnel/launchd/com.devfix.tunnel.recovery.plist" "$STAGE/launchd/com.devfix.tunnel.recovery.plist"
install -m 644 "$ROOT/tunnel/README.md" "$STAGE/README.md"
install -m 755 "$ROOT/tunnel/portable-install.sh" "$STAGE/install.sh"
tar -C "$WORK" -czf "$OUT" "$(basename "$STAGE")"
echo "$OUT"
