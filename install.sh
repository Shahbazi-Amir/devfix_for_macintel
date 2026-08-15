#!/bin/bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
PREFIX=${PREFIX:-/usr/local}
DESTDIR=${DESTDIR:-}
TARGET="$DESTDIR$PREFIX"

if [ -d "$ROOT/libexec/devfix/tor" ]; then
  TOR_SOURCE="$ROOT/libexec/devfix/tor"
elif [ -d "$ROOT/build/vendor/tor" ]; then
  TOR_SOURCE="$ROOT/build/vendor/tor"
else
  echo "Self-contained Tor payload not found." >&2
  echo "Install the release .pkg/.tar.gz, or run scripts/fetch-tor-bundle.sh before installing from source." >&2
  exit 1
fi

NEED_SUDO=0
if [ -z "$DESTDIR" ]; then
  parent=$(dirname "$PREFIX")
  if [ ! -w "$parent" ] && [ ! -w "$PREFIX" ]; then
    command -v sudo >/dev/null 2>&1 || { echo "sudo is required to install to $PREFIX" >&2; exit 1; }
    NEED_SUDO=1
  fi
fi

as_root() {
  if [ "$NEED_SUDO" -eq 1 ]; then
    sudo "$@"
  else
    "$@"
  fi
}

as_root mkdir -p "$TARGET/bin" "$TARGET/libexec/devfix" "$TARGET/share/man/man1" "$TARGET/share/devfix"
as_root cp "$ROOT/bin/devfix" "$TARGET/bin/devfix"
as_root rm -rf "$TARGET/libexec/devfix/tor"
as_root cp -R "$TOR_SOURCE" "$TARGET/libexec/devfix/tor"
as_root cp "$ROOT/share/man/man1/devfix.1" "$TARGET/share/man/man1/devfix.1"
for f in README.md SECURITY.md THIRD_PARTY_NOTICES.md LICENSE uninstall.sh; do
  [ -f "$ROOT/share/devfix/$f" ] && as_root cp "$ROOT/share/devfix/$f" "$TARGET/share/devfix/$f"
done
as_root chmod +x "$TARGET/bin/devfix" "$TARGET/libexec/devfix/tor/tor" "$TARGET/libexec/devfix/tor/pluggable_transports/lyrebird"
[ ! -f "$TARGET/share/devfix/uninstall.sh" ] || as_root chmod +x "$TARGET/share/devfix/uninstall.sh"

echo "DevFix installed to $TARGET"
echo "Run: devfix doctor"
