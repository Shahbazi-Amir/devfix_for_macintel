#!/bin/bash
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TUNNEL="$ROOT/tunnel/cli/devfix-tunnel"
GUARDIAN="$ROOT/tunnel/libexec/devfix-tunnel-guardian"
TMP=$(mktemp -d)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT INT TERM
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

bash -n "$TUNNEL" || fail "tunnel syntax"
bash -n "$GUARDIAN" || fail "guardian syntax"
"$TUNNEL" version | grep -q '0.3.0-rc3' || fail "version"
"$TUNNEL" help | grep -q 'System Proxy' || fail "help"
pass "syntax and basic CLI"

FAKE_TOR="$TMP/fake-tor"; FAKE_LYREBIRD="$TMP/fake-lyrebird"; FAKE_NETWORKSETUP="$TMP/networksetup"; FAKE_ROUTE="$TMP/route"; FAKE_SLEEP="$TMP/sleep"
cat > "$FAKE_TOR" <<'EOF'
#!/bin/bash
printf '%s\n' 'Bootstrapped 10% (conn): Connecting'
sleep 0.05
printf '%s\n' 'Bootstrapped 30% (handshake): Handshaking'
sleep 0.05
printf '%s\n' 'Bootstrapped 100% (done): Done'
while :; do sleep 1; done
EOF
cat > "$FAKE_LYREBIRD" <<'EOF'
#!/bin/bash
exit 0
EOF
cat > "$FAKE_SLEEP" <<'EOF'
#!/bin/bash
/bin/sleep "${1:-0}"
EOF
cat > "$FAKE_ROUTE" <<'EOF'
#!/bin/bash
iface=$(cat "$FAKE_ROUTE_IFACE_FILE")
cat <<EOT
   route to: default
destination: default
  interface: $iface
EOT
EOF
cat > "$FAKE_NETWORKSETUP" <<'EOF'
#!/bin/bash
set -eu
state="$FAKE_PROXY_STATE_FILE"; web="${FAKE_WEB_ENABLED:-No}"; secure="${FAKE_SECURE_ENABLED:-No}"; auto="${FAKE_AUTO_ENABLED:-No}"; discovery="${FAKE_DISCOVERY_ENABLED:-Off}"
read_state() { SOCKS_ENABLED=$(sed -n 's/^ENABLED=//p' "$state"); SOCKS_SERVER=$(sed -n 's/^SERVER=//p' "$state"); SOCKS_PORT=$(sed -n 's/^PORT=//p' "$state"); }
write_state() { printf 'ENABLED=%s\nSERVER=%s\nPORT=%s\n' "$SOCKS_ENABLED" "$SOCKS_SERVER" "$SOCKS_PORT" > "$state"; }
cmd="${1:-}"; shift || true
case "$cmd" in
-listnetworkserviceorder) printf '%s\n' 'An asterisk (*) denotes that a network service is disabled.' '(1) Wi-Fi' '(Hardware Port: Wi-Fi, Device: en0)' '(2) Ethernet' '(Hardware Port: Ethernet, Device: en1)' ;;
-getinfo) case "${1:-}" in 'Wi-Fi'|'Ethernet') printf 'IP address: 192.0.2.2\n' ;; *) exit 1 ;; esac ;;
-getsocksfirewallproxy) read_state; printf 'Enabled: %s\nServer: %s\nPort: %s\nAuthenticated Proxy Enabled: %s\n' "$SOCKS_ENABLED" "$SOCKS_SERVER" "$SOCKS_PORT" "${FAKE_SOCKS_AUTH_ENABLED:-0}" ;;
-getwebproxy) printf 'Enabled: %s\nServer: \nPort: 0\nAuthenticated Proxy Enabled: 0\n' "$web" ;;
-getsecurewebproxy) printf 'Enabled: %s\nServer: \nPort: 0\nAuthenticated Proxy Enabled: 0\n' "$secure" ;;
-getautoproxyurl) printf 'URL: (null)\nEnabled: %s\n' "$auto" ;;
-getproxyautodiscovery) printf 'Auto Proxy Discovery: %s\n' "$discovery" ;;
-getproxybypassdomains) printf '%s\n' "There aren't any bypass domains set on Wi-Fi." ;;
-setsocksfirewallproxy) service="$1"; server="$2"; port="$3"; case "$service" in 'Wi-Fi'|'Ethernet') ;; *) exit 1 ;; esac; read_state; SOCKS_ENABLED=Yes; SOCKS_SERVER="$server"; SOCKS_PORT="$port"; write_state ;;
-setsocksfirewallproxystate) service="$1"; desired="$2"; case "$service" in 'Wi-Fi'|'Ethernet') ;; *) exit 1 ;; esac; read_state; case "$desired" in on|On|ON) SOCKS_ENABLED=Yes ;; *) SOCKS_ENABLED=No ;; esac; write_state ;;
*) printf 'unexpected networksetup command: %s %s\n' "$cmd" "$*" >&2; exit 2 ;;
esac
EOF
chmod +x "$FAKE_TOR" "$FAKE_LYREBIRD" "$FAKE_NETWORKSETUP" "$FAKE_ROUTE" "$FAKE_SLEEP"

FAKE_CATALOG="$TMP/transports.tsv"
FAKE_GEOIP="$TMP/geoip"
FAKE_GEOIP6="$TMP/geoip6"
cat > "$FAKE_CATALOG" <<'EOF'
# transport<TAB>candidate<TAB>bridge-line
snowflake	1	snowflake 192.0.2.3:80 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA fingerprint=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA url=https://example.invalid/ fronts=example.invalid ice=stun:example.invalid:3478
snowflake	2	snowflake 192.0.2.4:80 BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB fingerprint=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB url=https://example.invalid/ fronts=example.invalid ice=stun:example.invalid:3478
meek	1	meek_lite 192.0.2.20:80 url=https://example.invalid front=example.invalid
obfs4	1	obfs4 192.0.2.40:443 CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC cert=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA iat-mode=0
EOF
printf '%s\n' '0,4294967295,de' > "$FAKE_GEOIP"
printf '%s\n' '::/0,de' > "$FAKE_GEOIP6"

export DEVFIX_TUNNEL_TEST_MODE=1 DEVFIX_TUNNEL_TOR_BIN="$FAKE_TOR" DEVFIX_TUNNEL_LYREBIRD_BIN="$FAKE_LYREBIRD" DEVFIX_TUNNEL_GUARDIAN_BIN="$GUARDIAN" DEVFIX_TUNNEL_NETWORKSETUP_BIN="$FAKE_NETWORKSETUP" DEVFIX_TUNNEL_ROUTE_BIN="$FAKE_ROUTE" DEVFIX_TUNNEL_SLEEP_BIN="$FAKE_SLEEP" DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT=5 DEVFIX_TUNNEL_STALL_TIMEOUT=3 DEVFIX_TUNNEL_GUARDIAN_START_TIMEOUT=5 DEVFIX_TUNNEL_GUARDIAN_STOP_TIMEOUT=5 DEVFIX_TUNNEL_SOCKS_PORT=29150 DEVFIX_TUNNEL_TRANSPORT_CATALOG="$FAKE_CATALOG" DEVFIX_TUNNEL_GEOIP="$FAKE_GEOIP" DEVFIX_TUNNEL_GEOIP6="$FAKE_GEOIP6" DEVFIX_TUNNEL_MAX_AUTO_ATTEMPTS=4

new_case() { CASE="$TMP/$1"; mkdir -p "$CASE"; export DEVFIX_TUNNEL_STATE_DIR="$CASE/user-state" DEVFIX_TUNNEL_LOG_DIR="$CASE/user-logs" DEVFIX_TUNNEL_SYSTEM_STATE_DIR="$CASE/system-state" FAKE_PROXY_STATE_FILE="$CASE/proxy.state" FAKE_ROUTE_IFACE_FILE="$CASE/route.iface"; unset FAKE_WEB_ENABLED FAKE_SECURE_ENABLED FAKE_AUTO_ENABLED FAKE_DISCOVERY_ENABLED FAKE_SOCKS_AUTH_ENABLED || true; printf 'ENABLED=No\nSERVER=old.invalid\nPORT=1080\n' > "$FAKE_PROXY_STATE_FILE"; printf 'en0\n' > "$FAKE_ROUTE_IFACE_FILE"; }
wait_for() { timeout="$1"; shift; i=0; while [ "$i" -lt "$timeout" ]; do if "$@"; then return 0; fi; /bin/sleep 0.1; i=$((i + 1)); done; return 1; }
proxy_is_enabled_owned() { grep -q '^ENABLED=Yes$' "$FAKE_PROXY_STATE_FILE" && grep -q '^SERVER=127.0.0.1$' "$FAKE_PROXY_STATE_FILE" && grep -q '^PORT=29150$' "$FAKE_PROXY_STATE_FILE"; }
proxy_is_restored() { grep -q '^ENABLED=No$' "$FAKE_PROXY_STATE_FILE" && grep -q '^SERVER=old.invalid$' "$FAKE_PROXY_STATE_FILE" && grep -q '^PORT=1080$' "$FAKE_PROXY_STATE_FILE"; }

new_case system_success
"$TUNNEL" connect system > "$CASE/connect.out" 2>&1 || { cat "$CASE/connect.out" >&2; fail "system connect"; }
grep -q 'Connected with DevFix Tunnel System Proxy' "$CASE/connect.out" || fail "system success contract"
grep -q '^MODE=SYSTEM_PROXY$' "$DEVFIX_TUNNEL_STATE_DIR/run/state" || fail "system mode state"
grep -q '^PROXY_SERVICE=Wi-Fi$' "$DEVFIX_TUNNEL_STATE_DIR/run/state" || fail "service discovery"
proxy_is_enabled_owned || fail "proxy not owned after connect"
pass "system proxy connect"
"$TUNNEL" status > "$CASE/status.out" || fail "healthy status"; grep -q '^Health: OK$' "$CASE/status.out" || fail "health status"
"$TUNNEL" disconnect > "$CASE/disconnect.out" 2>&1 || { cat "$CASE/disconnect.out" >&2; fail "system disconnect"; }
proxy_is_restored || fail "proxy snapshot not restored"; [ ! -f "$DEVFIX_TUNNEL_STATE_DIR/run/state" ] || fail "state not cleared"; pass "exact disabled SOCKS state restored"

new_case socks_only
before=$(cat "$FAKE_PROXY_STATE_FILE"); "$TUNNEL" connect socks > "$CASE/connect.out" 2>&1 || fail "socks-only connect"; after=$(cat "$FAKE_PROXY_STATE_FILE"); [ "$before" = "$after" ] || fail "socks-only mutated proxy"; "$TUNNEL" disconnect >/dev/null 2>&1 || fail "socks-only disconnect"; pass "socks-only isolation"

new_case existing_socks
printf 'ENABLED=Yes\nSERVER=10.0.0.9\nPORT=9999\n' > "$FAKE_PROXY_STATE_FILE"
if "$TUNNEL" connect system > "$CASE/connect.out" 2>&1; then fail "existing SOCKS proxy should block system mode"; fi
grep -q 'EXISTING_SOCKS_PROXY' "$CASE/connect.out" || fail "SOCKS conflict classification"; grep -q '^SERVER=10.0.0.9$' "$FAKE_PROXY_STATE_FILE" || fail "existing SOCKS overwritten"; grep -q '^ENABLED=Yes$' "$FAKE_PROXY_STATE_FILE" || fail "existing SOCKS disabled"; pass "existing SOCKS conflict preserved"

new_case existing_http
export FAKE_WEB_ENABLED=Yes
if "$TUNNEL" connect system > "$CASE/connect.out" 2>&1; then fail "existing HTTP proxy should block system mode"; fi
grep -q 'EXISTING_HTTP_PROXY' "$CASE/connect.out" || fail "HTTP conflict classification"; proxy_is_restored || fail "proxy state changed despite HTTP conflict"; unset FAKE_WEB_ENABLED; pass "existing HTTP conflict preserved"

new_case tor_crash
"$TUNNEL" connect system > "$CASE/connect.out" 2>&1 || fail "crash case connect"; tor_pid=$(sed -n 's/^PID=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state"); kill "$tor_pid" 2>/dev/null || true
wait_for 50 proxy_is_restored || fail "guardian did not restore after Tor death"; wait_for 50 test -f "$DEVFIX_TUNNEL_STATE_DIR/run/system-proxy.failed" || fail "guardian failure marker missing"; grep -q 'TOR_PROCESS_DIED' "$DEVFIX_TUNNEL_STATE_DIR/run/system-proxy.failed" || fail "Tor crash classification"; rm -f "$DEVFIX_TUNNEL_STATE_DIR/run/state" "$DEVFIX_TUNNEL_STATE_DIR/run/tor.pid" "$DEVFIX_TUNNEL_STATE_DIR/run/torrc" || true; pass "Tor crash recovery"

new_case external_change
"$TUNNEL" connect system > "$CASE/connect.out" 2>&1 || fail "external change connect"; printf 'ENABLED=Yes\nSERVER=203.0.113.8\nPORT=4444\n' > "$FAKE_PROXY_STATE_FILE"; wait_for 50 test -f "$DEVFIX_TUNNEL_STATE_DIR/run/system-proxy.failed" || fail "ownership-loss marker missing"; grep -q 'PROXY_OWNERSHIP_LOST' "$DEVFIX_TUNNEL_STATE_DIR/run/system-proxy.failed" || fail "ownership-loss classification"; grep -q '^SERVER=203.0.113.8$' "$FAKE_PROXY_STATE_FILE" || fail "external proxy was overwritten"; tor_pid=$(sed -n 's/^PID=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state"); kill "$tor_pid" 2>/dev/null || true; rm -f "$DEVFIX_TUNNEL_STATE_DIR/run/state" "$DEVFIX_TUNNEL_STATE_DIR/run/tor.pid" "$DEVFIX_TUNNEL_STATE_DIR/run/torrc" || true; pass "external proxy ownership conflict is non-destructive"

new_case network_change
"$TUNNEL" connect system > "$CASE/connect.out" 2>&1 || fail "network change connect"; printf 'en1\n' > "$FAKE_ROUTE_IFACE_FILE"; wait_for 50 proxy_is_restored || fail "network change did not restore old proxy"; wait_for 50 test -f "$DEVFIX_TUNNEL_STATE_DIR/run/system-proxy.failed" || fail "network-change marker missing"; grep -q 'NETWORK_SERVICE_CHANGED' "$DEVFIX_TUNNEL_STATE_DIR/run/system-proxy.failed" || fail "network-change classification"; tor_pid=$(sed -n 's/^PID=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state"); kill "$tor_pid" 2>/dev/null || true; rm -f "$DEVFIX_TUNNEL_STATE_DIR/run/state" "$DEVFIX_TUNNEL_STATE_DIR/run/tor.pid" "$DEVFIX_TUNNEL_STATE_DIR/run/torrc" || true; pass "network service change recovery"

new_case idempotent_system
"$TUNNEL" connect system > "$CASE/connect1.out" 2>&1 || fail "idempotent system first connect"
session1=$(sed -n 's/^SESSION=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state")
proxy1=$(cat "$FAKE_PROXY_STATE_FILE")
"$TUNNEL" connect system > "$CASE/connect2.out" 2>&1 || fail "idempotent system second connect"
session2=$(sed -n 's/^SESSION=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state")
[ "$session1" = "$session2" ] || fail "repeated system connect created a new session"
[ "$proxy1" = "$(cat "$FAKE_PROXY_STATE_FILE")" ] || fail "repeated system connect changed proxy state"
grep -q 'already connected in System Proxy mode' "$CASE/connect2.out" || fail "idempotent system contract"
if "$TUNNEL" connect socks > "$CASE/switch.out" 2>&1; then fail "system to socks transition should require disconnect"; fi
grep -q 'disconnect before switching to SOCKS-only mode' "$CASE/switch.out" || fail "system to socks refusal contract"
proxy_is_enabled_owned || fail "mode-switch refusal damaged System Proxy"
"$TUNNEL" disconnect >/dev/null 2>&1 || fail "idempotent system cleanup"
pass "System Proxy idempotency and transition refusal"

new_case idempotent_socks
"$TUNNEL" connect socks > "$CASE/connect1.out" 2>&1 || fail "idempotent socks first connect"
session1=$(sed -n 's/^SESSION=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state")
"$TUNNEL" connect socks > "$CASE/connect2.out" 2>&1 || fail "idempotent socks second connect"
session2=$(sed -n 's/^SESSION=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state")
[ "$session1" = "$session2" ] || fail "repeated SOCKS connect created a new session"
grep -q 'already connected in SOCKS-only mode' "$CASE/connect2.out" || fail "idempotent SOCKS contract"
if "$TUNNEL" connect system > "$CASE/switch.out" 2>&1; then fail "socks to system transition should require disconnect"; fi
grep -q 'disconnect before switching to System Proxy mode' "$CASE/switch.out" || fail "socks to system refusal contract"
"$TUNNEL" restart > "$CASE/restart.out" 2>&1 || fail "mode-preserving restart"
grep -q '^MODE=SOCKS$' "$DEVFIX_TUNNEL_STATE_DIR/run/state" || fail "restart drifted from SOCKS to System Proxy"
proxy_is_restored || fail "SOCKS restart changed proxy"
"$TUNNEL" disconnect >/dev/null 2>&1 || fail "idempotent socks cleanup"
pass "SOCKS idempotency, transition refusal, and restart mode preservation"

new_case disabled_authenticated_socks
export FAKE_SOCKS_AUTH_ENABLED=1
if "$TUNNEL" connect system > "$CASE/connect.out" 2>&1; then fail "disabled authenticated SOCKS config should block System Proxy"; fi
grep -q 'EXISTING_AUTHENTICATED_SOCKS_CONFIG' "$CASE/connect.out" || fail "authenticated SOCKS conflict classification"
proxy_is_restored || fail "authenticated disabled SOCKS config was modified"
unset FAKE_SOCKS_AUTH_ENABLED
pass "disabled authenticated SOCKS configuration preserved"

# Static privilege-boundary guard: production user-marker writes must drop to UID.
grep -q 'USER_SUDO_BIN' "$GUARDIAN" || fail "guardian user privilege-drop binary missing"
grep -q 'user_exec .* /usr/bin/tee' "$GUARDIAN" || fail "guardian marker writes are not user-scoped"
grep -q 'safe_user_marker_exists' "$GUARDIAN" || fail "guardian stop marker read is not user-scoped"
pass "guardian user-marker privilege boundary"

new_case v5_foreign_policy
"$TUNNEL" connect socks --transport snowflake --foreign-only --exit-country de > "$CASE/connect.out" 2>&1 || { cat "$CASE/connect.out" >&2; fail "v5 foreign policy connect"; }
grep -q '^TRANSPORT=snowflake$' "$DEVFIX_TUNNEL_STATE_DIR/run/state" || fail "transport state missing"
grep -q '^EXIT_POLICY=FOREIGN_ONLY$' "$DEVFIX_TUNNEL_STATE_DIR/run/state" || fail "foreign policy state missing"
grep -q '^EXIT_COUNTRY=de$' "$DEVFIX_TUNNEL_STATE_DIR/run/state" || fail "exit country state missing"
grep -q 'GeoIPFile ' "$DEVFIX_TUNNEL_STATE_DIR/run/torrc" || fail "GeoIPFile missing from torrc"
grep -q 'GeoIPv6File ' "$DEVFIX_TUNNEL_STATE_DIR/run/torrc" || fail "GeoIPv6File missing from torrc"
grep -Fq 'ExcludeExitNodes {ir},{??}' "$DEVFIX_TUNNEL_STATE_DIR/run/torrc" || fail "foreign-only exclusion missing"
grep -Fq 'ExitNodes {de}' "$DEVFIX_TUNNEL_STATE_DIR/run/torrc" || fail "preferred exit country missing"
DEVFIX_TUNNEL_TEST_EXIT_IP=203.0.113.9 "$TUNNEL" exit > "$CASE/exit.out" 2>&1 || { cat "$CASE/exit.out" >&2; fail "exit verification"; }
grep -q '^Exit country: de$' "$CASE/exit.out" || fail "local GeoIP exit mapping"
grep -q '^Foreign-only verification: PASS$' "$CASE/exit.out" || fail "foreign-only exit verification"
"$TUNNEL" run /usr/bin/env > "$CASE/run.out" || fail "run command"
grep -q '^ALL_PROXY=socks5h://127.0.0.1:29150$' "$CASE/run.out" || fail "run child ALL_PROXY environment"
grep -q '^all_proxy=socks5h://127.0.0.1:29150$' "$CASE/run.out" || fail "run child all_proxy environment"
"$TUNNEL" disconnect >/dev/null 2>&1 || fail "v5 foreign policy cleanup"
pass "V5 foreign-exit policy, exit identity, and child run environment"

new_case v5_any_exit
"$TUNNEL" connect socks --transport snowflake --allow-any-exit > "$CASE/connect.out" 2>&1 || fail "allow-any-exit connect"
if grep -Fq 'ExcludeExitNodes {ir},{??}' "$DEVFIX_TUNNEL_STATE_DIR/run/torrc"; then fail "allow-any-exit still excludes Iran"; fi
"$TUNNEL" disconnect >/dev/null 2>&1 || fail "allow-any-exit cleanup"
if "$TUNNEL" connect socks --foreign-only --exit-country ir > "$CASE/invalid.out" 2>&1; then fail "foreign-only should reject Iran preferred exit"; fi
grep -q 'foreign-only policy conflicts' "$CASE/invalid.out" || fail "foreign/IR conflict classification"
pass "V5 exit policy opt-out and validation"

FAKE_TOR_FALLBACK="$TMP/fake-tor-fallback"
cat > "$FAKE_TOR_FALLBACK" <<'EOF'
#!/bin/bash
torrc=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-f" ] && [ "$#" -ge 2 ]; then torrc="$2"; break; fi
  shift
done
if grep -q '^Bridge snowflake ' "$torrc"; then
  printf '%s\n' 'Bootstrapped 10% (conn_done): Connected to a relay'
  printf '%s\n' 'Managed proxy "lyrebird": broker rendezvous peer received'
  printf '%s\n' 'Managed proxy "lyrebird": trying a new proxy: timeout waiting for DataChannel.OnOpen'
  while :; do /bin/sleep 1; done
fi
printf '%s\n' 'Bootstrapped 10% (conn): Connecting'
printf '%s\n' 'Bootstrapped 100% (done): Done'
while :; do /bin/sleep 1; done
EOF
chmod +x "$FAKE_TOR_FALLBACK"

new_case v5_fallback
DEVFIX_TUNNEL_TOR_BIN="$FAKE_TOR_FALLBACK" DEVFIX_TUNNEL_STALL_TIMEOUT=1 DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT=5 DEVFIX_TUNNEL_MAX_AUTO_ATTEMPTS=4 \
  "$TUNNEL" connect socks --transport auto > "$CASE/connect.out" 2>&1 || { cat "$CASE/connect.out" >&2; fail "auto fallback connect"; }
grep -q 'SNOWFLAKE_WEBRTC_DATACHANNEL_FAILURE' "$CASE/connect.out" || fail "WebRTC failure classification missing"
grep -q 'Transport ready: meek candidate 1' "$CASE/connect.out" || fail "auto fallback did not reach meek"
grep -q '^TRANSPORT=meek$' "$DEVFIX_TUNNEL_STATE_DIR/run/state" || fail "successful fallback transport state"
count=$(find "$DEVFIX_TUNNEL_LOG_DIR" -name 'attempt-*snowflake*.log' -type f | wc -l | tr -d ' ')
[ "$count" -ge 2 ] || fail "expected per-attempt Snowflake logs"
"$TUNNEL" disconnect >/dev/null 2>&1 || fail "fallback cleanup"
pass "V5 bounded Snowflake-to-meek fallback and attempt logging"
new_case doctor
if DEVFIX_TUNNEL_TOR_BIN="$CASE/missing-tor" DEVFIX_TUNNEL_LYREBIRD_BIN="$CASE/missing-lyrebird" "$TUNNEL" doctor > "$CASE/doctor.out" 2>&1; then fail "doctor should fail with missing payload"; fi
grep -q 'Tor runtime: MISSING' "$CASE/doctor.out" || fail "doctor Tor evidence"; pass "doctor failure classification"
printf '%s\n' 'ALL DEVFIX TUNNEL SYSTEM-PROXY TESTS PASSED'
