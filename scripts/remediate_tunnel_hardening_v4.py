#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    p = Path(path)
    text = p.read_text()
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly 1 match in {path}, found {n}")
    p.write_text(text.replace(old, new, 1))


def replace_function(path: str, name: str, next_name: str, replacement: str) -> None:
    p = Path(path)
    text = p.read_text()
    start = text.find(f"{name}() {{")
    end = text.find(f"\n{next_name}() {{", start)
    if start < 0 or end < 0:
        raise SystemExit(f"function boundaries not found in {path}: {name} -> {next_name}")
    p.write_text(text[:start] + replacement.rstrip() + "\n" + text[end:])


cli = "tunnel/cli/devfix-tunnel"
replace_function(cli, "start_transport", "marker_get", r'''start_transport() {
  requested_mode="$1"
  ensure_dirs
  runtime_available || die "independent Tor runtime is missing under $TUNNEL_LIBEXEC_DIR; install the DevFix Tunnel package"

  old_pid=$(state_get PID '')
  old_state=$(state_get STATE '')
  old_mode=$(state_get MODE '')

  if [ "$old_state" = "CONNECTED" ] && pid_is_owned "$old_pid"; then
    if [ "$requested_mode" = "$old_mode" ]; then
      return 0
    fi
    if [ "$old_mode" = "SYSTEM_PROXY" ]; then
      die "an active System Proxy session already exists; disconnect or repair it before starting another transport mode"
    fi
    stop_owned_tor "$old_pid" || die "could not safely stop the previous tunnel-owned SOCKS transport"
  elif [ -n "$old_pid" ] && is_pid_alive "$old_pid"; then
    if ! pid_is_owned "$old_pid"; then
      die "stale state references a live process not owned by DevFix Tunnel; run 'devfix-tunnel repair' after reviewing status"
    fi
    if [ "$old_mode" = "SYSTEM_PROXY" ]; then
      die "stale System Proxy state with a live owned Tor process requires 'devfix-tunnel repair' before transport restart"
    fi
    stop_owned_tor "$old_pid" || die "could not safely stop stale tunnel-owned Tor process"
  fi

  clear_runtime_state
  port=$(choose_socks_port "$DEFAULT_SOCKS_PORT") ||
    die "no free local SOCKS port in $DEFAULT_SOCKS_PORT-$((DEFAULT_SOCKS_PORT + 19))"
  write_torrc "$port"
  : > "$TUNNEL_TOR_LOG"
  chmod 600 "$TUNNEL_TOR_LOG" 2>/dev/null || true

  session="$(now_epoch)-$$"
  started="$(now_utc)"
  write_state STARTING SOCKS '' "$port" "$session" "$started" ''
  info "Starting DevFix Tunnel Snowflake transport..."
  "$TUNNEL_TOR_BIN" -f "$TUNNEL_TORRC" >> "$TUNNEL_TOR_LOG" 2>&1 &
  pid=$!
  printf '%s\n' "$pid" > "$TUNNEL_PID_FILE"
  chmod 600 "$TUNNEL_PID_FILE" 2>/dev/null || true
  write_state BOOTSTRAPPING SOCKS "$pid" "$port" "$session" "$started" ''
  log_line "session=$session state=BOOTSTRAPPING pid=$pid port=$port"

  start_epoch=$(now_epoch)
  deadline=$((start_epoch + BOOTSTRAP_TIMEOUT))
  last_progress_epoch=$start_epoch
  last_percent=-1
  while [ "$(now_epoch)" -lt "$deadline" ]; do
    if ! is_pid_alive "$pid"; then
      write_state FAILED SOCKS "$pid" "$port" "$session" "$started" ''
      err "TRANSPORT_PROCESS_FAILURE: Tor exited before bootstrap completed."
      return 1
    fi
    percent=$(bootstrap_percent)
    if [ "$percent" != "$last_percent" ]; then
      info "Bootstrapped ${percent}%"
      last_percent="$percent"
      last_progress_epoch=$(now_epoch)
    fi
    if [ "$percent" -ge 100 ] 2>/dev/null; then
      break
    fi
    if [ $(( $(now_epoch) - last_progress_epoch )) -ge "$STALL_TIMEOUT" ]; then
      stop_owned_tor "$pid" || true
      write_state FAILED SOCKS "$pid" "$port" "$session" "$started" ''
      err "SNOWFLAKE_BOOTSTRAP_FAILURE: bootstrap stalled at ${percent}% for ${STALL_TIMEOUT}s."
      return 1
    fi
    sleep 1
  done

  percent=$(bootstrap_percent)
  if [ "$percent" -lt 100 ] 2>/dev/null; then
    stop_owned_tor "$pid" || true
    write_state FAILED SOCKS "$pid" "$port" "$session" "$started" ''
    err "TIMEOUT: Snowflake did not reach 100% within ${BOOTSTRAP_TIMEOUT}s."
    return 1
  fi

  write_state VALIDATING SOCKS "$pid" "$port" "$session" "$started" ''
  info "Snowflake bootstrap complete; validating SOCKS route..."
  if ! validate_socks_route "$port"; then
    stop_owned_tor "$pid" || true
    write_state FAILED SOCKS "$pid" "$port" "$session" "$started" ''
    err "ROUTE_VALIDATION_FAILURE: Tor reached 100% but routed HTTPS validation failed."
    return 1
  fi

  write_state CONNECTED SOCKS "$pid" "$port" "$session" "$started" ''
  log_line "session=$session state=CONNECTED mode=SOCKS pid=$pid port=$port"
  info "Snowflake transport is ready."
  info "Local SOCKS: socks5h://127.0.0.1:$port"
}''')

replace_function(cli, "cmd_connect", "cmd_status", r'''cmd_connect() {
  mode="system"
  service=""
  if [ "${1:-}" = "socks" ]; then
    mode="socks"
    shift
  elif [ "${1:-}" = "system" ]; then
    mode="system"
    shift
  fi

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --service)
        [ "$#" -ge 2 ] || die "--service requires a network service name"
        service="$2"
        shift 2
        ;;
      *) die "unknown connect option: $1" ;;
    esac
  done

  existing_state=$(state_get STATE DISCONNECTED)
  existing_mode=$(state_get MODE NONE)
  existing_pid=$(state_get PID '')
  if [ "$existing_state" = "CONNECTED" ] && pid_is_owned "$existing_pid"; then
    case "$mode:$existing_mode" in
      system:SYSTEM_PROXY)
        if [ -f "$TUNNEL_PROXY_FAILED" ]; then
          die "existing System Proxy session is degraded; run 'devfix-tunnel status' and 'devfix-tunnel repair'"
        fi
        info "DevFix Tunnel is already connected in System Proxy mode."
        return 0
        ;;
      socks:SOCKS)
        info "DevFix Tunnel is already connected in SOCKS-only mode."
        return 0
        ;;
      socks:SYSTEM_PROXY)
        die "already connected in System Proxy mode; disconnect before switching to SOCKS-only mode"
        ;;
      system:SOCKS)
        die "already connected in SOCKS-only mode; disconnect before switching to System Proxy mode"
        ;;
    esac
  fi

  if [ "$mode" = "socks" ]; then
    start_transport SOCKS || exit 1
    info "Connected in SOCKS-only mode. macOS System Proxy was not changed."
    return 0
  fi

  start_transport SYSTEM_PROXY || exit 1
  if ! start_system_proxy_guardian "$service"; then
    pid=$(state_get PID '')
    stop_owned_tor "$pid" || true
    clear_runtime_state
    die "System Proxy activation failed; transport was rolled back"
  fi
  info "Connected with DevFix Tunnel System Proxy."
}''')

# Insert a mode-preserving restart helper before cmd_repair.
p = Path(cli)
text = p.read_text()
needle = "\ncmd_repair() {"
if text.count(needle) != 1:
    raise SystemExit("cmd_repair insertion point not unique")
restart_fn = r'''
cmd_restart() {
  requested="${1:-}"
  if [ -z "$requested" ]; then
    current_mode=$(state_get MODE NONE)
    case "$current_mode" in
      SOCKS) requested="socks" ;;
      SYSTEM_PROXY) requested="system" ;;
      *) requested="system" ;;
    esac
  fi
  case "$requested" in
    system|socks) ;;
    *) die "restart mode must be 'system' or 'socks'" ;;
  esac
  cmd_disconnect || return 1
  cmd_connect "$requested"
}
'''
p.write_text(text.replace(needle, "\n" + restart_fn.rstrip() + needle, 1))
replace_once(cli, 'restart) shift; saved_mode="${1:-system}"; cmd_disconnect || exit 1; cmd_connect "$saved_mode" ;;', 'restart) shift; cmd_restart "$@" ;;', "restart dispatch")

guardian = "tunnel/libexec/devfix-tunnel-guardian"
replace_once(guardian, 'SLEEP_BIN="${DEVFIX_TUNNEL_SLEEP_BIN:-/bin/sleep}"', 'SLEEP_BIN="${DEVFIX_TUNNEL_SLEEP_BIN:-/bin/sleep}"\nUSER_SUDO_BIN="${DEVFIX_TUNNEL_USER_SUDO_BIN:-/usr/bin/sudo}"', "guardian user sudo bin")

replace_function(guardian, "safe_user_marker", "owner_get", r'''user_exec() {
  uid="$1"
  shift
  case "$uid" in ''|*[!0-9]*) return 1 ;; esac
  [ -x "$USER_SUDO_BIN" ] || return 1
  "$USER_SUDO_BIN" -n -u "#$uid" "$@"
}

safe_user_marker() {
  user_state="$1"
  name="$2"
  content="$3"
  uid="${4:-}"
  gid="${5:-}"
  validate_user_state "$user_state" "$uid" "$gid" || return 1
  case "$name" in ''|*/*|*'..'*) return 1 ;; esac
  run_dir="$user_state/run"
  tmp="$run_dir/$name.tmp.$$"
  target="$run_dir/$name"

  if [ "$TEST_MODE" = "1" ]; then
    printf '%s\n' "$content" > "$tmp" || return 1
    chmod 600 "$tmp" 2>/dev/null || true
    mv -f "$tmp" "$target"
    return $?
  fi

  printf '%s\n' "$content" | user_exec "$uid" /usr/bin/tee "$tmp" >/dev/null || return 1
  user_exec "$uid" /bin/chmod 600 "$tmp" || { user_exec "$uid" /bin/rm -f "$tmp" || true; return 1; }
  user_exec "$uid" /bin/mv -f "$tmp" "$target"
}

safe_user_remove() {
  user_state="$1"
  name="$2"
  uid="$3"
  gid="$4"
  validate_user_state "$user_state" "$uid" "$gid" || return 1
  case "$name" in ''|*/*|*'..'*) return 1 ;; esac
  target="$user_state/run/$name"
  if [ "$TEST_MODE" = "1" ]; then
    rm -f "$target"
  else
    user_exec "$uid" /bin/rm -f "$target"
  fi
}

safe_user_marker_exists() {
  user_state="$1"
  name="$2"
  uid="$3"
  gid="$4"
  validate_user_state "$user_state" "$uid" "$gid" || return 1
  case "$name" in ''|*/*|*'..'*) return 1 ;; esac
  target="$user_state/run/$name"
  if [ "$TEST_MODE" = "1" ]; then
    [ -f "$target" ]
  else
    user_exec "$uid" /bin/test -f "$target"
  fi
}

safe_user_marker_value() {
  user_state="$1"
  name="$2"
  key="$3"
  uid="$4"
  gid="$5"
  validate_user_state "$user_state" "$uid" "$gid" || return 1
  case "$name" in ''|*/*|*'..'*) return 1 ;; esac
  case "$key" in ''|*[!A-Z0-9_]*) return 1 ;; esac
  target="$user_state/run/$name"
  if [ "$TEST_MODE" = "1" ]; then
    sed -n "s/^${key}=//p" "$target" 2>/dev/null | tail -n 1
  else
    user_exec "$uid" /usr/bin/sed -n "s/^${key}=//p" "$target" 2>/dev/null | tail -n 1
  fi
}''')

replace_function(guardian, "snapshot_conflict_reason", "current_socks", r'''snapshot_conflict_reason() {
  snapshot="$1"
  socks=$(cat "$snapshot/socks")
  web=$(cat "$snapshot/web")
  secure=$(cat "$snapshot/secureweb")
  auto=$(cat "$snapshot/autoproxy")
  discovery=$(cat "$snapshot/autodiscovery")
  socks_auth=$(proxy_field "$socks" "Authenticated Proxy Enabled")

  case "$socks_auth" in
    1|Yes|YES|yes|On|ON|on)
      printf '%s' 'EXISTING_AUTHENTICATED_SOCKS_CONFIG'
      return
      ;;
  esac
  if proxy_enabled "$socks"; then printf '%s' 'EXISTING_SOCKS_PROXY'; return; fi
  if proxy_enabled "$web"; then printf '%s' 'EXISTING_HTTP_PROXY'; return; fi
  if proxy_enabled "$secure"; then printf '%s' 'EXISTING_HTTPS_PROXY'; return; fi
  if proxy_enabled "$auto"; then printf '%s' 'EXISTING_PAC_PROXY'; return; fi
  if proxy_enabled "$discovery"; then printf '%s' 'EXISTING_PROXY_AUTODISCOVERY'; return; fi
  printf '%s' ''
}''')

replace_function(guardian, "restore_snapshot", "clear_owner_after_restore", r'''restore_snapshot() {
  service="$1"
  snapshot="$2"
  previous=$(cat "$snapshot/socks")
  previous_enabled=$(proxy_field "$previous" Enabled)
  previous_server=$(proxy_field "$previous" Server)
  previous_port=$(proxy_field "$previous" Port)
  previous_auth=$(proxy_field "$previous" "Authenticated Proxy Enabled")

  case "$previous_auth" in
    1|Yes|YES|yes|On|ON|on) return 1 ;;
  esac

  if [ -n "$previous_server" ]; then
    case "$previous_port" in
      ''|*[!0-9]*) return 1 ;;
      *) ns_set -setsocksfirewallproxy "$service" "$previous_server" "$previous_port" off >/dev/null || return 1 ;;
    esac
  fi

  case "$previous_enabled" in
    Yes) ns_set -setsocksfirewallproxystate "$service" on >/dev/null || return 1 ;;
    *) ns_set -setsocksfirewallproxystate "$service" off >/dev/null || return 1 ;;
  esac

  after=$(current_socks "$service") || return 1
  after_enabled=$(proxy_field "$after" Enabled)
  after_server=$(proxy_field "$after" Server)
  after_port=$(proxy_field "$after" Port)
  after_auth=$(proxy_field "$after" "Authenticated Proxy Enabled")

  if [ "$previous_enabled" = "Yes" ]; then
    [ "$after_enabled" = "Yes" ] || return 1
  else
    [ "$after_enabled" != "Yes" ] || return 1
  fi
  if [ -n "$previous_server" ]; then
    [ "$after_server" = "$previous_server" ] || return 1
    [ "$after_port" = "$previous_port" ] || return 1
  fi
  case "$after_auth" in 1|Yes|YES|yes|On|ON|on) return 1 ;; esac
  return 0
}''')

replace_once(guardian, 'rm -f "$user_state/run/system-proxy.ready" 2>/dev/null || true', 'safe_user_remove "$user_state" "system-proxy.ready" "$uid" "$gid" || true', "root ready-marker removal")

replace_function(guardian, "guardian_monitor", "cmd_apply", r'''guardian_monitor() {
  session="$1"
  tor_pid="$2"
  service="$3"
  port="$4"
  user_state="$5"
  uid="$6"
  gid="$7"
  original_service="$service"

  while :; do
    if safe_user_marker_exists "$user_state" "system-proxy.stop" "$uid" "$gid"; then
      requested=$(safe_user_marker_value "$user_state" "system-proxy.stop" SESSION "$uid" "$gid" || true)
      if [ -z "$requested" ] || [ "$requested" = "$session" ]; then
        recover_owned_proxy "$session" "$user_state" "$uid" "$gid"
        return $?
      fi
    fi

    if ! kill -0 "$tor_pid" 2>/dev/null; then
      safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=TOR_PROCESS_DIED" "$uid" "$gid" || true
      recover_owned_proxy "$session" "$user_state" "$uid" "$gid"
      return $?
    fi

    if ! proxy_matches_owned "$service" "$port"; then
      write_owner "$session" CONFLICT "$service" "$port" "$user_state" "$uid" "$gid" "$(owner_get SNAPSHOT '')" "$$"
      safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=PROXY_OWNERSHIP_LOST" "$uid" "$gid" || true
      return 3
    fi

    active=$(discover_service '' 2>/dev/null || true)
    if [ -n "$active" ] && [ "$active" != "$original_service" ]; then
      safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=NETWORK_SERVICE_CHANGED" "$uid" "$gid" || true
      recover_owned_proxy "$session" "$user_state" "$uid" "$gid"
      return $?
    fi
    "$SLEEP_BIN" 1
  done
}''')

# Extend the fake networksetup and integration matrix.
test_path = Path("tests/test_devfix_tunnel.sh")
test = test_path.read_text()
replace = "printf 'Enabled: %s\\nServer: %s\\nPort: %s\\nAuthenticated Proxy Enabled: 0\\n' \"$SOCKS_ENABLED\" \"$SOCKS_SERVER\" \"$SOCKS_PORT\" ;;"
replacement = "printf 'Enabled: %s\\nServer: %s\\nPort: %s\\nAuthenticated Proxy Enabled: %s\\n' \"$SOCKS_ENABLED\" \"$SOCKS_SERVER\" \"$SOCKS_PORT\" \"${FAKE_SOCKS_AUTH_ENABLED:-0}\" ;;"
if test.count(replace) != 1:
    raise SystemExit("fake networksetup SOCKS output pattern not found")
test = test.replace(replace, replacement, 1)
# Ensure each fixture clears auth flag.
test = test.replace('unset FAKE_WEB_ENABLED FAKE_SECURE_ENABLED FAKE_AUTO_ENABLED FAKE_DISCOVERY_ENABLED || true;', 'unset FAKE_WEB_ENABLED FAKE_SECURE_ENABLED FAKE_AUTO_ENABLED FAKE_DISCOVERY_ENABLED FAKE_SOCKS_AUTH_ENABLED || true;', 1)
anchor = "new_case doctor\n"
if test.count(anchor) != 1:
    raise SystemExit("doctor test anchor not found")
extra = r'''new_case idempotent_system
"$TUNNEL" connect system > "$CASE/connect1.out" 2>&1 || fail "idempotent system first connect"
session1=$(sed -n 's/^SESSION=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state")
proxy1=$(cat "$FAKE_PROXY_STATE_FILE")
"$TUNNEL" connect system > "$CASE/connect2.out" 2>&1 || fail "idempotent system second connect"
session2=$(sed -n 's/^SESSION=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state")
[ "$session1" = "$session2" ] || fail "repeated system connect created a new session"
[ "$proxy1" = "$(cat "$FAKE_PROXY_STATE_FILE")" ] || fail "repeated system connect changed proxy state"
grep -q 'already connected in System Proxy mode' "$CASE/connect2.out" || fail "idempotent system contract"
if "$TUNNEL" connect socks > "$CASE/switch.out" 2>&1; then fail "system to socks transition should require disconnect"; fi
grep -q 'disconnect before switching to SOCKS-only mode' "$CASE/switch.out" || fail "system to socks refusal contract"
proxy_is_enabled_owned || fail "mode-switch refusal damaged System Proxy"
"$TUNNEL" disconnect >/dev/null 2>&1 || fail "idempotent system cleanup"
pass "System Proxy idempotency and transition refusal"

new_case idempotent_socks
"$TUNNEL" connect socks > "$CASE/connect1.out" 2>&1 || fail "idempotent socks first connect"
session1=$(sed -n 's/^SESSION=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state")
"$TUNNEL" connect socks > "$CASE/connect2.out" 2>&1 || fail "idempotent socks second connect"
session2=$(sed -n 's/^SESSION=//p' "$DEVFIX_TUNNEL_STATE_DIR/run/state")
[ "$session1" = "$session2" ] || fail "repeated SOCKS connect created a new session"
grep -q 'already connected in SOCKS-only mode' "$CASE/connect2.out" || fail "idempotent SOCKS contract"
if "$TUNNEL" connect system > "$CASE/switch.out" 2>&1; then fail "socks to system transition should require disconnect"; fi
grep -q 'disconnect before switching to System Proxy mode' "$CASE/switch.out" || fail "socks to system refusal contract"
"$TUNNEL" restart > "$CASE/restart.out" 2>&1 || fail "mode-preserving restart"
grep -q '^MODE=SOCKS$' "$DEVFIX_TUNNEL_STATE_DIR/run/state" || fail "restart drifted from SOCKS to System Proxy"
proxy_is_restored || fail "SOCKS restart changed proxy"
"$TUNNEL" disconnect >/dev/null 2>&1 || fail "idempotent socks cleanup"
pass "SOCKS idempotency, transition refusal, and restart mode preservation"

new_case disabled_authenticated_socks
export FAKE_SOCKS_AUTH_ENABLED=1
if "$TUNNEL" connect system > "$CASE/connect.out" 2>&1; then fail "disabled authenticated SOCKS config should block System Proxy"; fi
grep -q 'EXISTING_AUTHENTICATED_SOCKS_CONFIG' "$CASE/connect.out" || fail "authenticated SOCKS conflict classification"
proxy_is_restored || fail "authenticated disabled SOCKS config was modified"
unset FAKE_SOCKS_AUTH_ENABLED
pass "disabled authenticated SOCKS configuration preserved"

# Static privilege-boundary guard: production user-marker writes must drop to UID.
grep -q 'USER_SUDO_BIN' "$GUARDIAN" || fail "guardian user privilege-drop binary missing"
grep -q -- '-u "#$uid"' "$GUARDIAN" || fail "guardian marker path I/O does not drop to target UID"
grep -q 'safe_user_marker_exists' "$GUARDIAN" || fail "guardian stop marker read is not user-scoped"
pass "guardian user-marker privilege boundary"

'''
test = test.replace(anchor, extra + anchor, 1)
test_path.write_text(test)

# Extend Intel macOS command contract with the exact privilege-drop form.
workflow = Path(".github/workflows/tunnel-ci.yml")
w = workflow.read_text()
needle = '          /usr/sbin/networksetup -help 2>&1 | grep -q -- "-listnetworkserviceorder"\n'
if w.count(needle) != 1:
    raise SystemExit("macOS command-contract insertion point not found")
w = w.replace(needle, needle + '          sudo -n -u "#$(id -u)" /usr/bin/true\n', 1)
workflow.write_text(w)

rem = Path("docs/tunnel/remediations")
rem.mkdir(parents=True, exist_ok=True)
(rem / "004_RC_SECURITY_IDEMPOTENCY_REVIEW.md").write_text(
    "# Remediation 004 — RC security/idempotency review\n\n"
    "Post-green-CI architecture review found four pre-real-Mac failure classes: `MODE_TRANSITION_NOT_IDEMPOTENT`, `RESTART_MODE_DRIFT`, `ROOT_USER_STATE_TOCTOU`, and `DISABLED_AUTHENTICATED_SOCKS_CONFIG`. V4 closes them with explicit same-mode idempotency, fail-closed cross-mode transitions, mode-preserving restart, user-identity marker I/O from the privileged guardian, authenticated dormant SOCKS conflict detection, and stronger restore verification. Existing crash/conflict/network-change tests remain mandatory.\n"
)
