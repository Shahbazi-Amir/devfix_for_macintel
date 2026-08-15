from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    s = p.read_text()
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{path}: expected one match, found {n}: {old[:100]!r}")
    p.write_text(s.replace(old, new, 1))


Path("VERSION").write_text("2.0.3\n")
replace_once("bin/devfix", 'DEVFIX_VERSION="2.0.2"', 'DEVFIX_VERSION="2.0.3"')

replace_once(
    "bin/devfix",
    '''  q_data=$(torrc_quote "$DEVFIX_TOR_DATA_DIR")\n  q_pt=$(torrc_quote "$DEVFIX_LYREBIRD_BIN")\n  cat > "$DEVFIX_TORRC" <<EOF_TORRC\nDataDirectory $q_data\nSocksPort 127.0.0.1:$port\nClientOnly 1\nAvoidDiskWrites 1\nUseBridges 1\nClientTransportPlugin snowflake exec $q_pt\nBridge $SNOWFLAKE_BRIDGE\nLog notice stdout\nEOF_TORRC''',
    '''  q_data=$(torrc_quote "$DEVFIX_TOR_DATA_DIR")\n  case "$DEVFIX_LYREBIRD_BIN" in\n    *' '*|*$'\\t'*|*$'\\n'*|*$'\\r'*) die "lyrebird executable path contains whitespace; install DevFix under /usr/local" ;;\n  esac\n  cat > "$DEVFIX_TORRC" <<EOF_TORRC\nDataDirectory $q_data\nSocksPort 127.0.0.1:$port\nClientOnly 1\nAvoidDiskWrites 1\nUseBridges 1\nClientTransportPlugin snowflake exec $DEVFIX_LYREBIRD_BIN\nBridge $SNOWFLAKE_BRIDGE\nLog notice stdout\nEOF_TORRC'''
)

replace_once(
    "bin/devfix",
    '''    latest_progress=$(grep 'Bootstrapped [0-9][0-9]*%' "$DEVFIX_TOR_LOG" 2>/dev/null | tail -n 1)\n    if [ -n "$latest_progress" ] && [ "$latest_progress" != "$last_progress" ]; then''',
    '''    pt_failures=$(grep -c 'Managed proxy .*terminated with status code [1-9]' "$DEVFIX_TOR_LOG" 2>/dev/null || true)\n    case "$pt_failures" in ''|*[!0-9]*) pt_failures=0 ;; esac\n    if [ "$pt_failures" -ge 5 ]; then\n      stop_tor_pid "$pid"\n      clear_state\n      tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true\n      warn "PLUGGABLE_TRANSPORT_FAILURE: lyrebird repeatedly exited before Snowflake could bootstrap."\n      return 1\n    fi\n\n    latest_progress=$(grep 'Bootstrapped [0-9][0-9]*%' "$DEVFIX_TOR_LOG" 2>/dev/null | tail -n 1)\n    if [ -n "$latest_progress" ] && [ "$latest_progress" != "$last_progress" ]; then'''
)

replace_once(
    "tests/test_devfix.sh",
    '''if grep -Fq 'Log notice stdout' "$DEVFIX_STATE_DIR/run/torrc"; then pass "tor logs to stdout"; else fail "tor logs to stdout"; fi\nif grep -Fq 'Log notice file' "$DEVFIX_STATE_DIR/run/torrc"; then fail "tor avoids direct log file"; else pass "tor avoids direct log file"; fi\nout=$("$DEVFIX" status)''',
    '''if grep -Fq 'Log notice stdout' "$DEVFIX_STATE_DIR/run/torrc"; then pass "tor logs to stdout"; else fail "tor logs to stdout"; fi\nif grep -Fq 'Log notice file' "$DEVFIX_STATE_DIR/run/torrc"; then fail "tor avoids direct log file"; else pass "tor avoids direct log file"; fi\nexpected_pt="ClientTransportPlugin snowflake exec $DEVFIX_LYREBIRD_BIN"\nif grep -Fxq "$expected_pt" "$DEVFIX_STATE_DIR/run/torrc"; then pass "lyrebird path is unquoted for Tor managed transport"; else fail "lyrebird path is unquoted for Tor managed transport"; fi\nif grep -Fq 'ClientTransportPlugin snowflake exec "' "$DEVFIX_STATE_DIR/run/torrc"; then fail "lyrebird path has no literal quote wrapper"; else pass "lyrebird path has no literal quote wrapper"; fi\nout=$("$DEVFIX" status)'''
)

replace_once(
    "tests/test_devfix.sh",
    '''"$DEVFIX" disconnect >/dev/null\n\n# Auto mode falls back to Snowflake when direct is blocked.''',
    '''"$DEVFIX" disconnect >/dev/null\n\n# Repeated managed-transport crashes should fail fast with a specific diagnosis.\ncat > "$TMP/libexec/tor/tor" <<'SH'\n#!/bin/bash\ni=0\nwhile [ "$i" -lt 5 ]; do\n  echo 'Managed proxy "/tmp/lyrebird" having PID 123 terminated with status code 1'\n  i=$((i + 1))\ndone\nsleep 30\nSH\nchmod +x "$TMP/libexec/tor/tor"\nunset DEVFIX_TEST_MODE\nexport DEVFIX_BOOTSTRAP_TIMEOUT=30\nexport DEVFIX_BOOTSTRAP_STALL_TIMEOUT=30\nset +e\npt_err=$("$DEVFIX" connect snowflake 2>&1 >/dev/null)\npt_rc=$?\nset -e\nif [ "$pt_rc" -ne 0 ]; then pass "managed transport crash returns failure"; else fail "managed transport crash returns failure"; fi\nassert_contains "managed transport crash classified" "PLUGGABLE_TRANSPORT_FAILURE" "$pt_err"\ncat > "$TMP/libexec/tor/tor" <<'SH'\n#!/bin/bash\nexec sleep 300\nSH\nchmod +x "$TMP/libexec/tor/tor"\nexport DEVFIX_TEST_MODE=1\nunset DEVFIX_BOOTSTRAP_TIMEOUT DEVFIX_BOOTSTRAP_STALL_TIMEOUT\n\n# Auto mode falls back to Snowflake when direct is blocked.'''
)

p = Path("CHANGELOG.md")
s = p.read_text()
header = "# Changelog\n\n"
if not s.startswith(header):
    raise SystemExit("CHANGELOG.md: unexpected header")
entry = '''## 2.0.3 - 2026-08-15\n\n- Fixed Tor managed-transport launch on Intel Monterey by removing a literal quote wrapper around the bundled lyrebird executable path.\n- Added regression coverage for the exact `ClientTransportPlugin snowflake exec /usr/local/.../lyrebird` torrc form used by Tor Project documentation.\n- Added fast failure classification when lyrebird repeatedly exits before Snowflake bootstrap, avoiding a long generic stall timeout for launch/configuration failures.\n\n'''
p.write_text(header + entry + s[len(header):])
replace_once("man/devfix.1", '"DevFix 2.0.2"', '"DevFix 2.0.3"')

Path(".github/bootstrap/devfix_203_patch.py").unlink()
Path(".github/workflows/devfix-203-fix.yml").unlink()
