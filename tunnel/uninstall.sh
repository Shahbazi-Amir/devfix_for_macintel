#!/bin/bash
set -euo pipefail
PREFIX="/usr/local"
PLIST="/Library/LaunchDaemons/com.devfix.tunnel.recovery.plist"
GUARDIAN="$PREFIX/libexec/devfix-tunnel/devfix-tunnel-guardian"
PURGE=0
[ "${1:-}" = "--purge" ] && PURGE=1
if [ "$(id -u)" -ne 0 ]; then echo "Run with sudo: sudo /usr/local/share/devfix-tunnel/uninstall.sh [--purge]" >&2; exit 1; fi
if [ -x "$GUARDIAN" ]; then "$GUARDIAN" recover || { echo "Refusing uninstall because tunnel-owned System Proxy state could not be safely recovered." >&2; exit 1; }; fi
/bin/launchctl bootout system "$PLIST" >/dev/null 2>&1 || true
/bin/launchctl unload -w "$PLIST" >/dev/null 2>&1 || true
rm -f "$PLIST" "$PREFIX/bin/devfix-tunnel" "$PREFIX/bin/devfix-tunnel-chrome"
rm -rf "$PREFIX/libexec/devfix-tunnel" "$PREFIX/share/devfix-tunnel"
if [ "$PURGE" -eq 1 ]; then
  rm -rf "/Library/Application Support/DevFixTunnel"
  for home in /Users/*; do
    if [ -d "$home/Library/Application Support/DevFixTunnel" ]; then rm -rf "$home/Library/Application Support/DevFixTunnel"; fi
    if [ -d "$home/Library/Logs/DevFixTunnel" ]; then rm -rf "$home/Library/Logs/DevFixTunnel"; fi
  done
fi
echo "DevFix Tunnel removed."
