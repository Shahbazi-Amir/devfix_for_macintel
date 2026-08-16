#!/bin/bash
set -euo pipefail

TOR_DIR=${1:-}
CATALOG=${2:-}

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

[ -n "$TOR_DIR" ] || fail "usage: test_devfix_tunnel_tor_config.sh TOR_DIR CATALOG"
[ -n "$CATALOG" ] || fail "catalog path is required"

TOR="$TOR_DIR/tor"
LYREBIRD="$TOR_DIR/pluggable_transports/lyrebird"
GEOIP="$TOR_DIR/geoip"
GEOIP6="$TOR_DIR/geoip6"

[ -x "$TOR" ] || fail "Tor binary missing"
[ -x "$LYREBIRD" ] || fail "lyrebird binary missing"
[ -f "$GEOIP" ] || fail "geoip missing"
[ -f "$GEOIP6" ] || fail "geoip6 missing"
[ -f "$CATALOG" ] || fail "transport catalog missing"

TMP=$(mktemp -d "${TMPDIR:-/tmp}/devfix-tunnel-tor-config.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT TERM

candidate() {
  transport="$1"
  awk -F '\t' -v wanted="$transport" '
    /^#/ {next}
    NF >= 3 && $1 == wanted {
      bridge=$3
      for (i=4; i<=NF; i++) bridge=bridge "\t" $i
      print bridge
      exit
    }
  ' "$CATALOG"
}

plugin_name() {
  case "$1" in
    snowflake) printf '%s' snowflake ;;
    meek) printf '%s' meek_lite ;;
    obfs4) printf '%s' obfs4 ;;
    *) return 1 ;;
  esac
}

verify_transport() {
  transport="$1"
  bridge=$(candidate "$transport")
  [ -n "$bridge" ] || fail "no $transport bridge candidate"
  plugin=$(plugin_name "$transport") || fail "unsupported test transport $transport"
  data="$TMP/data-$transport"
  torrc="$TMP/torrc-$transport"
  mkdir -p "$data"

  cat > "$torrc" <<EOF
DataDirectory "$data"
SocksPort 0
ClientOnly 1
AvoidDiskWrites 1
UseBridges 1
ClientTransportPlugin $plugin exec $LYREBIRD
Bridge $bridge
GeoIPFile "$GEOIP"
GeoIPv6File "$GEOIP6"
GeoIPExcludeUnknown 1
ExcludeExitNodes {ir},{??}
ExitNodes {de}
Log notice stdout
EOF

  if ! "$TOR" --verify-config -f "$torrc" > "$TMP/verify-$transport.log" 2>&1; then
    cat "$TMP/verify-$transport.log" >&2
    fail "real Tor rejected $transport V5 torrc"
  fi
  grep -q 'Configuration was valid' "$TMP/verify-$transport.log" || {
    cat "$TMP/verify-$transport.log" >&2
    fail "Tor did not confirm valid $transport configuration"
  }
  pass "real Tor accepts $transport + GeoIP foreign-exit configuration"
}

verify_transport snowflake
verify_transport meek
verify_transport obfs4

echo "ALL DEVFIX TUNNEL REAL TOR CONFIG TESTS PASSED"
