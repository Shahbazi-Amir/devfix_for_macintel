#!/bin/bash
# Launch an isolated Chrome profile through DevFix Tunnel SOCKS without changing macOS System Proxy.
set -u

CLI_BIN="${DEVFIX_TUNNEL_CLI_BIN:-/usr/local/bin/devfix-tunnel}"
PROFILE_DIR="${DEVFIX_TUNNEL_CHROME_PROFILE:-$HOME/Library/Application Support/DevFixTunnel/ChromeProfile}"
URL="${1:-https://check.torproject.org/}"

err() { printf 'Error: %s\n' "$*" >&2; }
die() { err "$*"; exit 1; }

case "$URL" in
  http://*|https://*) ;;
  *) die "URL must start with http:// or https://" ;;
esac

[ -x "$CLI_BIN" ] || die "devfix-tunnel CLI not found: $CLI_BIN"

find_chrome() {
  if [ -n "${DEVFIX_TUNNEL_CHROME_BIN:-}" ]; then
    [ -x "$DEVFIX_TUNNEL_CHROME_BIN" ] || return 1
    printf '%s' "$DEVFIX_TUNNEL_CHROME_BIN"
    return 0
  fi
  for candidate in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "$HOME/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "$HOME/Applications/Chromium.app/Contents/MacOS/Chromium"
  do
    if [ -x "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

status_output() { "$CLI_BIN" status 2>/dev/null || true; }

ensure_socks_route() {
  current=$(status_output)
  state=$(printf '%s\n' "$current" | sed -n 's/^State: //p' | head -n 1)
  if [ "$state" != "CONNECTED" ]; then
    printf '%s\n' "DevFix Tunnel is not connected; starting isolated SOCKS mode..."
    "$CLI_BIN" connect socks --transport auto --foreign-only || return 1
    current=$(status_output)
  fi

  port=$(printf '%s\n' "$current" | sed -nE 's#^SOCKS: socks5h://127\.0\.0\.1:([0-9]+)$#\1#p' | head -n 1)
  case "$port" in
    ''|*[!0-9]*) return 1 ;;
  esac
  printf '%s' "$port"
}

CHROME_BIN=$(find_chrome) || die "Google Chrome/Chromium was not found"
PORT=$(ensure_socks_route) || die "could not establish a validated DevFix Tunnel SOCKS route"

mkdir -p "$PROFILE_DIR" || die "cannot create isolated Chrome profile directory"
chmod 700 "$PROFILE_DIR" 2>/dev/null || true

PROXY="socks5://127.0.0.1:$PORT"
HOST_RULES="MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"
WEBRTC_POLICY="disable_non_proxied_udp"

printf 'Launching isolated tunneled Chrome profile.\n'
printf 'SOCKS: %s\n' "$PROXY"
printf 'Profile: %s\n' "$PROFILE_DIR"
printf 'Normal Chrome instances are not modified by this launcher.\n'

if [ "${DEVFIX_TUNNEL_CHROME_TEST_MODE:-0}" = "1" ]; then
  "$CHROME_BIN" \
    "--user-data-dir=$PROFILE_DIR" \
    "--proxy-server=$PROXY" \
    "--host-resolver-rules=$HOST_RULES" \
    "--force-webrtc-ip-handling-policy=$WEBRTC_POLICY" \
    --no-first-run \
    "$URL"
  exit $?
fi

/usr/bin/nohup "$CHROME_BIN" \
  "--user-data-dir=$PROFILE_DIR" \
  "--proxy-server=$PROXY" \
  "--host-resolver-rules=$HOST_RULES" \
  "--force-webrtc-ip-handling-policy=$WEBRTC_POLICY" \
  --no-first-run \
  "$URL" >/dev/null 2>&1 &

printf '%s\n' "Tunneled Chrome launched."
