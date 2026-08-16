from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    s = p.read_text()
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{path}: expected one match, found {n}: {old[:120]!r}")
    p.write_text(s.replace(old, new, 1))


# Version metadata.
Path("VERSION").write_text("2.0.4\n")
replace_once("bin/devfix", 'DEVFIX_VERSION="2.0.3"', 'DEVFIX_VERSION="2.0.4"')
replace_once(
    "bin/devfix",
    'DEVFIX_BOOTSTRAP_STALL_TIMEOUT="${DEVFIX_BOOTSTRAP_STALL_TIMEOUT:-180}"\nDEVFIX_TEST_MODE="${DEVFIX_TEST_MODE:-0}"',
    'DEVFIX_BOOTSTRAP_STALL_TIMEOUT="${DEVFIX_BOOTSTRAP_STALL_TIMEOUT:-180}"\nDEVFIX_ROUTE_VALIDATION_TIMEOUT="${DEVFIX_ROUTE_VALIDATION_TIMEOUT:-30}"\nDEVFIX_TEST_MODE="${DEVFIX_TEST_MODE:-0}"'
)

# Registry connectivity probes must use the Docker Registry API base health endpoint.
# Repository roots are not health endpoints and can legitimately return 404.
replace_once(
    "bin/devfix",
    "    'https://ghcr.io/v2/homebrew/core/'; do",
    "    'https://ghcr.io/v2/'; do"
)
replace_once(
    "bin/devfix",
    "  probe_one \"$mode\" \"Homebrew bottles\" 'https://ghcr.io/v2/homebrew/core/' || fail=$((fail + 1))",
    "  probe_one \"$mode\" \"Homebrew bottles\" 'https://ghcr.io/v2/' || fail=$((fail + 1))"
)

old_loop = '''  elapsed=0
  last_progress=""
  last_progress_at=0
  while [ "$elapsed" -lt "$DEVFIX_BOOTSTRAP_TIMEOUT" ]; do
    if ! is_pid_alive "$pid"; then
      tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
      clear_state
      warn "TRANSPORT_FAILURE: Snowflake/Tor exited before bootstrap completed."
      return 1
    fi

    pt_failures=$(grep -c 'Managed proxy .*terminated with status code [1-9]' "$DEVFIX_TOR_LOG" 2>/dev/null || true)
    case "$pt_failures" in ''|*[!0-9]*) pt_failures=0 ;; esac
    if [ "$pt_failures" -ge 5 ]; then
      stop_tor_pid "$pid"
      clear_state
      tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
      warn "PLUGGABLE_TRANSPORT_FAILURE: lyrebird repeatedly exited before Snowflake could bootstrap."
      return 1
    fi

    latest_progress=$(grep 'Bootstrapped [0-9][0-9]*%' "$DEVFIX_TOR_LOG" 2>/dev/null | tail -n 1)
    if [ -n "$latest_progress" ] && [ "$latest_progress" != "$last_progress" ]; then
      progress_text=$(printf '%s\n' "$latest_progress" | sed 's/^.*Bootstrapped /Bootstrapped /')
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
      progress_text=$(printf '%s\n' "$last_progress" | sed 's/^.*Bootstrapped /Bootstrapped /')
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
    progress_text=$(printf '%s\n' "$last_progress" | sed 's/^.*Bootstrapped /Bootstrapped /')
  else
    progress_text="no bootstrap progress reported"
  fi
  stop_tor_pid "$pid"
  clear_state
  tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
  warn "TRANSPORT_FAILURE: Snowflake bootstrap timed out after ${DEVFIX_BOOTSTRAP_TIMEOUT}s at $progress_text."
  return 1
}'''

new_loop = '''  started_at=$(date +%s)
  last_progress=""
  last_progress_at="$started_at"
  last_status_at="$started_at"
  bootstrap_done=0
  validation_started_at=0

  while :; do
    now=$(date +%s)
    elapsed=$((now - started_at))
    [ "$elapsed" -lt "$DEVFIX_BOOTSTRAP_TIMEOUT" ] || break

    if ! is_pid_alive "$pid"; then
      tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
      clear_state
      warn "TRANSPORT_FAILURE: Snowflake/Tor exited before bootstrap completed."
      return 1
    fi

    pt_failures=$(grep -c 'Managed proxy .*terminated with status code [1-9]' "$DEVFIX_TOR_LOG" 2>/dev/null || true)
    case "$pt_failures" in ''|*[!0-9]*) pt_failures=0 ;; esac
    if [ "$pt_failures" -ge 5 ]; then
      stop_tor_pid "$pid"
      clear_state
      tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
      warn "PLUGGABLE_TRANSPORT_FAILURE: lyrebird repeatedly exited before Snowflake could bootstrap."
      return 1
    fi

    latest_progress=$(grep 'Bootstrapped [0-9][0-9]*%' "$DEVFIX_TOR_LOG" 2>/dev/null | tail -n 1)
    if [ -n "$latest_progress" ] && [ "$latest_progress" != "$last_progress" ]; then
      progress_text=$(printf '%s\n' "$latest_progress" | sed 's/^.*Bootstrapped /Bootstrapped /')
      info "Snowflake: $progress_text"
      last_progress="$latest_progress"
      last_progress_at="$now"
    fi

    if grep -q 'Bootstrapped 100%' "$DEVFIX_TOR_LOG" 2>/dev/null; then
      if [ "$bootstrap_done" -eq 0 ]; then
        bootstrap_done=1
        validation_started_at="$now"
        info "Snowflake bootstrap complete; validating developer endpoints..."
      fi

      if port_in_use "$port" && probe_critical_quiet snowflake; then
        ok "Connected with built-in Snowflake."
        log_line "transport=snowflake action=connected"
        return 0
      fi

      now=$(date +%s)
      validation_elapsed=$((now - validation_started_at))
      if [ "$validation_elapsed" -ge "$DEVFIX_ROUTE_VALIDATION_TIMEOUT" ]; then
        stop_tor_pid "$pid"
        clear_state
        tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
        warn "ROUTE_VALIDATION_FAILURE: Tor reached 100% bootstrap, but required developer endpoints were not reachable through Snowflake within ${DEVFIX_ROUTE_VALIDATION_TIMEOUT}s."
        return 1
      fi
    fi

    now=$(date +%s)
    if [ "$bootstrap_done" -eq 0 ] && [ -n "$last_progress" ] && [ $((now - last_progress_at)) -ge "$DEVFIX_BOOTSTRAP_STALL_TIMEOUT" ]; then
      progress_text=$(printf '%s\n' "$last_progress" | sed 's/^.*Bootstrapped /Bootstrapped /')
      stop_tor_pid "$pid"
      clear_state
      tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
      warn "TRANSPORT_FAILURE: Snowflake stalled at $progress_text for ${DEVFIX_BOOTSTRAP_STALL_TIMEOUT}s."
      return 1
    fi

    if [ $((now - last_status_at)) -ge 30 ]; then
      if [ "$bootstrap_done" -eq 1 ]; then
        info "Snowflake route validation still in progress..."
      else
        elapsed=$((now - started_at))
        info "Snowflake bootstrap still in progress (${elapsed}s/${DEVFIX_BOOTSTRAP_TIMEOUT}s)..."
      fi
      last_status_at="$now"
    fi

    sleep 1
  done

  if [ -n "$last_progress" ]; then
    progress_text=$(printf '%s\n' "$last_progress" | sed 's/^.*Bootstrapped /Bootstrapped /')
  else
    progress_text="no bootstrap progress reported"
  fi
  stop_tor_pid "$pid"
  clear_state
  tail -n 30 "$DEVFIX_TOR_LOG" >&2 2>/dev/null || true
  if [ "$bootstrap_done" -eq 1 ]; then
    warn "ROUTE_VALIDATION_FAILURE: Tor reached 100% bootstrap, but developer-route validation did not complete before the ${DEVFIX_BOOTSTRAP_TIMEOUT}s hard deadline."
  else
    warn "TRANSPORT_FAILURE: Snowflake bootstrap timed out after ${DEVFIX_BOOTSTRAP_TIMEOUT}s at $progress_text."
  fi
  return 1
}'''
replace_once("bin/devfix", old_loop, new_loop)

# Homebrew documents all_proxy as the SOCKS5 variable. Keep generic wrappers broad,
# but make the brew wrapper use the exact process environment proven on the target Mac.
replace_once(
    "bin/devfix",
    '''  ensure_route\n  apply_route_env\n  ensure_dirs\n  tmp="$DEVFIX_RUN_DIR/${label}.stderr.$$"''',
    '''  ensure_route\n  apply_route_env\n  if [ "$label" = "brew" ] && [ "$(file_get "$DEVFIX_STATE_FILE" TRANSPORT "")" = "snowflake" ]; then\n    unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY\n  fi\n  ensure_dirs\n  tmp="$DEVFIX_RUN_DIR/${label}.stderr.$$"'''
)

# Test fake curl: capture the URL and model the registry base endpoint semantics.
replace_once(
    "tests/test_devfix.sh",
    '''cat > "$TMP/fakecurl" <<'SH'\n#!/bin/bash\ncase "${FAKE_CURL_MODE:-ok}" in\n  ok) printf '200' ;;\n  blocked) printf '000'; exit 28 ;;\n  proxy-only)\n    seen=0\n    for a in "$@"; do [ "$a" != "--proxy" ] || seen=1; done\n    if [ "$seen" -eq 1 ]; then printf '200'; else printf '000'; exit 28; fi\n    ;;\nesac\nSH''',
    '''cat > "$TMP/fakecurl" <<'SH'\n#!/bin/bash\nurl=""\nseen_proxy=0\nfor a in "$@"; do\n  [ "$a" != "--proxy" ] || seen_proxy=1\n  case "$a" in http://*|https://*) url="$a" ;; esac\ndone\n[ -z "${FAKE_CURL_CAPTURE:-}" ] || printf '%s\\n' "$url" >> "$FAKE_CURL_CAPTURE"\ncase "${FAKE_CURL_MODE:-ok}" in\n  ok) printf '200' ;;\n  blocked) printf '000'; exit 28 ;;\n  registry-probe)\n    case "$url" in\n      https://ghcr.io/v2/) printf '401' ;;\n      https://ghcr.io/*) printf '404' ;;\n      *) printf '200' ;;\n    esac\n    ;;\n  proxy-only)\n    if [ "$seen_proxy" -eq 1 ]; then printf '200'; else printf '000'; exit 28; fi\n    ;;\nesac\nSH'''
)

# Insert 100%-bootstrap route validation regression after the managed-proxy crash test.
anchor = '''assert_contains "managed transport crash classified" "PLUGGABLE_TRANSPORT_FAILURE" "$pt_err"\ncat > "$TMP/libexec/tor/tor" <<'SH'\n#!/bin/bash\nexec sleep 300\nSH\nchmod +x "$TMP/libexec/tor/tor"\nexport DEVFIX_TEST_MODE=1\nunset DEVFIX_BOOTSTRAP_TIMEOUT DEVFIX_BOOTSTRAP_STALL_TIMEOUT\n'''
insert = '''assert_contains "managed transport crash classified" "PLUGGABLE_TRANSPORT_FAILURE" "$pt_err"\n\n# 100% bootstrap must validate against the registry API base endpoint and succeed.\ncat > "$TMP/libexec/tor/tor" <<'SH'\n#!/bin/bash\ntorrc="${2:-}"\nport=$(sed -n 's/^SocksPort 127.0.0.1://p' "$torrc" | head -n 1)\necho 'Bootstrapped 100% (done): Done'\nexec python3 - "$port" <<'PY'\nimport socket, sys\ns = socket.socket()\ns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\ns.bind(("127.0.0.1", int(sys.argv[1])))\ns.listen(16)\nwhile True:\n    c, _ = s.accept()\n    c.close()\nPY\nSH\nchmod +x "$TMP/libexec/tor/tor"\nunset DEVFIX_TEST_MODE\nexport DEVFIX_BOOTSTRAP_TIMEOUT=10\nexport DEVFIX_BOOTSTRAP_STALL_TIMEOUT=5\nexport DEVFIX_ROUTE_VALIDATION_TIMEOUT=3\nexport FAKE_CURL_CAPTURE="$TMP/curl-urls"\n: > "$FAKE_CURL_CAPTURE"\nset +e\nroute_out=$(FAKE_CURL_MODE=registry-probe "$DEVFIX" connect snowflake 2>&1)\nroute_rc=$?\nset -e\nassert_eq "100 percent bootstrap validates successfully" "0" "$route_rc"\nassert_contains "100 percent bootstrap reports connected" "Connected with built-in Snowflake." "$route_out"\nif grep -Fxq 'https://ghcr.io/v2/' "$FAKE_CURL_CAPTURE"; then pass "registry base endpoint used"; else fail "registry base endpoint used"; fi\nif grep -Fq 'https://ghcr.io/v2/homebrew/core/' "$FAKE_CURL_CAPTURE"; then fail "repository root is not used as health endpoint"; else pass "repository root is not used as health endpoint"; fi\n"$DEVFIX" disconnect >/dev/null\n\n# A failed post-100% route check is not a bootstrap stall.\n: > "$FAKE_CURL_CAPTURE"\nset +e\nvalidation_err=$(FAKE_CURL_MODE=blocked "$DEVFIX" connect snowflake 2>&1 >/dev/null)\nvalidation_rc=$?\nset -e\nif [ "$validation_rc" -ne 0 ]; then pass "route validation failure returns failure"; else fail "route validation failure returns failure"; fi\nassert_contains "route validation failure classified" "ROUTE_VALIDATION_FAILURE" "$validation_err"\nif printf '%s' "$validation_err" | grep -Fq 'stalled at Bootstrapped 100%'; then fail "100 percent is never classified as bootstrap stall"; else pass "100 percent is never classified as bootstrap stall"; fi\n\ncat > "$TMP/libexec/tor/tor" <<'SH'\n#!/bin/bash\nexec sleep 300\nSH\nchmod +x "$TMP/libexec/tor/tor"\nexport DEVFIX_TEST_MODE=1\nunset DEVFIX_BOOTSTRAP_TIMEOUT DEVFIX_BOOTSTRAP_STALL_TIMEOUT DEVFIX_ROUTE_VALIDATION_TIMEOUT FAKE_CURL_CAPTURE\n'''
replace_once("tests/test_devfix.sh", anchor, insert)

# Tighten the Homebrew wrapper regression to the exact SOCKS environment that passed on the real Mac.
replace_once(
    "tests/test_devfix.sh",
    '''captured=$(cat "$BREW_CAPTURE")\nassert_contains "snowflake wrapper proxy" "socks5h://127.0.0.1:" "$captured"''',
    '''captured=$(cat "$BREW_CAPTURE")\ncase "$captured" in\n  '|socks5h://127.0.0.1:'*) pass "snowflake brew wrapper uses all_proxy SOCKS only" ;;\n  *) fail "snowflake brew wrapper uses all_proxy SOCKS only (captured=$captured)" ;;\nesac'''
)

# Changelog and man page.
p = Path("CHANGELOG.md")
s = p.read_text()
header = "# Changelog\n\n"
if not s.startswith(header):
    raise SystemExit("CHANGELOG.md: unexpected header")
entry = '''## 2.0.4 - 2026-08-16\n\n- Fixed Snowflake post-bootstrap validation to probe the GHCR Registry API base endpoint (`/v2/`) instead of treating a repository root as a health endpoint.\n- Made bootstrap and validation deadlines use real wall-clock time, so slow endpoint probes cannot silently stretch a nominal timeout into many minutes.\n- Separated 100% Tor bootstrap from developer-route validation; 100% can no longer be misreported as a bootstrap stall.\n- Added a dedicated `ROUTE_VALIDATION_FAILURE` diagnosis for the rare case where Tor is fully bootstrapped but required developer endpoints remain unreachable.\n- Aligned `devfix brew` Snowflake routing with Homebrew's documented SOCKS environment by using process-scoped `all_proxy`/`ALL_PROXY` and clearing protocol-specific proxy variables for the brew subprocess.\n- Added regressions for the exact GHCR health endpoint, successful 100% bootstrap validation, post-100% failure classification, and Homebrew SOCKS environment.\n\n'''
p.write_text(header + entry + s[len(header):])
replace_once("man/devfix.1", '"DevFix 2.0.3"', '"DevFix 2.0.4"')

# One-shot helper removes itself from the product commit. The workflow is removed
# separately through the connector because Actions tokens cannot update workflows.
Path(".github/bootstrap/devfix_204_patch.py").unlink()
