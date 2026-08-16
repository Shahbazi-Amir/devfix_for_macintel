#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 match in {path}, found {count}")
    p.write_text(text.replace(old, new, 1))


cli = "tunnel/cli/devfix-tunnel"
replace_once(
    cli,
    'SELF_DIR=$(cd -- "$(dirname -- "$SELF_PATH")" 2>/dev/null && pwd || pwd)',
    'SELF_DIR=$(cd -- "$(dirname -- "$SELF_PATH")" 2>/dev/null && pwd)\nif [ -z "$SELF_DIR" ]; then\n  SELF_DIR=$(pwd)\nfi',
    "cli SELF_DIR",
)
replace_once(
    cli,
    "[ -x /usr/sbin/networksetup ] && printf 'networksetup: OK\\n' || { printf 'networksetup: MISSING\\n'; fail=1; };",
    "if [ -x /usr/sbin/networksetup ]; then printf 'networksetup: OK\\n'; else printf 'networksetup: MISSING\\n'; fail=1; fi;",
    "cli doctor networksetup",
)
replace_once(
    cli,
    "[ -x /sbin/route ] && printf 'route: OK\\n' || { printf 'route: MISSING\\n'; fail=1; };",
    "if [ -x /sbin/route ]; then printf 'route: OK\\n'; else printf 'route: MISSING\\n'; fail=1; fi;",
    "cli doctor route",
)

guardian_path = Path("tunnel/libexec/devfix-tunnel-guardian")
guardian = guardian_path.read_text()
start = guardian.find("recover_owned_proxy() {")
end = guardian.find("\nguardian_monitor() {", start)
if start < 0 or end < 0:
    raise SystemExit("guardian recover_owned_proxy function boundaries not found")
patched_recover = '''recover_owned_proxy() {
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
}
'''
guardian = guardian[:start] + patched_recover + guardian[end:]
guardian_path.write_text(guardian)

replace_once(
    str(guardian_path),
    '[ -n "$user_state" ] && [ -n "$session" ] && [ -n "$tor_pid" ] && [ -n "$port" ] || die "apply requires user-state/session/tor-pid/port";',
    'if [ -z "$user_state" ] || [ -z "$session" ] || [ -z "$tor_pid" ] || [ -z "$port" ]; then\n    die "apply requires user-state/session/tor-pid/port"\n  fi',
    "guardian required apply args",
)

replace_once(
    "tunnel/scripts/fetch-tor-bundle.sh",
    '[ -n "$source_dir" ] && [ -d "$source_dir" ] || { echo "Tor bundle layout not recognized" >&2; exit 1; }',
    'if [ -z "$source_dir" ] || [ ! -d "$source_dir" ]; then\n  echo "Tor bundle layout not recognized" >&2\n  exit 1\nfi',
    "fetch bundle source directory",
)

replace_once(
    "tunnel/uninstall.sh",
    '[ -d "$home/Library/Application Support/DevFixTunnel" ] && rm -rf "$home/Library/Application Support/DevFixTunnel" || true;',
    'if [ -d "$home/Library/Application Support/DevFixTunnel" ]; then rm -rf "$home/Library/Application Support/DevFixTunnel"; fi;',
    "uninstall application state purge",
)
replace_once(
    "tunnel/uninstall.sh",
    '[ -d "$home/Library/Logs/DevFixTunnel" ] && rm -rf "$home/Library/Logs/DevFixTunnel" || true;',
    'if [ -d "$home/Library/Logs/DevFixTunnel" ]; then rm -rf "$home/Library/Logs/DevFixTunnel"; fi;',
    "uninstall logs purge",
)

rem = Path("docs/tunnel/remediations")
rem.mkdir(parents=True, exist_ok=True)
(rem / "001_SHELLCHECK_SC2015.md").write_text(
    "# Remediation 001 — SHELLCHECK_SC2015\n\n"
    "CI run `31936598799` failed on `SC2015`. Compact `A && B || C` control flow was replaced with explicit fail-closed conditionals. Tests and safety rules were not weakened. Closure requires green post-fix CI.\n"
)
(rem / "002_WORKFLOW_YAML_PARSE.md").write_text(
    "# Remediation 002 — WORKFLOW_YAML_PARSE\n\n"
    "The first one-shot remediation workflow escaped YAML indentation because multiline Python was embedded directly in the workflow. The strategy changed to a standalone Python remediation script.\n"
)
(rem / "003_REMEDIATION_PATCH_SYNTAX.md").write_text(
    "# Remediation 003 — REMEDIATION_PATCH_SYNTAX\n\n"
    "Run `31936994080` showed that substring rewriting of a compact one-line shell function produced invalid shell syntax after `fi`. The strategy changed again: the complete `recover_owned_proxy` function is replaced atomically by the already locally syntax/integration-tested multiline implementation. No product test was suppressed.\n"
)
