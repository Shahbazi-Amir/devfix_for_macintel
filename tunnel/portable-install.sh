#!/bin/bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
INSTALLED_CLI="/usr/local/bin/devfix-tunnel"
INSTALLED_GUARDIAN="/usr/local/libexec/devfix-tunnel/devfix-tunnel-guardian"
PLIST="/Library/LaunchDaemons/com.devfix.tunnel.recovery.plist"
TUNNEL_TOR_PATTERN='/usr/local/libexec/devfix-tunnel/tor/tor.*DevFixTunnel/run/torrc'

[ "$(uname -s)" = "Darwin" ] || { echo "DevFix Tunnel supports macOS only." >&2; exit 1; }
[ "$(uname -m)" = "x86_64" ] || { echo "This package targets Intel x86_64 Macs." >&2; exit 1; }
[ -f "$ROOT/share/transports.tsv" ] || { echo "Transport catalog missing from portable package." >&2; exit 1; }
[ -f "$ROOT/libexec/tor/geoip" ] || { echo "Tor geoip data missing from portable package." >&2; exit 1; }
[ -f "$ROOT/libexec/tor/geoip6" ] || { echo "Tor geoip6 data missing from portable package." >&2; exit 1; }
[ -f "$ROOT/bin/devfix-tunnel-chrome" ] || { echo "Selective Chrome launcher missing from portable package." >&2; exit 1; }

# Do not replace runtime files while an existing tunnel is active or bootstrapping.
if /usr/bin/pgrep -f "$TUNNEL_TOR_PATTERN" >/dev/null 2>&1; then
  echo "DevFix Tunnel is currently running. Disconnect it before upgrading." >&2
  exit 1
fi

# A connected state without a visible process is degraded/stale; refuse a silent
# overwrite and require the existing installation to be repaired first.
if [ -x "$INSTALLED_CLI" ]; then
  installed_status=$($INSTALLED_CLI status 2>&1 || true)
  installed_state=$(printf '%s\n' "$installed_status" | sed -n 's/^State: //p' | head -n 1)
  if [ "$installed_state" = "CONNECTED" ]; then
    echo "Installed DevFix Tunnel still reports CONNECTED. Disconnect/repair it before upgrading." >&2
    exit 1
  fi
fi

sudo -v

if [ -x "$INSTALLED_GUARDIAN" ]; then
  if ! sudo "$INSTALLED_GUARDIAN" recover; then
    echo "Refusing upgrade because previous tunnel-owned proxy state could not be safely recovered." >&2
    exit 1
  fi
fi

sudo mkdir -p /usr/local/bin /usr/local/libexec/devfix-tunnel/tor /usr/local/share/devfix-tunnel "/Library/Application Support/DevFixTunnel"
sudo install -m 755 "$ROOT/bin/devfix-tunnel" /usr/local/bin/devfix-tunnel
sudo install -m 755 "$ROOT/bin/devfix-tunnel-chrome" /usr/local/bin/devfix-tunnel-chrome
sudo install -m 755 "$ROOT/libexec/devfix-tunnel-guardian" /usr/local/libexec/devfix-tunnel/devfix-tunnel-guardian
sudo rm -rf /usr/local/libexec/devfix-tunnel/tor
sudo mkdir -p /usr/local/libexec/devfix-tunnel/tor
sudo cp -R "$ROOT/libexec/tor/." /usr/local/libexec/devfix-tunnel/tor/
sudo chmod -R a+rX /usr/local/libexec/devfix-tunnel/tor
sudo install -m 644 "$ROOT/share/transports.tsv" /usr/local/share/devfix-tunnel/transports.tsv
sudo install -m 644 "$ROOT/launchd/com.devfix.tunnel.recovery.plist" "$PLIST"
sudo install -m 644 "$ROOT/README.md" /usr/local/share/devfix-tunnel/README.md
sudo chown root:wheel "$PLIST" 2>/dev/null || true
sudo chmod 644 "$PLIST"
sudo chmod 700 "/Library/Application Support/DevFixTunnel"

if ! sudo /usr/local/libexec/devfix-tunnel/devfix-tunnel-guardian recover; then
  echo "New DevFix Tunnel guardian could not verify a safe proxy state." >&2
  exit 1
fi

sudo launchctl bootout system "$PLIST" >/dev/null 2>&1 || true
if ! sudo launchctl bootstrap system "$PLIST" >/dev/null 2>&1; then
  if ! sudo launchctl load -w "$PLIST" >/dev/null 2>&1; then
    echo "DevFix Tunnel recovery LaunchDaemon could not be activated." >&2
    exit 1
  fi
fi

echo "DevFix Tunnel installed."
echo "Run: devfix-tunnel doctor"
echo "Selective Chrome: devfix-tunnel-chrome https://example.com/"
