#!/bin/bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
[ "$(uname -s)" = "Darwin" ] || { echo "DevFix Tunnel supports macOS only." >&2; exit 1; }
[ "$(uname -m)" = "x86_64" ] || { echo "This package targets Intel x86_64 Macs." >&2; exit 1; }
sudo -v
sudo mkdir -p /usr/local/bin /usr/local/libexec/devfix-tunnel/tor /usr/local/share/devfix-tunnel "/Library/Application Support/DevFixTunnel"
sudo install -m 755 "$ROOT/bin/devfix-tunnel" /usr/local/bin/devfix-tunnel
sudo install -m 755 "$ROOT/libexec/devfix-tunnel-guardian" /usr/local/libexec/devfix-tunnel/devfix-tunnel-guardian
sudo rm -rf /usr/local/libexec/devfix-tunnel/tor
sudo mkdir -p /usr/local/libexec/devfix-tunnel/tor
sudo cp -R "$ROOT/libexec/tor/." /usr/local/libexec/devfix-tunnel/tor/
sudo chmod -R a+rX /usr/local/libexec/devfix-tunnel/tor
sudo install -m 644 "$ROOT/launchd/com.devfix.tunnel.recovery.plist" /Library/LaunchDaemons/com.devfix.tunnel.recovery.plist
sudo install -m 644 "$ROOT/README.md" /usr/local/share/devfix-tunnel/README.md
sudo chown root:wheel /Library/LaunchDaemons/com.devfix.tunnel.recovery.plist 2>/dev/null || true
sudo chmod 644 /Library/LaunchDaemons/com.devfix.tunnel.recovery.plist
sudo chmod 700 "/Library/Application Support/DevFixTunnel"
sudo /usr/local/libexec/devfix-tunnel/devfix-tunnel-guardian recover || true
sudo launchctl bootout system /Library/LaunchDaemons/com.devfix.tunnel.recovery.plist >/dev/null 2>&1 || true
sudo launchctl bootstrap system /Library/LaunchDaemons/com.devfix.tunnel.recovery.plist >/dev/null 2>&1 || sudo launchctl load -w /Library/LaunchDaemons/com.devfix.tunnel.recovery.plist >/dev/null 2>&1 || true
echo "DevFix Tunnel installed."
echo "Run: devfix-tunnel doctor"
