# Remediation 004 — RC security/idempotency review

Post-green-CI architecture review found four pre-real-Mac failure classes: `MODE_TRANSITION_NOT_IDEMPOTENT`, `RESTART_MODE_DRIFT`, `ROOT_USER_STATE_TOCTOU`, and `DISABLED_AUTHENTICATED_SOCKS_CONFIG`. V4 closes them with explicit same-mode idempotency, fail-closed cross-mode transitions, mode-preserving restart, user-identity marker I/O from the privileged guardian, authenticated dormant SOCKS conflict detection, and stronger restore verification. Existing crash/conflict/network-change tests remain mandatory.
