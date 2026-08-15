#!/bin/bash
set -eu

PREFIX="${DEVFIX_PREFIX:-/usr/local}"
PURGE=0
if [ "${1:-}" = "--purge" ]; then
  PURGE=1
elif [ -n "${1:-}" ]; then
  echo "Usage: ./uninstall.sh [--purge]" >&2
  exit 2
fi

remove_path() {
  path="$1"
  if [ ! -e "$path" ]; then
    return
  fi
  if [ -w "$(dirname "$path")" ]; then
    rm -f "$path"
  else
    sudo rm -f "$path"
  fi
}

remove_path "$PREFIX/bin/devfix"
remove_path "$PREFIX/share/man/man1/devfix.1"

echo "DevFix program files removed."

if [ "$PURGE" -eq 1 ]; then
  CONFIG_DIR="${DEVFIX_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/devfix}"
  if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    echo "Configuration removed: $CONFIG_DIR"
  fi
else
  echo "Configuration preserved. Use --purge to remove it too."
fi
