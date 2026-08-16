from pathlib import Path


def must_replace(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)

cli = Path('tunnel/cli/devfix-tunnel')
s = cli.read_text()
for old, new, label in [
    ('TUNNEL_VERSION="0.3.0-rc2"', 'TUNNEL_VERSION="0.3.0-rc3"', 'version'),
    ('BOOTSTRAP_TIMEOUT="${DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT:-420}"', 'BOOTSTRAP_TIMEOUT="${DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT:-1200}"', 'bootstrap timeout'),
    ('STALL_TIMEOUT_CONSENSUS="${DEVFIX_TUNNEL_STALL_TIMEOUT_CONSENSUS:-240}"', 'STALL_TIMEOUT_CONSENSUS="${DEVFIX_TUNNEL_STALL_TIMEOUT_CONSENSUS:-240}"\nSTALL_TIMEOUT_DIRINFO="${DEVFIX_TUNNEL_STALL_TIMEOUT_DIRINFO:-900}"', 'dirinfo timeout'),
]:
    s = must_replace(s, old, new, label)

s = must_replace(s,
'''clear_runtime_state() {
  data_dir=$(state_get DATA_DIR '')
  rm -f "$TUNNEL_STATE_FILE" "$TUNNEL_PID_FILE" "$TUNNEL_TORRC"
  rm -f "$TUNNEL_STOP_REQUEST" "$TUNNEL_PROXY_READY" "$TUNNEL_PROXY_FAILED" "$TUNNEL_PROXY_RESTORED"
  safe_remove_data_dir "$data_dir" 2>/dev/null || true
}''',
'''clear_runtime_state() {
  data_dir=$(state_get DATA_DIR '')
  session=$(state_get SESSION '')
  cache_dir=""
  if [ -n "$session" ]; then cache_dir="$TUNNEL_TOR_DATA_BASE/$session-cache"; fi
  rm -f "$TUNNEL_STATE_FILE" "$TUNNEL_PID_FILE" "$TUNNEL_TORRC"
  rm -f "$TUNNEL_STOP_REQUEST" "$TUNNEL_PROXY_READY" "$TUNNEL_PROXY_FAILED" "$TUNNEL_PROXY_RESTORED"
  safe_remove_data_dir "$data_dir" 2>/dev/null || true
  safe_remove_data_dir "$cache_dir" 2>/dev/null || true
}''', 'clear cache')

s = must_replace(s,
'''write_torrc() {
  port="$1"; data_dir="$2"; transport="$3"; bridge="$4"; exit_policy="$5"; exit_country="$6"
  ensure_dirs
  q_data=$(torrc_quote "$data_dir")''',
'''write_torrc() {
  port="$1"; data_dir="$2"; cache_dir="$3"; transport="$4"; bridge="$5"; exit_policy="$6"; exit_country="$7"
  ensure_dirs
  q_data=$(torrc_quote "$data_dir")
  q_cache=$(torrc_quote "$cache_dir")''', 'write_torrc signature')

s = must_replace(s, 'DataDirectory $q_data\nSocksPort', 'DataDirectory $q_data\nCacheDirectory $q_cache\nSocksPort', 'cache directory torrc')

s = must_replace(s,
'''  elif [ "$percent" -ge 25 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_CONSENSUS"''',
'''  elif [ "$percent" -ge 40 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_DIRINFO"
  elif [ "$percent" -ge 25 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_CONSENSUS"''', 'phase 50 timeout')

s = must_replace(s,
'''  mode="$1"; requested_transport="$2"; transport="$3"; candidate="$4"; bridge="$5"; port="$6"; session="$7"; started="$8"; exit_policy="$9"; exit_country="${10}"; attempt_no="${11}"
  data_dir="$TUNNEL_TOR_DATA_BASE/$session-attempt-$attempt_no-$transport-$candidate"''',
'''  mode="$1"; requested_transport="$2"; transport="$3"; candidate="$4"; bridge="$5"; port="$6"; session="$7"; started="$8"; exit_policy="$9"; exit_country="${10}"; attempt_no="${11}"; cache_dir="${12}"
  data_dir="$TUNNEL_TOR_DATA_BASE/$session-attempt-$attempt_no-$transport-$candidate"''', 'attempt signature')

s = must_replace(s, 'write_torrc "$port" "$data_dir" "$transport" "$bridge" "$exit_policy" "$exit_country"', 'write_torrc "$port" "$data_dir" "$cache_dir" "$transport" "$bridge" "$exit_policy" "$exit_country"', 'attempt torrc')

s = must_replace(s,
'''  attempt_no=0
  found=0

  while IFS=$'\\t' read -r transport candidate bridge; do''',
'''  attempt_no=0
  found=0
  session_cache_dir="$TUNNEL_TOR_DATA_BASE/$session-cache"
  safe_remove_data_dir "$session_cache_dir" 2>/dev/null || true
  mkdir -p "$session_cache_dir" || die "cannot create session Tor cache directory"
  chmod 700 "$session_cache_dir" 2>/dev/null || true

  while IFS=$'\\t' read -r transport candidate bridge; do''', 'session cache create')

s = must_replace(s,
'''    if run_transport_attempt "$requested_mode" "$requested_transport" "$transport" "$candidate" "$bridge" "$port" "$session" "$started" "$exit_policy" "$exit_country" "$attempt_no"; then''',
'''    if run_transport_attempt "$requested_mode" "$requested_transport" "$transport" "$candidate" "$bridge" "$port" "$session" "$started" "$exit_policy" "$exit_country" "$attempt_no" "$session_cache_dir"; then''', 'pass cache')

s = must_replace(s,
'''  err "ALL_TRANSPORTS_FAILED: no validated Tor route was established. System Proxy was not enabled."
  return 1''',
'''  safe_remove_data_dir "$session_cache_dir" 2>/dev/null || true
  err "ALL_TRANSPORTS_FAILED: no validated Tor route was established. System Proxy was not enabled."
  return 1''', 'final cache cleanup')

cli.write_text(s)
Path('tunnel/VERSION').write_text('0.3.0-rc3\n')

for p in ['tests/test_devfix_tunnel.sh','tests/test_devfix_tunnel_chrome.sh']:
    path=Path(p); path.write_text(path.read_text().replace('0.3.0-rc2','0.3.0-rc3'))

readme=Path('tunnel/README.md')
r=readme.read_text().replace('0.3.0-rc2','0.3.0-rc3')
r += '''\n\n## RC3 directory-progress remediation\n\nPhysical RC2 reached bootstrap 50% on multiple obfs4 bridges and had already learned a usable consensus with exit nodes, but the controller killed the route after 240 seconds without a percentage change. Tor documents phase 50 as the bulk descriptor-loading phase, especially on slow links. RC3 therefore keeps attempt-specific DataDirectory isolation while sharing a session-scoped CacheDirectory across sequential transport candidates, raises the overall bootstrap ceiling to 1200 seconds, and gives phases >=40 a 900-second no-progress window. Early 0/10% failures remain bounded by the shorter existing limits. System Proxy activation remains gated on 100% bootstrap plus routed HTTPS validation.\n'''
readme.write_text(r)

rem=Path('docs/tunnel/remediations'); rem.mkdir(parents=True,exist_ok=True)
(rem/'015_REAL_MAC_DESCRIPTOR_CACHE_RESET.md').write_text('''# 015 — REAL_MAC_DESCRIPTOR_CACHE_RESET\n\nPhysical RC2 reached 50% on later obfs4 candidates, but each fallback used a fresh DataDirectory, discarding consensus/microdescriptor cache from the previous candidate. RC3 introduces a session-scoped Tor CacheDirectory shared only across sequential candidates while retaining separate attempt DataDirectories.\n''')
(rem/'016_REAL_MAC_PHASE50_TIMEOUT.md').write_text('''# 016 — REAL_MAC_PHASE50_TIMEOUT\n\nPhysical RC2 reached `loading_descriptors` (50%) and learned that the current consensus contained exit nodes, but the controller terminated the candidate after 240 seconds with no percentage change. Tor documents phase 50 as the bulk of bootstrap on slow links. RC3 uses a 900-second no-progress limit from phase 40 onward and a 1200-second total attempt ceiling, while keeping shorter limits at early phases.\n''')

# Dedicated static regression assertions.
t=Path('tests/test_devfix_tunnel_rc3.sh')
t.write_text('''#!/bin/bash\nset -euo pipefail\nROOT=$(cd "$(dirname "$0")/.." && pwd)\nT="$ROOT/tunnel/cli/devfix-tunnel"\nfail(){ echo "FAIL: $*" >&2; exit 1; }\ngrep -Fq 'TUNNEL_VERSION="0.3.0-rc3"' "$T" || fail version\ngrep -Fq 'BOOTSTRAP_TIMEOUT="${DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT:-1200}"' "$T" || fail bootstrap\ngrep -Fq 'STALL_TIMEOUT_DIRINFO="${DEVFIX_TUNNEL_STALL_TIMEOUT_DIRINFO:-900}"' "$T" || fail dirinfo\ngrep -Fq 'CacheDirectory $q_cache' "$T" || fail cache-torrc\ngrep -Fq 'session_cache_dir="$TUNNEL_TOR_DATA_BASE/$session-cache"' "$T" || fail session-cache\ngrep -Fq 'run_transport_attempt "$requested_mode" "$requested_transport" "$transport" "$candidate" "$bridge" "$port" "$session" "$started" "$exit_policy" "$exit_country" "$attempt_no" "$session_cache_dir"' "$T" || fail cache-forward\necho 'ALL DEVFIX TUNNEL RC3 REGRESSIONS PASSED'\n''')
