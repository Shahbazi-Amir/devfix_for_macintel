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
if [ ! -x "$VENDOR/tor" ] || [ ! -x "$VENDOR/pluggable_transports/lyrebird" ]; then "$ROOT/tunnel/scripts/fetch-tor-bundle.sh" "$VENDOR"; fi
mkdir -p "$STAGE/bin" "$STAGE/libexec/tor" "$STAGE/share" "$STAGE/launchd"
install -m 755 "$ROOT/tunnel/cli/devfix-tunnel" "$STAGE/bin/devfix-tunnel"
install -m 755 "$ROOT/tunnel/libexec/devfix-tunnel-guardian" "$STAGE/libexec/devfix-tunnel-guardian"
cp -R "$VENDOR/." "$STAGE/libexec/tor/"
install -m 644 "$ROOT/tunnel/launchd/com.devfix.tunnel.recovery.plist" "$STAGE/launchd/com.devfix.tunnel.recovery.plist"
install -m 644 "$ROOT/tunnel/README.md" "$STAGE/README.md"
install -m 755 "$ROOT/tunnel/portable-install.sh" "$STAGE/install.sh"
tar -C "$WORK" -czf "$OUT" "$(basename "$STAGE")"
echo "$OUT"
