#!/bin/bash
set -euo pipefail
PREFIX=${PREFIX:-/usr/local}
DESTDIR=${DESTDIR:-}
TARGET="$DESTDIR$PREFIX"
PURGE=0
[ "${1:-}" != "--purge" ] || PURGE=1

NEED_SUDO=0
if [ -z "$DESTDIR" ]; then
  if [ ! -w "$PREFIX" ]; then
    command -v sudo >/dev/null 2>&1 || { echo "sudo is required to uninstall from $PREFIX" >&2; exit 1; }
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

as_root rm -f "$TARGET/bin/devfix" "$TARGET/share/man/man1/devfix.1"
as_root rm -rf "$TARGET/libexec/devfix" "$TARGET/share/devfix"

echo "DevFix program files removed."
if [ "$PURGE" -eq 1 ]; then
  rm -rf "$HOME/Library/Application Support/DevFix" "$HOME/Library/Logs/DevFix" \
    "${XDG_STATE_HOME:-$HOME/.local/state}/devfix"
  echo "User configuration, state, and logs removed."
else
  echo "User configuration and logs were kept. Use --purge to remove them."
fi
