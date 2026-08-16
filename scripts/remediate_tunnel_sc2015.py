#!/usr/bin/env python3
from pathlib import Path
import re


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

guardian = "tunnel/libexec/devfix-tunnel-guardian"
p = Path(guardian)
text = p.read_text()
pattern = re.compile(
    r'''\[ -f "\$CURRENT_FILE" \] \|\| \{ \[ -n "\$marker_user_state" \] && safe_user_marker "\$marker_user_state" "system-proxy\.restored" "SESSION=\$\{requested_session:-none\}\nRESULT=NO_OWNED_PROXY" "\$marker_uid" "\$marker_gid" \|\| true; return 0; \};'''
)
replacement = (
    'if [ ! -f "$CURRENT_FILE" ]; then\n'
    '    if [ -n "$marker_user_state" ]; then\n'
    '      safe_user_marker "$marker_user_state" "system-proxy.restored" '
    '"SESSION=${requested_session:-none}\\nRESULT=NO_OWNED_PROXY" '
    '"$marker_uid" "$marker_gid" || true\n'
    '    fi\n'
    '    return 0\n'
    '  fi'
)
text2, n = pattern.subn(lambda _: replacement, text, count=1)
if n != 1:
    raise SystemExit(f"guardian recover no-current: expected 1 match, found {n}")
p.write_text(text2)
replace_once(
    guardian,
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

Path("docs/tunnel/remediations").mkdir(parents=True, exist_ok=True)
Path("docs/tunnel/remediations/001_SHELLCHECK_SC2015.md").write_text(
    "# Remediation 001 — SHELLCHECK_SC2015\n\n"
    "## Failure\n\n"
    "CI run `31936598799` failed the Tunnel ShellCheck gate on `SC2015`.\n\n"
    "## Root cause\n\n"
    "Several compact shell expressions used `A && B || C`, which is ambiguous control flow because C can execute if B fails even when A succeeds.\n\n"
    "## Fix\n\n"
    "All flagged sites are converted to explicit fail-closed `if/then/else` control flow. No test, ownership rule, restore rule, conflict rule, or security gate is weakened.\n\n"
    "## Validation\n\n"
    "Syntax, ShellCheck, unchanged Tunnel integration tests, Intel macOS command-contract tests, inherited DevFix regression, and packaging must all pass before this failure class is closed.\n"
)

Path("docs/tunnel/remediations/002_WORKFLOW_YAML_PARSE.md").write_text(
    "# Remediation 002 — WORKFLOW_YAML_PARSE\n\n"
    "The first one-shot remediation workflow produced no jobs because multiline Python content escaped the YAML block indentation. The strategy was changed: remediation logic now lives in `scripts/remediate_tunnel_sc2015.py`, and YAML only invokes the script. No product code or tests were weakened to work around the workflow failure.\n"
)
