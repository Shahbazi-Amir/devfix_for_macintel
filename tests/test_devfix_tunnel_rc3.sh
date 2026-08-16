#!/bin/bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
T="$ROOT/tunnel/cli/devfix-tunnel"
fail(){ printf 'FAIL: %s\n' "$*" >&2; exit 1; }

literal_bootstrap='BOOTSTRAP_TIMEOUT="${DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT:-1200}"'
literal_descriptor='STALL_TIMEOUT_DESCRIPTORS="${DEVFIX_TUNNEL_STALL_TIMEOUT_DESCRIPTORS:-900}"'
literal_cache='CacheDirectory $q_cache'
literal_cache_root='TUNNEL_TOR_CACHE_DIR="${DEVFIX_TUNNEL_CACHE_DIR:-$TUNNEL_STATE_ROOT/tor-cache}"'

grep -Fq 'TUNNEL_VERSION="0.3.0-rc3"' "$T" || fail version
grep -Fq "$literal_bootstrap" "$T" || fail bootstrap-timeout
grep -Fq "$literal_descriptor" "$T" || fail descriptor-timeout
grep -Fq "$literal_cache" "$T" || fail cache-torrc
grep -Fq "$literal_cache_root" "$T" || fail cache-root
grep -Fq 'AvoidDiskWrites 0' "$T" || fail cache-write-policy
grep -Fq 'DIRECTORY_INFO_STALL' "$T" || fail directory-stall-classifier

echo 'ALL DEVFIX TUNNEL RC3 REGRESSIONS PASSED'
