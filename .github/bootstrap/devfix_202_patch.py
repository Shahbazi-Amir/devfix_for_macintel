from pathlib import Path
import re


def replace_once(path, old, new):
    p = Path(path)
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one literal match, got {count}: {old[:80]!r}")
    p.write_text(s.replace(old, new, 1))


def sub_once(path, pattern, repl, flags=0):
    p = Path(path)
    s = p.read_text()
    ns, n = re.subn(pattern, repl, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"{path}: expected exactly one regex match, got {n}: {pattern[:120]!r}")
    p.write_text(ns)


Path("VERSION").write_text("2.0.2\n")
replace_once("bin/devfix", 'DEVFIX_VERSION="2.0.1"', 'DEVFIX_VERSION="2.0.2"')
replace_once(
    "bin/devfix",
    'DEVFIX_BOOTSTRAP_TIMEOUT="${DEVFIX_BOOTSTRAP_TIMEOUT:-75}"\nDEVFIX_TEST_MODE="${DEVFIX_TEST_MODE:-0}"',
    'DEVFIX_BOOTSTRAP_TIMEOUT="${DEVFIX_BOOTSTRAP_TIMEOUT:-600}"\nDEVFIX_BOOTSTRAP_STALL_TIMEOUT="${DEVFIX_BOOTSTRAP_STALL_TIMEOUT:-180}"\nDEVFIX_TEST_MODE="${DEVFIX_TEST_MODE:-0}"',
)

replace_once(
    "bin/devfix",
    '''snowflake_available() {
  [ -x "$DEVFIX_TOR_BIN" ] && [ -x "$DEVFIX_LYREBIRD_BIN" ]
}
''',
    '''snowflake_available() {
  [ -x "$DEVFIX_TOR_BIN" ] && [ -x "$DEVFIX_LYREBIRD_BIN" ]
}

snowflake_payload_state() {
  if snowflake_available; then
    printf 'available'
  elif [ -d "$DEVFIX_LIBEXEC_DIR/tor" ] && [ ! -x "$DEVFIX_LIBEXEC_DIR/tor" ]; then
    printf 'inaccessible'
  elif [ -d "$DEVFIX_LIBEXEC_DIR/tor" ]; then
    printf 'incomplete'
  else
    printf 'missing'
  fi
}
''',
)

replace_once(
    "bin/devfix",
    '  q_log=$(torrc_quote "$DEVFIX_TOR_LOG")\n  q_pt=$(torrc_quote "$DEVFIX_LYREBIRD_BIN")',
    '  q_pt=$(torrc_quote "$DEVFIX_LYREBIRD_BIN")',
)
replace_once("bin/devfix", "Log notice file $q_log", "Log notice stdout")

old_loop = r'''  elapsed=0
  while \[ "\$elapsed" -lt "\$DEVFIX_BOOTSTRAP_TIMEOUT" \]; do
.*?  warn "TRANSPORT_FAILURE: Snowflake could not establish a working route\."
  return 1'''
new_loop = '''  elapsed=0
  last_progress=""
  last_progress_at=0
  while [ "$elapsed" -lt "$DEVFIX_BOOTSTRAP_TIMEOUT" ]; do
    if ! is_pid_alive "$pid"; then
      tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
      clear_state
      warn "TRANSPORT_FAILURE: Snowflake/Tor exited before bootstrap completed."
      return 1
    fi

    latest_progress=$(grep 'Bootstrapped [0-9][0-9]*%' "$DEVFIX_TOR_LOG" 2>/dev/null | tail -n 1)
    if [ -n "$latest_progress" ] && [ "$latest_progress" != "$last_progress" ]; then
      progress_text=$(printf '%s\\n' "$latest_progress" | sed 's/^.*Bootstrapped /Bootstrapped /')
      info "Snowflake: $progress_text"
      last_progress="$latest_progress"
      last_progress_at="$elapsed"
    elif [ "$elapsed" -gt 0 ] && [ $((elapsed % 30)) -eq 0 ]; then
      info "Snowflake bootstrap still in progress (${elapsed}s/${DEVFIX_BOOTSTRAP_TIMEOUT}s)..."
    fi

    if grep -q 'Bootstrapped 100%' "$DEVFIX_TOR_LOG" 2>/dev/null && port_in_use "$port"; then
      if probe_critical_quiet snowflake; then
        ok "Connected with built-in Snowflake."
        log_line "transport=snowflake action=connected"
        return 0
      fi
    fi

    if [ -n "$last_progress" ] && [ $((elapsed - last_progress_at)) -ge "$DEVFIX_BOOTSTRAP_STALL_TIMEOUT" ]; then
      progress_text=$(printf '%s\\n' "$last_progress" | sed 's/^.*Bootstrapped /Bootstrapped /')
      stop_tor_pid "$pid"
      clear_state
      tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
      warn "TRANSPORT_FAILURE: Snowflake stalled at $progress_text for ${DEVFIX_BOOTSTRAP_STALL_TIMEOUT}s."
      return 1
    fi

    sleep 1
    elapsed=$((elapsed + 1))
  done

  if [ -n "$last_progress" ]; then
    progress_text=$(printf '%s\\n' "$last_progress" | sed 's/^.*Bootstrapped /Bootstrapped /')
  else
    progress_text="no bootstrap progress reported"
  fi
  stop_tor_pid "$pid"
  clear_state
  tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
  warn "TRANSPORT_FAILURE: Snowflake bootstrap timed out after ${DEVFIX_BOOTSTRAP_TIMEOUT}s at $progress_text."
  return 1'''
sub_once("bin/devfix", old_loop, new_loop, flags=re.S)

replace_once(
    "bin/devfix",
    '''      if snowflake_available; then
        printf 'snowflake       built-in   available\\n'
      else
        printf 'snowflake       built-in   not installed\\n'
      fi''',
    '''      payload_state=$(snowflake_payload_state)
      case "$payload_state" in
        available) printf 'snowflake       built-in   available\\n' ;;
        inaccessible) printf 'snowflake       built-in   inaccessible (permissions)\\n' ;;
        incomplete) printf 'snowflake       built-in   incomplete payload\\n' ;;
        *) printf 'snowflake       built-in   not installed\\n' ;;
      esac''',
)

replace_once(
    "bin/devfix",
    '''  if snowflake_available; then
    printf '  %-20s %s\\n' snowflake available
  else
    printf '  %-20s %s\\n' snowflake 'NOT INSTALLED'
  fi''',
    '''  payload_state=$(snowflake_payload_state)
  case "$payload_state" in
    available) printf '  %-20s %s\\n' snowflake available ;;
    inaccessible) printf '  %-20s %s\\n' snowflake 'INACCESSIBLE (permissions)' ;;
    incomplete) printf '  %-20s %s\\n' snowflake 'INCOMPLETE PAYLOAD' ;;
    *) printf '  %-20s %s\\n' snowflake 'NOT INSTALLED' ;;
  esac''',
)

replace_once(
    "bin/devfix",
    '''  elif snowflake_available; then
    printf 'Primary issue: NETWORK_BLOCKED_OR_UNREACHABLE\\n'
    printf 'Recommendation: run devfix connect; auto mode will try built-in Snowflake.\\n'
  else
    printf 'Primary issue: NETWORK_BLOCKED_OR_UNREACHABLE\\n'
    printf 'Recommendation: reinstall the self-contained DevFix package; Snowflake payload is missing.\\n'
  fi''',
    '''  elif snowflake_available; then
    printf 'Primary issue: PARTIAL_DEVELOPER_NETWORK\\n'
    printf 'Recommendation: run devfix connect; auto mode will try built-in Snowflake for required endpoints.\\n'
  elif [ "$(snowflake_payload_state)" = "inaccessible" ]; then
    printf 'Primary issue: SNOWFLAKE_PAYLOAD_PERMISSIONS\\n'
    printf 'Recommendation: install the latest DevFix package; its upgrade repair fixes legacy payload permissions.\\n'
  else
    printf 'Primary issue: NETWORK_BLOCKED_OR_UNREACHABLE\\n'
    printf 'Recommendation: reinstall the self-contained DevFix package; Snowflake payload is missing or incomplete.\\n'
  fi''',
)

replace_once(
    "bin/devfix",
    "DevFix 2.0.0 - built-in developer-network routing for Intel macOS",
    "DevFix - built-in developer-network routing for Intel macOS",
)

replace_once(
    "install.sh",
    'as_root cp -R "$TOR_SOURCE" "$TARGET/libexec/devfix/tor"\nas_root cp "$ROOT/share/man/man1/devfix.1"',
    'as_root cp -R "$TOR_SOURCE" "$TARGET/libexec/devfix/tor"\nas_root chmod -R a+rX "$TARGET/libexec/devfix/tor"\nas_root cp "$ROOT/share/man/man1/devfix.1"',
)

replace_once(
    "scripts/fetch-tor-bundle.sh",
    'cp -R "$source_dir" "$DEST"\nchmod +x "$DEST/tor" "$DEST/pluggable_transports/lyrebird"',
    'cp -R "$source_dir" "$DEST"\nchmod -R a+rX "$DEST"\nchmod +x "$DEST/tor" "$DEST/pluggable_transports/lyrebird"',
)

replace_once(
    "scripts/build-pkg.sh",
    'cp -R "$VENDOR" "$PKGROOT/usr/local/libexec/devfix/tor"\ncp "$ROOT/man/devfix.1"',
    'cp -R "$VENDOR" "$PKGROOT/usr/local/libexec/devfix/tor"\nchmod -R a+rX "$PKGROOT/usr/local/libexec/devfix/tor"\ncp "$ROOT/man/devfix.1"',
)
replace_once(
    "scripts/build-pkg.sh",
    'chmod 755 "$DEVFIX" "$TOR" "$LYREBIRD"',
    'chmod -R a+rX /usr/local/libexec/devfix/tor\nchmod 755 "$DEVFIX" "$TOR" "$LYREBIRD"',
)
replace_once("scripts/build-pkg.sh", "--ownership preserve", "--ownership recommended")

replace_once(
    "tests/test_devfix.sh",
    '''assert_contains "snowflake available" "available" "$out"

out=$("$DEVFIX" proxy status)''',
    '''assert_contains "snowflake available" "available" "$out"

chmod 600 "$TMP/libexec/tor"
out=$("$DEVFIX" transport list)
assert_contains "snowflake permission diagnosis" "inaccessible (permissions)" "$out"
chmod 755 "$TMP/libexec/tor"

out=$("$DEVFIX" proxy status)''',
)

replace_once(
    "tests/test_devfix.sh",
    '''"$DEVFIX" connect snowflake >/dev/null
out=$("$DEVFIX" status)
assert_contains "snowflake connected" "Transport: snowflake" "$out"''',
    '''"$DEVFIX" connect snowflake >/dev/null
if grep -Fq 'Log notice stdout' "$DEVFIX_STATE_DIR/run/torrc"; then pass "tor logs to stdout"; else fail "tor logs to stdout"; fi
if grep -Fq 'Log notice file' "$DEVFIX_STATE_DIR/run/torrc"; then fail "tor avoids direct log file"; else pass "tor avoids direct log file"; fi
out=$("$DEVFIX" status)
assert_contains "snowflake connected" "Transport: snowflake" "$out"''',
)

replace_once(
    ".github/workflows/package.yml",
    '''          sudo /usr/local/share/devfix/uninstall.sh
      - name: Portable artifact smoke test''',
    '''          sudo /usr/local/share/devfix/uninstall.sh
      - name: Upgrade repairs legacy payload permissions
        run: |
          set -euo pipefail
          version=$(cat VERSION)
          pkg="dist/DevFix-${version}-macos-x86_64.pkg"
          sudo rm -rf /usr/local/libexec/devfix /usr/local/share/devfix
          sudo rm -f /usr/local/bin/devfix /usr/local/share/man/man1/devfix.1
          sudo mkdir -p /usr/local/libexec/devfix/tor/pluggable_transports
          sudo touch /usr/local/libexec/devfix/tor/legacy-marker
          sudo chmod 700 /usr/local/libexec/devfix/tor
          sudo chmod 700 /usr/local/libexec/devfix/tor/pluggable_transports
          sudo installer -pkg "$pkg" -target /
          test -x /usr/local/bin/devfix
          test -x /usr/local/libexec/devfix/tor/tor
          test -x /usr/local/libexec/devfix/tor/pluggable_transports/lyrebird
          test "$(stat -f '%Lp' /usr/local/libexec/devfix/tor)" = "755"
          /usr/local/bin/devfix transport list | grep -E 'snowflake.*available'
          sudo /usr/local/share/devfix/uninstall.sh
      - name: Portable artifact smoke test''',
)

p = Path("CHANGELOG.md")
s = p.read_text()
entry = '''# Changelog

## 2.0.2 - 2026-08-15

- Fixed upgrades that could leave the bundled Tor directory root-only and make Snowflake look uninstalled.
- Normalized Tor payload permissions in source fetch, tar installation, package build, and package postinstall repair.
- Changed Tor notice logging to stdout with DevFix owning the log redirection, avoiding Monterey log-file initialization failures.
- Added progress-aware Snowflake bootstrap with a 10-minute hard limit and a 3-minute no-progress stall limit.
- Improved diagnostics for inaccessible versus missing Snowflake payloads and partial developer-network reachability.
- Added a package-upgrade regression test that reproduces the legacy root-owned mode-700 directory.

'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("CHANGELOG.md: unexpected header")
p.write_text(entry + s[len("# Changelog\n\n"):])

replace_once("man/devfix.1", '"DevFix 2.0.0"', '"DevFix 2.0.2"')

for helper in (
    Path(".github/workflows/devfix-202-reliability-fix.yml"),
    Path(".github/bootstrap/devfix_202_patch.py"),
):
    if helper.exists():
        helper.unlink()
