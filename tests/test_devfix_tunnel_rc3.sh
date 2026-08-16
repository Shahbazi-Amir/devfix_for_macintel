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
chmod +x "$FAKE_LYREBIRD"

cat > "$CATALOG" <<'EOF'
# transport<TAB>candidate<TAB>bridge-line
obfs4	1	obfs4 192.0.2.40:443 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA cert=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA iat-mode=0
obfs4	2	obfs4 192.0.2.41:443 BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB cert=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB iat-mode=0
EOF
printf '%s\n' '0,4294967295,de' > "$GEOIP"
printf '%s\n' '::/0,de' > "$GEOIP6"

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
[ -n "$torrc" ] || exit 90
cache=$(sed -n 's/^CacheDirectory "\(.*\)"$/\1/p' "$torrc" | head -n 1)
[ -n "$cache" ] || exit 91
mkdir -p "$cache"
if [ -f "$cache/rc3-warm.marker" ]; then
  printf '%s\n' 'Bootstrapped 100% (done): Done'
  while :; do /bin/sleep 1; done
fi
printf '%s\n' warm > "$cache/rc3-warm.marker"
printf '%s\n' 'Bootstrapped 10% (conn_done): Connected to a relay'
while :; do /bin/sleep 1; done
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
export DEVFIX_TUNNEL_SOCKS_PORT=29350

"$TUNNEL" version | grep -q '0.3.0-rc3' || fail 'RC3 version missing'

"$TUNNEL" connect socks --transport obfs4 --foreign-only > "$TMP/first.out" 2>&1 || {
  cat "$TMP/first.out" >&2
  fail 'first RC3 connection did not reuse warmed cache on fallback'
}
grep -q 'Transport attempt 2: obfs4 candidate 2' "$TMP/first.out" || fail 'second candidate not reached'
grep -q 'Transport ready: obfs4 candidate 2' "$TMP/first.out" || fail 'second candidate did not reuse cache'
CACHE_DIR="$STATE/tor-cache"
[ -f "$CACHE_DIR/rc3-warm.marker" ] || fail 'persistent cache marker missing after fallback'
grep -Fq 'CacheDirectory ' "$STATE/run/torrc" || fail 'CacheDirectory missing from generated torrc'
grep -Fq 'AvoidDiskWrites 0' "$STATE/run/torrc" || fail 'normal cache writes are not enabled'
"$TUNNEL" disconnect >/dev/null 2>&1 || fail 'first disconnect failed'
[ -f "$CACHE_DIR/rc3-warm.marker" ] || fail 'disconnect deleted persistent directory cache'
pass 'directory cache survives candidate fallback and disconnect'

"$TUNNEL" connect socks --transport obfs4 --foreign-only > "$TMP/second.out" 2>&1 || {
  cat "$TMP/second.out" >&2
  fail 'second RC3 connection did not reuse persistent cache'
}
grep -q 'Transport attempt 1: obfs4 candidate 1' "$TMP/second.out" || fail 'second session first candidate missing'
grep -q 'Transport ready: obfs4 candidate 1' "$TMP/second.out" || fail 'persistent cache was not reused across sessions'
"$TUNNEL" disconnect >/dev/null 2>&1 || fail 'second disconnect failed'
pass 'directory cache survives across sessions while attempt DataDirectories remain disposable'

literal_descriptor="STALL_TIMEOUT_DESCRIPTORS=\"\${DEVFIX_TUNNEL_STALL_TIMEOUT_DESCRIPTORS:-900}\""
literal_bootstrap="BOOTSTRAP_TIMEOUT=\"\${DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT:-1200}\""
grep -Fq "$literal_descriptor" "$TUNNEL" || fail 'descriptor-stage timeout missing'
grep -Fq "$literal_bootstrap" "$TUNNEL" || fail 'extended overall bootstrap ceiling missing'
grep -Fq 'DIRECTORY_INFO_STALL' "$TUNNEL" || fail 'directory-stall classifier missing'
pass 'late directory phase receives a longer bounded grace period'

echo 'ALL DEVFIX TUNNEL RC3 REGRESSIONS PASSED'
