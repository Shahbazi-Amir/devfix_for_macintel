#!/bin/bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=$(cat "$ROOT/TOR_BUNDLE_VERSION")
DEST=${1:-"$ROOT/build/vendor/tor"}
ARCHIVE="tor-expert-bundle-macos-x86_64-${VERSION}.tar.gz"
BASE="https://archive.torproject.org/tor-package-archive/torbrowser/${VERSION}"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/devfix-tor.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT TERM

CURL=/usr/bin/curl
[ -x "$CURL" ] || CURL=$(command -v curl)
[ -n "$CURL" ] || { echo "curl is required" >&2; exit 1; }

fetch() {
  "$CURL" --fail --location --silent --show-error --retry 3 \
    --proto '=https' --tlsv1.2 "$1" -o "$2"
}

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

echo "Fetching official Tor Expert Bundle ${VERSION} for macOS x86_64..."
fetch "$BASE/$ARCHIVE" "$TMP/$ARCHIVE"
fetch "$BASE/sha256sums-signed-build.txt" "$TMP/SHA256SUMS"

expected=$(awk -v name="$ARCHIVE" '$2 == name {print $1; exit}' "$TMP/SHA256SUMS")
[ -n "$expected" ] || { echo "Could not find $ARCHIVE in Tor checksum manifest" >&2; exit 1; }
actual=$(sha256_file "$TMP/$ARCHIVE")
[ "$actual" = "$expected" ] || { echo "Tor bundle checksum mismatch" >&2; exit 1; }

tar -xzf "$TMP/$ARCHIVE" -C "$TMP"
source_dir="$TMP/tor"
[ -d "$source_dir" ] || source_dir=$(find "$TMP" -type d -name tor | head -n 1)
[ -n "$source_dir" ] && [ -d "$source_dir" ] || { echo "Tor bundle layout not recognized" >&2; exit 1; }
[ -x "$source_dir/tor" ] || { echo "Tor binary missing from expert bundle" >&2; exit 1; }
[ -x "$source_dir/pluggable_transports/lyrebird" ] || { echo "lyrebird missing from expert bundle" >&2; exit 1; }

rm -rf "$DEST"
mkdir -p "$(dirname "$DEST")"
cp -R "$source_dir" "$DEST"
chmod +x "$DEST/tor" "$DEST/pluggable_transports/lyrebird"
cat > "$DEST/DEVFIX_BUNDLE_SOURCE.txt" <<EOF_META
Source: Tor Project official package archive
Version: $VERSION
Artifact: $ARCHIVE
URL: $BASE/$ARCHIVE
SHA256: $actual
Manifest: $BASE/sha256sums-signed-build.txt
EOF_META

echo "Verified Tor bundle: $actual"
