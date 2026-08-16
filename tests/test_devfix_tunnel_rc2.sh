#!/bin/bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TUNNEL="$ROOT/tunnel/cli/devfix-tunnel"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT INT TERM

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

FAKE_TOR="$TMP/fake-tor"
FAKE_LYREBIRD="$TMP/fake-lyrebird"
CATALOG="$TMP/transports.tsv"
GEOIP="$TMP/geoip"
GEOIP6="$TMP/geoip6"
STATE="$TMP/state"
LOGS="$TMP/logs"

cat > "$FAKE_LYREBIRD" <<'EOF'
#!/bin/bash
exit 0
EOF

cat > "$CATALOG" <<'EOF'
# transport<TAB>candidate<TAB>bridge-line
snowflake	1	snowflake 192.0.2.3:80 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA url=https://example.invalid/ fronts=example.invalid ice=stun:example.invalid:3478
snowflake	2	snowflake 192.0.2.4:80 BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB url=https://example.invalid/ fronts=example.invalid ice=stun:example.invalid:3478
meek	1	meek_lite 192.0.2.20:80 url=https://example.invalid front=example.invalid
obfs4	1	obfs4 192.0.2.40:443 CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC cert=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA iat-mode=0
obfs4	2	obfs4 192.0.2.41:443 DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD cert=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB iat-mode=0
obfs4	3	obfs4 192.0.2.42:443 EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE cert=CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC iat-mode=0
obfs4	4	obfs4 192.0.2.43:443 FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF cert=DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD iat-mode=0
EOF

printf '%s\n' '0,4294967295,de' > "$GEOIP"
printf '%s\n' '::/0,de' > "$GEOIP6"
chmod +x "$FAKE_LYREBIRD"

cat > "$FAKE_TOR" <<'EOF'
#!/bin/bash
torrc=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-f" ] && [ "$#" -ge 2 ]; then
    torrc="$2"
    break
  fi
  shift
done
bridge=$(grep '^Bridge ' "$torrc" 2>/dev/null || true)
case "$bridge" in
  *'192.0.2.42:443'*)
    printf '%s\n' 'Bootstrapped 10% (conn_done): Connected to a relay'
    printf '%s\n' 'Bootstrapped 30% (loading_status): Loading networkstatus consensus'
    printf '%s\n' 'Bootstrapped 100% (done): Done'
    while :; do /bin/sleep 1; done
    ;;
  *)
    printf '%s\n' 'Bootstrapped 10% (conn_done): Connected to a relay'
    while :; do /bin/sleep 1; done
    ;;
esac
EOF
chmod +x "$FAKE_TOR"

export DEVFIX_TUNNEL_TEST_MODE=1
export DEVFIX_TUNNEL_TOR_BIN="$FAKE_TOR"
export DEVFIX_TUNNEL_LYREBIRD_BIN="$FAKE_LYREBIRD"
export DEVFIX_TUNNEL_TRANSPORT_CATALOG="$CATALOG"
export DEVFIX_TUNNEL_GEOIP="$GEOIP"
export DEVFIX_TUNNEL_GEOIP6="$GEOIP6"
export DEVFIX_TUNNEL_STATE_DIR="$STATE"
export DEVFIX_TUNNEL_LOG_DIR="$LOGS"
export DEVFIX_TUNNEL_STALL_TIMEOUT=1
export DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT=5
export DEVFIX_TUNNEL_SOCKS_PORT=29250
unset DEVFIX_TUNNEL_MAX_AUTO_ATTEMPTS || true

"$TUNNEL" version | grep -q '0.3.0-rc2' || fail 'RC2 version missing'

"$TUNNEL" connect socks --transport auto --foreign-only > "$TMP/connect.out" 2>&1 || {
  cat "$TMP/connect.out" >&2
  fail 'auto fallback did not reach a later obfs4 candidate'
}

grep -q 'Transport attempt 6: obfs4 candidate 3' "$TMP/connect.out" || fail 'auto mode still stopped at the former five-attempt ceiling'
grep -q 'Transport ready: obfs4 candidate 3' "$TMP/connect.out" || fail 'later obfs4 candidate did not become active'
grep -q '^TRANSPORT=obfs4$' "$STATE/run/state" || fail 'successful transport state missing'
grep -q '^CANDIDATE=3$' "$STATE/run/state" || fail 'successful candidate state missing'
pass 'auto mode exhausts catalog beyond five attempts'

grep -Fq 'GeoIPExcludeUnknown 0' "$STATE/run/torrc" || fail 'GeoIP unknown policy still excludes entry bridges'
grep -Fq 'ExcludeExitNodes {ir},{??}' "$STATE/run/torrc" || fail 'foreign-only exit exclusion missing'
if grep -Fq 'GeoIPExcludeUnknown 1' "$STATE/run/torrc"; then
  fail 'unknown-country exclusion still applies globally'
fi
pass 'foreign-only policy is exit-scoped and bridge-safe'

grep -Fq "STALL_TIMEOUT_HANDSHAKE=\"\${DEVFIX_TUNNEL_STALL_TIMEOUT_HANDSHAKE:-150}\"" "$TUNNEL" || fail '150s handshake-stage stall limit missing'
grep -Fq "STALL_TIMEOUT_CONSENSUS=\"\${DEVFIX_TUNNEL_STALL_TIMEOUT_CONSENSUS:-240}\"" "$TUNNEL" || fail '240s consensus-stage stall limit missing'
grep -Fq 'stall_timeout_for_percent' "$TUNNEL" || fail 'phase-aware stall function missing'
pass 'phase-aware bootstrap stall policy is present'

"$TUNNEL" disconnect >/dev/null 2>&1 || fail 'RC2 cleanup'

echo 'ALL DEVFIX TUNNEL RC2 PHYSICAL-FAILURE REGRESSIONS PASSED'
