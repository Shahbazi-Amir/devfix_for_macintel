#!/bin/bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")/../.." && pwd)
TOR_DIR=${1:-"$ROOT/build/tunnel/vendor/tor"}

[ -x "$TOR_DIR/tor" ] || { echo "Tor binary missing: $TOR_DIR/tor" >&2; exit 1; }

version_line=$("$TOR_DIR/tor" --version 2>/dev/null | head -n 1)
CORE_VERSION=$(printf '%s\n' "$version_line" | sed -nE 's/^Tor version ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+).*$/\1/p')
[ -n "$CORE_VERSION" ] || { echo "Could not determine Tor core version from: $version_line" >&2; exit 1; }

BASE="https://dist.torproject.org"
ARCHIVE="tor-${CORE_VERSION}.tar.gz"
CHECKSUM="${ARCHIVE}.sha256sum"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/devfix-tunnel-geoip.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT TERM

CURL=/usr/bin/curl
[ -x "$CURL" ] || CURL=$(command -v curl)
[ -n "$CURL" ] || { echo "curl is required" >&2; exit 1; }

fetch() {
  "$CURL" --fail --location --silent --show-error --retry 3 --retry-all-errors \
    --proto '=https' --tlsv1.2 "$1" -o "$2"
}

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

echo "Fetching Tor ${CORE_VERSION} source GeoIP data..."
fetch "$BASE/$ARCHIVE" "$TMP/$ARCHIVE"
fetch "$BASE/$CHECKSUM" "$TMP/$CHECKSUM"

expected=$(awk -v name="$ARCHIVE" '$2 == name || $2 == "*" name {print $1; exit}' "$TMP/$CHECKSUM")
if [ -z "$expected" ]; then
  expected=$(awk 'NF >= 1 {print $1; exit}' "$TMP/$CHECKSUM")
fi
[ -n "$expected" ] || { echo "Could not parse Tor source checksum" >&2; exit 1; }
actual=$(sha256_file "$TMP/$ARCHIVE")
[ "$actual" = "$expected" ] || { echo "Tor source checksum mismatch" >&2; exit 1; }

tar -xzf "$TMP/$ARCHIVE" -C "$TMP"
SOURCE="$TMP/tor-$CORE_VERSION/src/config"
[ -f "$SOURCE/geoip" ] || { echo "geoip missing from Tor source" >&2; exit 1; }
[ -f "$SOURCE/geoip6" ] || { echo "geoip6 missing from Tor source" >&2; exit 1; }

install -m 644 "$SOURCE/geoip" "$TOR_DIR/geoip"
install -m 644 "$SOURCE/geoip6" "$TOR_DIR/geoip6"
cat > "$TOR_DIR/DEVFIX_TUNNEL_GEOIP_SOURCE.txt" <<EOF
Source: Tor Project official dist
Tor core version: $CORE_VERSION
Artifact: $ARCHIVE
URL: $BASE/$ARCHIVE
SHA256: $actual
Checksum: $BASE/$CHECKSUM
EOF

echo "Verified Tor GeoIP source: $actual"
