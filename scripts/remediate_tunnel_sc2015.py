#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 match in {path}, found {count}")
    p.write_text(text.replace(old, new, 1))


def replace_function(path: str, name: str, next_name: str, replacement: str) -> None:
    p = Path(path)
    text = p.read_text()
    start = text.find(f"{name}() {{")
    end = text.find(f"\n{next_name}() {{", start)
    if start < 0 or end < 0:
        raise SystemExit(f"function boundaries not found: {name} -> {next_name}")
    p.write_text(text[:start] + replacement.rstrip() + "\n" + text[end:])


cli = "tunnel/cli/devfix-tunnel"
replace_once(cli, 'SELF_DIR=$(cd -- "$(dirname -- "$SELF_PATH")" 2>/dev/null && pwd || pwd)', 'SELF_DIR=$(cd -- "$(dirname -- "$SELF_PATH")" 2>/dev/null && pwd)\nif [ -z "$SELF_DIR" ]; then\n  SELF_DIR=$(pwd)\nfi', "cli SELF_DIR")
replace_once(cli, "[ -x /usr/sbin/networksetup ] && printf 'networksetup: OK\\n' || { printf 'networksetup: MISSING\\n'; fail=1; };", "if [ -x /usr/sbin/networksetup ]; then printf 'networksetup: OK\\n'; else printf 'networksetup: MISSING\\n'; fail=1; fi;", "cli doctor networksetup")
replace_once(cli, "[ -x /sbin/route ] && printf 'route: OK\\n' || { printf 'route: MISSING\\n'; fail=1; };", "if [ -x /sbin/route ]; then printf 'route: OK\\n'; else printf 'route: MISSING\\n'; fail=1; fi;", "cli doctor route")

guardian = "tunnel/libexec/devfix-tunnel-guardian"
replace_function(guardian, "recover_owned_proxy", "guardian_monitor", r'''recover_owned_proxy() {
  requested_session="${1:-}"
  marker_user_state="${2:-}"
  marker_uid="${3:-}"
  marker_gid="${4:-}"

  if [ ! -f "$CURRENT_FILE" ]; then
    if [ -n "$marker_user_state" ]; then
      safe_user_marker "$marker_user_state" "system-proxy.restored" "SESSION=${requested_session:-none}
RESULT=NO_OWNED_PROXY" "$marker_uid" "$marker_gid" || true
    fi
    return 0
  fi

  session=$(owner_get SESSION '')
  phase=$(owner_get PHASE '')
  service=$(owner_get SERVICE '')
  port=$(owner_get PORT '')
  user_state=$(owner_get USER_STATE "$marker_user_state")
  uid=$(owner_get UID "$marker_uid")
  gid=$(owner_get GID "$marker_gid")
  snapshot=$(owner_get SNAPSHOT '')

  if [ -n "$requested_session" ] && [ "$session" != "$requested_session" ]; then
    log_line "recover_refused requested=$requested_session owned=$session reason=SESSION_MISMATCH"
    return 2
  fi

  case "$phase" in
    SNAPSHOTTED)
      rm -f "$CURRENT_FILE"
      [ -d "$snapshot" ] && rm -rf "$snapshot"
      safe_user_marker "$user_state" "system-proxy.restored" "SESSION=$session
RESULT=SNAPSHOT_ONLY_CLEARED" "$uid" "$gid" || true
      return 0
      ;;
    APPLIED)
      if proxy_matches_owned "$service" "$port"; then
        if restore_snapshot "$service" "$snapshot"; then
          clear_owner_after_restore "$snapshot"
          safe_user_marker "$user_state" "system-proxy.restored" "SESSION=$session
SERVICE=$service
RESULT=RESTORED" "$uid" "$gid" || true
          rm -f "$user_state/run/system-proxy.ready" 2>/dev/null || true
          log_line "session=$session restore=success service=$service"
          return 0
        fi
        safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=RESTORE_COMMAND_FAILED" "$uid" "$gid" || true
        log_line "session=$session restore=failed reason=RESTORE_COMMAND_FAILED"
        return 1
      fi
      write_owner "$session" CONFLICT "$service" "$port" "$user_state" "$uid" "$gid" "$snapshot" "$(owner_get GUARDIAN_PID '')"
      safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=PROXY_OWNERSHIP_LOST" "$uid" "$gid" || true
      log_line "session=$session restore=refused reason=PROXY_OWNERSHIP_LOST"
      return 3
      ;;
    CONFLICT)
      safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=PROXY_OWNERSHIP_CONFLICT_REQUIRES_MANUAL_REVIEW" "$uid" "$gid" || true
      return 3
      ;;
    *)
      log_line "recover_refused session=$session unknown_phase=$phase"
      return 4
      ;;
  esac
}''')

replace_function(guardian, "cmd_apply", "cmd_recover", r'''cmd_apply() {
  require_root
  user_state=""
  session=""
  tor_pid=""
  port=""
  uid=""
  gid=""
  service_override=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --user-state) user_state="$2"; shift 2 ;;
      --session) session="$2"; shift 2 ;;
      --tor-pid) tor_pid="$2"; shift 2 ;;
      --port) port="$2"; shift 2 ;;
      --uid) uid="$2"; shift 2 ;;
      --gid) gid="$2"; shift 2 ;;
      --service) service_override="$2"; shift 2 ;;
      *) die "unknown apply argument: $1" ;;
    esac
  done

  if [ -z "$user_state" ] || [ -z "$session" ] || [ -z "$tor_pid" ] || [ -z "$port" ]; then
    die "apply requires user-state/session/tor-pid/port"
  fi

  validate_user_state "$user_state" "$uid" "$gid" ||
    die "user state path/ownership validation failed"

  case "$session" in *$'\n'*|*$'\r'*) die "invalid session" ;; esac
  case "$service_override" in *$'\n'*|*$'\r'*) die "invalid service name" ;; esac
  case "$tor_pid" in *[!0-9]*|'') die "invalid tor pid" ;; esac
  case "$port" in *[!0-9]*|'') die "invalid SOCKS port" ;; esac

  ensure_system_dir
  if [ -f "$CURRENT_FILE" ]; then
    if ! recover_owned_proxy '' "$user_state" "$uid" "$gid"; then
      safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=STALE_PROXY_RECOVERY_BLOCKED" "$uid" "$gid" || true
      exit 1
    fi
  fi

  service=$(discover_service "$service_override") || {
    safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=ACTIVE_NETWORK_SERVICE_NOT_FOUND" "$uid" "$gid" || true
    exit 1
  }

  snapshot="$SYSTEM_STATE_DIR/snapshot-$session"
  rm -rf "$snapshot"
  capture_snapshot "$service" "$snapshot" || {
    safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=PROXY_SNAPSHOT_FAILED" "$uid" "$gid" || true
    rm -rf "$snapshot"
    exit 1
  }

  conflict=$(snapshot_conflict_reason "$snapshot")
  if [ -n "$conflict" ]; then
    safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=$conflict" "$uid" "$gid" || true
    log_line "session=$session apply=refused service=$service reason=$conflict"
    rm -rf "$snapshot"
    exit 1
  fi

  write_owner "$session" SNAPSHOTTED "$service" "$port" "$user_state" "$uid" "$gid" "$snapshot" "$$"
  if ! apply_owned_proxy "$service" "$port"; then
    if proxy_matches_owned "$service" "$port"; then
      restore_snapshot "$service" "$snapshot" || true
    fi
    rm -f "$CURRENT_FILE"
    rm -rf "$snapshot"
    safe_user_marker "$user_state" "system-proxy.failed" "SESSION=$session
REASON=PROXY_APPLY_OR_VERIFY_FAILED" "$uid" "$gid" || true
    log_line "session=$session apply=failed service=$service"
    exit 1
  fi

  write_owner "$session" APPLIED "$service" "$port" "$user_state" "$uid" "$gid" "$snapshot" "$$"
  safe_user_marker "$user_state" "system-proxy.ready" "SESSION=$session
SERVICE=$service
PORT=$port
RESULT=ACTIVE" "$uid" "$gid" || {
    recover_owned_proxy "$session" "$user_state" "$uid" "$gid" || true
    exit 1
  }

  log_line "session=$session apply=success service=$service port=$port"
  guardian_monitor "$session" "$tor_pid" "$service" "$port" "$user_state" "$uid" "$gid"
}''')

replace_once("tunnel/scripts/fetch-tor-bundle.sh", '[ -n "$source_dir" ] && [ -d "$source_dir" ] || { echo "Tor bundle layout not recognized" >&2; exit 1; }', 'if [ -z "$source_dir" ] || [ ! -d "$source_dir" ]; then\n  echo "Tor bundle layout not recognized" >&2\n  exit 1\nfi', "fetch bundle source directory")
replace_once("tunnel/uninstall.sh", '[ -d "$home/Library/Application Support/DevFixTunnel" ] && rm -rf "$home/Library/Application Support/DevFixTunnel" || true;', 'if [ -d "$home/Library/Application Support/DevFixTunnel" ]; then rm -rf "$home/Library/Application Support/DevFixTunnel"; fi;', "uninstall application state purge")
replace_once("tunnel/uninstall.sh", '[ -d "$home/Library/Logs/DevFixTunnel" ] && rm -rf "$home/Library/Logs/DevFixTunnel" || true;', 'if [ -d "$home/Library/Logs/DevFixTunnel" ]; then rm -rf "$home/Library/Logs/DevFixTunnel"; fi;', "uninstall logs purge")

rem = Path("docs/tunnel/remediations")
rem.mkdir(parents=True, exist_ok=True)
(rem / "001_SHELLCHECK_SC2015.md").write_text("# Remediation 001 — SHELLCHECK_SC2015\n\nCI run `31936598799` failed on `SC2015`. Compact ambiguous boolean control flow is replaced by explicit fail-closed conditionals. No tests or safety rules are suppressed.\n")
(rem / "002_WORKFLOW_YAML_PARSE.md").write_text("# Remediation 002 — WORKFLOW_YAML_PARSE\n\nThe first remediation workflow embedded multiline Python in YAML incorrectly. Strategy changed to a standalone Python remediation script.\n")
(rem / "003_REMEDIATION_PATCH_SYNTAX.md").write_text("# Remediation 003 — REMEDIATION_PATCH_SYNTAX\n\nRuns `31936994080` and `31937053678` proved that injecting multiline fragments into legacy one-line shell functions is unsafe. Strategy changed to atomic full-function replacement using locally syntax/integration-tested multiline implementations for `recover_owned_proxy` and `cmd_apply`.\n")
