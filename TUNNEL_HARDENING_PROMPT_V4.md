# MASTER EXECUTION PROMPT — DEVFIX TUNNEL RC HARDENING V4

Repository: `Shahbazi-Amir/devfix_for_macintel`

Write branch: `feature/devfix-tunnel`

Stable branch: `main` — READ-ONLY

Release line: `0.2.0-rc1`

## Mission

Do not hand the release candidate to the real Intel Monterey target until the post-CI architecture review failure classes below are closed without weakening existing tests.

## Failure class A — MODE_TRANSITION_NOT_IDEMPOTENT

Repeated `connect system` must be an idempotent no-op for a healthy existing System Proxy session. Repeated `connect socks` must be an idempotent no-op for a healthy SOCKS-only session.

Switching between `SOCKS` and `SYSTEM_PROXY` while connected must fail closed with an explicit instruction to disconnect first. It must never silently orphan an old Tor process, launch a second guardian for the same session, or misreport SOCKS-only mode while System Proxy remains active.

`start_transport` must terminate only proven-owned stale/non-system Tor processes before clearing runtime state. It must never stop a potentially active System Proxy transport before proxy recovery.

## Failure class B — RESTART_MODE_DRIFT

`devfix-tunnel restart` with no explicit mode must preserve the currently connected mode. Explicit `restart system` and `restart socks` remain supported.

## Failure class C — ROOT_USER_STATE_TOCTOU

The privileged guardian must not open/write/remove user-controlled marker paths with root file privileges.

Production marker operations must drop to the validated target UID before opening user-controlled paths. The root helper may validate path ownership as root, but marker file content I/O and removal must occur as the user identity so a user-controlled symlink race cannot turn marker handling into an arbitrary root file write/remove/read primitive.

Test mode may use direct local fixture I/O because no root privilege exists there.

## Failure class D — DISABLED_AUTHENTICATED_SOCKS_CONFIG

A disabled but authenticated pre-existing SOCKS configuration may contain credentials/state that DevFix Tunnel cannot losslessly reconstruct. System Proxy mode must fail closed rather than overwrite it.

Required classification:

`EXISTING_AUTHENTICATED_SOCKS_CONFIG`

Normal disabled, unauthenticated SOCKS server/port state may be temporarily replaced only if exact server/port/enabled restoration is verified.

## Restore verification

Restoration must verify not only enabled/disabled state but also the prior SOCKS server and numeric port when those values existed. The guardian must never claim RESTORED if the observable restored configuration does not match the captured snapshot for fields DevFix Tunnel modified.

## Tests to add

- repeated System Proxy `connect system` is idempotent and keeps the same session
- repeated SOCKS-only `connect socks` is idempotent
- `system -> socks` transition without disconnect is refused and non-destructive
- `socks -> system` transition without disconnect is refused and non-destructive
- `restart` preserves current SOCKS mode by default
- disabled authenticated SOCKS configuration is refused and preserved
- existing conflict/crash/network-change tests remain unchanged and PASS
- root/user marker implementation is statically checked for privilege-drop mechanism
- ShellCheck and syntax remain clean
- Intel macOS command contract validates the privilege-drop command form used by the guardian
- inherited stable DevFix regressions remain PASS
- package build/install must be rerun after hardening

## Execution rule

For any new failure, assign a failure class, document root cause, change strategy rather than blindly retry, and continue until both official `DevFix Tunnel CI` and `DevFix Tunnel Package` pass on the same post-hardening code identity.

Only after artifact hashes are re-verified may `REAL_TARGET_MAC_ACCEPTANCE` become the sole remaining gate.
