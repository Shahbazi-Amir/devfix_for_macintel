#!/bin/bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
TMP=$(mktemp -d "${TMPDIR:-/tmp}/devfix-install.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT TERM
PORTABLE="$TMP/portable"
DEST="$TMP/dest"
mkdir -p "$PORTABLE/bin" "$PORTABLE/libexec/devfix/tor/pluggable_transports" "$PORTABLE/share/man/man1" "$PORTABLE/share/devfix"
cp "$ROOT/bin/devfix" "$PORTABLE/bin/devfix"
cp "$ROOT/install.sh" "$PORTABLE/install.sh"
cp "$ROOT/uninstall.sh" "$PORTABLE/share/devfix/uninstall.sh"
cp "$ROOT/man/devfix.1" "$PORTABLE/share/man/man1/devfix.1"
for f in README.md SECURITY.md THIRD_PARTY_NOTICES.md LICENSE; do cp "$ROOT/$f" "$PORTABLE/share/devfix/$f"; done
printf '#!/bin/bash\nexit 0\n' > "$PORTABLE/libexec/devfix/tor/tor"
printf '#!/bin/bash\nexit 0\n' > "$PORTABLE/libexec/devfix/tor/pluggable_transports/lyrebird"
chmod +x "$PORTABLE/bin/devfix" "$PORTABLE/install.sh" "$PORTABLE/share/devfix/uninstall.sh" "$PORTABLE/libexec/devfix/tor/tor" "$PORTABLE/libexec/devfix/tor/pluggable_transports/lyrebird"
DESTDIR="$DEST" PREFIX=/usr/local "$PORTABLE/install.sh" >/dev/null
[ -x "$DEST/usr/local/bin/devfix" ]
[ -x "$DEST/usr/local/libexec/devfix/tor/tor" ]
[ -x "$DEST/usr/local/libexec/devfix/tor/pluggable_transports/lyrebird" ]
[ "$("$DEST/usr/local/bin/devfix" --version)" = "DevFix 2.0.0" ]
DESTDIR="$DEST" PREFIX=/usr/local "$DEST/usr/local/share/devfix/uninstall.sh" >/dev/null
[ ! -e "$DEST/usr/local/bin/devfix" ]
echo "install/uninstall smoke test passed"
