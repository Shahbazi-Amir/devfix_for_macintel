#!/bin/bash
set -eu

PREFIX="${DEVFIX_PREFIX:-/usr/local}"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
BIN_SRC="$SCRIPT_DIR/bin/devfix"
MAN_SRC="$SCRIPT_DIR/man/devfix.1"

if [ ! -f "$BIN_SRC" ]; then
  echo "Error: bin/devfix not found. Run this installer from the DevFix repository." >&2
  exit 1
fi

run_install() {
  install -d "$PREFIX/bin" "$PREFIX/share/man/man1"
  install -m 0755 "$BIN_SRC" "$PREFIX/bin/devfix"
  if [ -f "$MAN_SRC" ]; then
    install -m 0644 "$MAN_SRC" "$PREFIX/share/man/man1/devfix.1"
  fi
}

if [ -w "$PREFIX" ] || { [ -d "$PREFIX/bin" ] && [ -w "$PREFIX/bin" ]; }; then
  run_install
else
  echo "Installing DevFix to $PREFIX (administrator password may be required)..."
  sudo install -d "$PREFIX/bin" "$PREFIX/share/man/man1"
  sudo install -m 0755 "$BIN_SRC" "$PREFIX/bin/devfix"
  if [ -f "$MAN_SRC" ]; then
    sudo install -m 0644 "$MAN_SRC" "$PREFIX/share/man/man1/devfix.1"
  fi
fi

echo "DevFix installed: $PREFIX/bin/devfix"
echo "Next: devfix doctor"
