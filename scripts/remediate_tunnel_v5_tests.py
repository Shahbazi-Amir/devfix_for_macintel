#!/usr/bin/env python3
from pathlib import Path

p = Path("tests/test_devfix_tunnel.sh")
text = p.read_text()

old = '"$TUNNEL" version | grep -q \'0.2.0-rc1\' || fail "version"'
new = '"$TUNNEL" version | grep -q \'0.3.0-rc1\' || fail "version"'
if text.count(old) != 1:
    raise SystemExit(f"version assertion match count={text.count(old)}")
text = text.replace(old, new, 1)

needle = 'chmod +x "$FAKE_TOR" "$FAKE_LYREBIRD" "$FAKE_NETWORKSETUP" "$FAKE_ROUTE" "$FAKE_SLEEP"\n\n'
if text.count(needle) != 1:
    raise SystemExit(f"fixture insertion match count={text.count(needle)}")
fixture = r'''chmod +x "$FAKE_TOR" "$FAKE_LYREBIRD" "$FAKE_NETWORKSETUP" "$FAKE_ROUTE" "$FAKE_SLEEP"

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

'''
text = text.replace(needle, fixture, 1)

old_export = 'export DEVFIX_TUNNEL_TEST_MODE=1 DEVFIX_TUNNEL_TOR_BIN="$FAKE_TOR" DEVFIX_TUNNEL_LYREBIRD_BIN="$FAKE_LYREBIRD" DEVFIX_TUNNEL_GUARDIAN_BIN="$GUARDIAN" DEVFIX_TUNNEL_NETWORKSETUP_BIN="$FAKE_NETWORKSETUP" DEVFIX_TUNNEL_ROUTE_BIN="$FAKE_ROUTE" DEVFIX_TUNNEL_SLEEP_BIN="$FAKE_SLEEP" DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT=5 DEVFIX_TUNNEL_STALL_TIMEOUT=3 DEVFIX_TUNNEL_GUARDIAN_START_TIMEOUT=5 DEVFIX_TUNNEL_GUARDIAN_STOP_TIMEOUT=5 DEVFIX_TUNNEL_SOCKS_PORT=29150'
new_export = old_export + ' DEVFIX_TUNNEL_TRANSPORT_CATALOG="$FAKE_CATALOG" DEVFIX_TUNNEL_GEOIP="$FAKE_GEOIP" DEVFIX_TUNNEL_GEOIP6="$FAKE_GEOIP6" DEVFIX_TUNNEL_MAX_AUTO_ATTEMPTS=4'
if text.count(old_export) != 1:
    raise SystemExit(f"export fixture match count={text.count(old_export)}")
text = text.replace(old_export, new_export, 1)

insert_at = '\nnew_case doctor\n'
if text.count(insert_at) != 1:
    raise SystemExit(f"doctor insertion match count={text.count(insert_at)}")

v5 = r'''
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
"$TUNNEL" run /bin/sh -c 'printf "%s|%s\n" "$ALL_PROXY" "$all_proxy"' > "$CASE/run.out" || fail "run command"
grep -q 'socks5h://127.0.0.1:29150|socks5h://127.0.0.1:29150' "$CASE/run.out" || fail "run child proxy environment"
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
'''
text = text.replace(insert_at, "\n" + v5.strip() + insert_at, 1)

p.write_text(text)
