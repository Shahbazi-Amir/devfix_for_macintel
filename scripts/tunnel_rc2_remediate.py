from pathlib import Path


def must_replace(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


cli = Path("tunnel/cli/devfix-tunnel")
s = cli.read_text()
for old, new, label in [
    ('TUNNEL_VERSION="0.3.0-rc1"', 'TUNNEL_VERSION="0.3.0-rc2"', "cli version"),
    ('MAX_AUTO_ATTEMPTS="${DEVFIX_TUNNEL_MAX_AUTO_ATTEMPTS:-5}"', 'MAX_AUTO_ATTEMPTS="${DEVFIX_TUNNEL_MAX_AUTO_ATTEMPTS:-0}"', "auto attempt default"),
    ('GeoIPExcludeUnknown 1\nExcludeExitNodes {ir},{??}', 'GeoIPExcludeUnknown 0\nExcludeExitNodes {ir},{??}', "foreign-only policy"),
    ('if [ "$requested_transport" = "auto" ] && [ "$attempt_no" -gt "$MAX_AUTO_ATTEMPTS" ]; then break; fi',
     'if [ "$requested_transport" = "auto" ] && [ "$MAX_AUTO_ATTEMPTS" -gt 0 ] && [ "$attempt_no" -gt "$MAX_AUTO_ATTEMPTS" ]; then break; fi',
     "auto attempt guard"),
]:
    s = must_replace(s, old, new, label)

s = must_replace(
    s,
    'STALL_TIMEOUT="${DEVFIX_TUNNEL_STALL_TIMEOUT:-90}"\nVALIDATION_TIMEOUT="${DEVFIX_TUNNEL_VALIDATION_TIMEOUT:-30}"',
    'STALL_TIMEOUT_OVERRIDE="${DEVFIX_TUNNEL_STALL_TIMEOUT:-}"\n'
    'STALL_TIMEOUT="${DEVFIX_TUNNEL_STALL_TIMEOUT:-90}"\n'
    'STALL_TIMEOUT_HANDSHAKE="${DEVFIX_TUNNEL_STALL_TIMEOUT_HANDSHAKE:-150}"\n'
    'STALL_TIMEOUT_CONSENSUS="${DEVFIX_TUNNEL_STALL_TIMEOUT_CONSENSUS:-240}"\n'
    'VALIDATION_TIMEOUT="${DEVFIX_TUNNEL_VALIDATION_TIMEOUT:-30}"',
    "stall constants",
)

s = must_replace(
    s,
    'TOR_CHECK_URL="${DEVFIX_TUNNEL_TOR_CHECK_URL:-https://check.torproject.org/api/ip}"\n\ninfo()',
    'TOR_CHECK_URL="${DEVFIX_TUNNEL_TOR_CHECK_URL:-https://check.torproject.org/api/ip}"\n\n'
    'case "$MAX_AUTO_ATTEMPTS" in \'\'|*[!0-9]*) MAX_AUTO_ATTEMPTS=0 ;; esac\n\n'
    'info()',
    "auto attempt normalization",
)

old = '''bootstrap_percent_from_log() {
  file="$1"
  [ -f "$file" ] || { printf '0'; return; }
  value=$(sed -nE 's/.*Bootstrapped ([0-9]+)%.*/\\1/p' "$file" | tail -n 1)
  case "$value" in ''|*[!0-9]*) printf '0' ;; *) printf '%s' "$value" ;; esac
}

classify_attempt_failure() {'''
new = '''bootstrap_percent_from_log() {
  file="$1"
  [ -f "$file" ] || { printf '0'; return; }
  value=$(sed -nE 's/.*Bootstrapped ([0-9]+)%.*/\\1/p' "$file" | tail -n 1)
  case "$value" in ''|*[!0-9]*) printf '0' ;; *) printf '%s' "$value" ;; esac
}

stall_timeout_for_percent() {
  percent="$1"
  if [ -n "$STALL_TIMEOUT_OVERRIDE" ]; then
    printf '%s' "$STALL_TIMEOUT"
  elif [ "$percent" -ge 25 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_CONSENSUS"
  elif [ "$percent" -ge 10 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_HANDSHAKE"
  else
    printf '%s' "$STALL_TIMEOUT"
  fi
}

classify_attempt_failure() {'''
s = must_replace(s, old, new, "stall helper")

old = '''  if [ "$transport" = "snowflake" ] && grep -q 'timeout waiting for DataChannel.OnOpen' "$file" 2>/dev/null; then
    printf 'SNOWFLAKE_WEBRTC_DATACHANNEL_FAILURE'
  elif [ "$transport" = "snowflake" ] && grep -q 'broker failure' "$file" 2>/dev/null; then'''
new = '''  if grep -q 'Not using bridge at .*it is in ExcludeNodes' "$file" 2>/dev/null; then
    printf 'BRIDGE_EXCLUDED_BY_NODE_POLICY'
  elif [ "$transport" = "snowflake" ] && grep -q 'timeout waiting for DataChannel.OnOpen' "$file" 2>/dev/null; then
    printf 'SNOWFLAKE_WEBRTC_DATACHANNEL_FAILURE'
  elif [ "$transport" = "snowflake" ] && grep -q 'broker failure' "$file" 2>/dev/null; then'''
s = must_replace(s, old, new, "failure classifier")

old = '''    if [ $(( $(now_epoch) - last_progress_epoch )) -ge "$STALL_TIMEOUT" ]; then
      classification=$(classify_attempt_failure "$transport" "$attempt_log" BOOTSTRAP_STALL)
      stop_owned_tor "$pid" || true
      write_state FAILED SOCKS "$pid" "$port" "$session" "$started" '' "$transport" "$candidate" "$requested_transport" "$exit_policy" "$exit_country" "$data_dir" "$attempt_log"
      warn "$classification: $transport candidate $candidate stalled at ${percent}% for ${STALL_TIMEOUT}s."
      safe_remove_data_dir "$data_dir" 2>/dev/null || true
      return 1
    fi'''
new = '''    stall_limit=$(stall_timeout_for_percent "$percent")
    if [ $(( $(now_epoch) - last_progress_epoch )) -ge "$stall_limit" ]; then
      classification=$(classify_attempt_failure "$transport" "$attempt_log" BOOTSTRAP_STALL)
      stop_owned_tor "$pid" || true
      write_state FAILED SOCKS "$pid" "$port" "$session" "$started" '' "$transport" "$candidate" "$requested_transport" "$exit_policy" "$exit_country" "$data_dir" "$attempt_log"
      warn "$classification: $transport candidate $candidate stalled at ${percent}% for ${stall_limit}s."
      safe_remove_data_dir "$data_dir" 2>/dev/null || true
      return 1
    fi'''
s = must_replace(s, old, new, "stall loop")
cli.write_text(s)

Path("tunnel/VERSION").write_text("0.3.0-rc2\n")

for path in [
    Path("tests/test_devfix_tunnel.sh"),
    Path("tests/test_devfix_tunnel_chrome.sh"),
    Path(".github/workflows/tunnel-package.yml"),
]:
    path.write_text(path.read_text().replace("0.3.0-rc1", "0.3.0-rc2"))

tor_test = Path("tests/test_devfix_tunnel_tor_config.sh")
s = tor_test.read_text()
if "GeoIPExcludeUnknown 1" not in s:
    raise SystemExit("real Tor config old unknown policy missing")
tor_test.write_text(s.replace("GeoIPExcludeUnknown 1", "GeoIPExcludeUnknown 0"))

readme = Path("tunnel/README.md")
s = readme.read_text().replace("0.3.0-rc1", "0.3.0-rc2")
anchor = "V5 removes that single-route dependency. The exact packaged Tor bundle is now the source of truth for the transport catalog.\n"
note = (
    "\nPhysical testing of `0.3.0-rc1` exposed a second resilience class: "
    "`GeoIPExcludeUnknown 1` could classify unknown-country entry bridges as excluded, "
    "the auto engine stopped after five candidates even when more obfs4 bridges existed, "
    "and a fixed 90-second no-progress cutoff was too aggressive for consensus loading. "
    "`0.3.0-rc2` separates exit-only country policy from entry-bridge eligibility, "
    "exhausts the packaged catalog by default, and uses phase-aware stall limits.\n"
)
if anchor not in s:
    raise SystemExit("README RC2 note anchor missing")
readme.write_text(s.replace(anchor, anchor + note, 1))

rem = Path("docs/tunnel/remediations")
rem.mkdir(parents=True, exist_ok=True)
(rem / "012_REAL_MAC_UNKNOWN_BRIDGE_EXCLUSION.md").write_text(
    "# 012 — REAL_MAC_UNKNOWN_BRIDGE_EXCLUSION\n\n"
    "Physical Monterey `0.3.0-rc1` logs repeatedly reported `Not using bridge ... it is in ExcludeNodes` for Snowflake and meek while foreign-only mode was enabled. "
    "Root cause: `GeoIPExcludeUnknown 1` makes unknown-country nodes excluded in both node and exit selection. "
    "Fix: use `GeoIPExcludeUnknown 0` and keep explicit `ExcludeExitNodes {ir},{??}` so unknown exits remain rejected without excluding entry bridges.\n"
)
(rem / "013_REAL_MAC_AUTO_CATALOG_TRUNCATION.md").write_text(
    "# 013 — REAL_MAC_AUTO_CATALOG_TRUNCATION\n\n"
    "Physical Monterey `0.3.0-rc1` showed auto mode stopped after five attempts: two Snowflake, one meek, and only two obfs4 candidates, despite seven packaged obfs4 candidates. "
    "Root cause: default `MAX_AUTO_ATTEMPTS=5`. Fix: default `0` means exhaust the finite packaged catalog; an explicit positive environment override may still bound attempts for tests/operators.\n"
)
(rem / "014_REAL_MAC_PHASE_AWARE_BOOTSTRAP_STALL.md").write_text(
    "# 014 — REAL_MAC_PHASE_AWARE_BOOTSTRAP_STALL\n\n"
    "Physical Monterey `0.3.0-rc1` reached Tor bootstrap 30% on obfs4 candidate 2 and was terminated after 90 seconds without a percentage change. "
    "Tor documents consensus loading as a phase that can take a while. Fix: retain a 90s initial stall limit, use 150s once relay-handshake progress reaches 10%, and 240s from consensus-request/loading progress (>=25%), while preserving the explicit `DEVFIX_TUNNEL_STALL_TIMEOUT` override for deterministic tests.\n"
)
