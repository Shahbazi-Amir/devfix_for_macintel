#!/bin/bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
LAUNCHER="$ROOT/tunnel/scripts/devfix-tunnel-chrome.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT INT TERM

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

FAKE_CLI="$TMP/devfix-tunnel"
FAKE_CHROME="$TMP/chrome"
STATE="$TMP/state"
CLI_LOG="$TMP/cli.log"
CHROME_LOG="$TMP/chrome.log"
PROFILE="$TMP/profile"

cat > "$FAKE_CLI" <<EOF
#!/bin/bash
STATE="$STATE"
LOG="$CLI_LOG"
case "\${1:-}" in
  status)
    if [ -f "\$STATE" ]; then
      printf '%s\n' 'DevFix Tunnel 0.3.0-rc1' 'State: CONNECTED' 'Mode: SOCKS' 'SOCKS: socks5h://127.0.0.1:29150' 'Health: OK'
    else
      printf '%s\n' 'DevFix Tunnel 0.3.0-rc1' 'State: DISCONNECTED' 'Mode: NONE'
    fi
    ;;
  connect)
    printf '%s\n' "\$*" >> "\$LOG"
    : > "\$STATE"
    ;;
  *) exit 2 ;;
esac
EOF

cat > "$FAKE_CHROME" <<EOF
#!/bin/bash
printf '%s\n' "\$@" > "$CHROME_LOG"
EOF
chmod +x "$FAKE_CLI" "$FAKE_CHROME"

export DEVFIX_TUNNEL_CLI_BIN="$FAKE_CLI"
export DEVFIX_TUNNEL_CHROME_BIN="$FAKE_CHROME"
export DEVFIX_TUNNEL_CHROME_PROFILE="$PROFILE"
export DEVFIX_TUNNEL_CHROME_TEST_MODE=1

bash -n "$LAUNCHER"

/bin/bash "$LAUNCHER" 'https://example.com/' > "$TMP/out" 2>&1 || { cat "$TMP/out" >&2; fail "launcher first run"; }
grep -Fxq 'connect socks --transport auto --foreign-only' "$CLI_LOG" || fail "launcher did not establish isolated SOCKS route"
grep -Fxq -- "--user-data-dir=$PROFILE" "$CHROME_LOG" || fail "isolated Chrome profile missing"
grep -Fxq -- '--proxy-server=socks5://127.0.0.1:29150' "$CHROME_LOG" || fail "Chrome SOCKS proxy flag missing"
grep -Fxq -- '--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1' "$CHROME_LOG" || fail "Chrome resolver isolation flag missing"
grep -Fxq -- '--force-webrtc-ip-handling-policy=disable_non_proxied_udp' "$CHROME_LOG" || fail "WebRTC non-proxied UDP restriction missing"
grep -Fxq -- 'https://example.com/' "$CHROME_LOG" || fail "requested URL missing"
[ -d "$PROFILE" ] || fail "isolated profile directory missing"
pass "isolated Chrome starts SOCKS route and receives leak-reduction flags"

: > "$CLI_LOG"
/bin/bash "$LAUNCHER" 'https://check.torproject.org/' > "$TMP/out2" 2>&1 || { cat "$TMP/out2" >&2; fail "launcher existing route"; }
[ ! -s "$CLI_LOG" ] || fail "launcher reconnected despite existing validated route"
grep -Fxq -- 'https://check.torproject.org/' "$CHROME_LOG" || fail "second URL missing"
pass "isolated Chrome reuses existing route without global proxy mutation"

echo "ALL DEVFIX TUNNEL CHROME TESTS PASSED"
