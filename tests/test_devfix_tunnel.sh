#!/bin/bash
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TUNNEL="$ROOT/tunnel/cli/devfix-tunnel"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

bash -n "$TUNNEL" || fail "shell syntax"
pass "shell syntax"

"$TUNNEL" version | grep -q '0.1.0-alpha' || fail "version"
"$TUNNEL" help | grep -q 'System Proxy' || fail "help must state current limitation"
pass "basic CLI"

STATE="$TMP/tunnel-state"
LOGS="$TMP/tunnel-logs"
DEVFIX_SENTINEL="$TMP/devfix-state-sentinel"
printf 'DO_NOT_TOUCH\n' > "$DEVFIX_SENTINEL"

FAKE_TOR="$TMP/fake-tor"
FAKE_LYREBIRD="$TMP/fake-lyrebird"
cat > "$FAKE_TOR" <<'EOF'
#!/bin/bash
printf '%s\n' 'Bootstrapped 10% (conn): Connecting to a relay'
sleep 0.1
printf '%s\n' 'Bootstrapped 30% (handshake): Handshaking with a relay'
sleep 0.1
printf '%s\n' 'Bootstrapped 100% (done): Done'
# Remain alive so the CLI owns a realistic long-lived process.
while :; do sleep 1; done
EOF
cat > "$FAKE_LYREBIRD" <<'EOF'
#!/bin/bash
exit 0
EOF
chmod +x "$FAKE_TOR" "$FAKE_LYREBIRD"

export DEVFIX_TUNNEL_TEST_MODE=1
export DEVFIX_TUNNEL_STATE_DIR="$STATE"
export DEVFIX_TUNNEL_LOG_DIR="$LOGS"
export DEVFIX_TUNNEL_TOR_BIN="$FAKE_TOR"
export DEVFIX_TUNNEL_LYREBIRD_BIN="$FAKE_LYREBIRD"
export DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT=5
export DEVFIX_TUNNEL_STALL_TIMEOUT=3
export DEVFIX_TUNNEL_SOCKS_PORT=29150

"$TUNNEL" connect > "$TMP/connect.out" 2>&1 || { cat "$TMP/connect.out" >&2; fail "connect fixture"; }
grep -q 'Connected with DevFix Tunnel Snowflake' "$TMP/connect.out" || fail "connect success contract"
grep -q 'System Proxy is NOT modified' "$TMP/connect.out" || fail "transport core must not claim system proxy"
[ -f "$STATE/run/state" ] || fail "state file created"
grep -q '^STATE=CONNECTED$' "$STATE/run/state" || fail "connected state"
grep -q '^SOCKS_PORT=29150$' "$STATE/run/state" || fail "separate SOCKS port"
[ -d "$STATE/tor-data" ] || fail "separate tor-data"
[ "$STATE" != "$HOME/Library/Application Support/DevFix" ] || fail "DevFix state collision"
pass "isolated connect fixture"

"$TUNNEL" status > "$TMP/status.out"
grep -q '^State: CONNECTED$' "$TMP/status.out" || fail "status state"
grep -q 'owned/alive' "$TMP/status.out" || fail "status ownership"
pass "status"

"$TUNNEL" disconnect > "$TMP/disconnect.out" 2>&1 || { cat "$TMP/disconnect.out" >&2; fail "disconnect"; }
[ ! -f "$STATE/run/state" ] || fail "runtime state removed"
grep -q '^DO_NOT_TOUCH$' "$DEVFIX_SENTINEL" || fail "unrelated DevFix sentinel modified"
pass "disconnect and isolation"

# Disconnect is intentionally idempotent.
"$TUNNEL" disconnect >/dev/null 2>&1 || fail "idempotent disconnect"
pass "idempotent disconnect"

# Doctor with missing payload must fail safely and report, not mutate system configuration.
if DEVFIX_TUNNEL_TOR_BIN="$TMP/missing-tor" DEVFIX_TUNNEL_LYREBIRD_BIN="$TMP/missing-lyrebird" "$TUNNEL" doctor > "$TMP/doctor.out" 2>&1; then
  fail "doctor should fail when runtime is missing"
fi
grep -q 'Tor runtime: MISSING' "$TMP/doctor.out" || fail "doctor missing runtime evidence"
pass "doctor failure classification"

printf '%s\n' 'ALL DEVFIX TUNNEL TESTS PASSED'
