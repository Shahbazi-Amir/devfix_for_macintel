# MASTER EXECUTION PROMPT — DEVFIX TUNNEL REAL MAC ACCEPTANCE V4

Repository: `Shahbazi-Amir/devfix_for_macintel`

Branch: `feature/devfix-tunnel`

Release candidate: `0.2.0-rc1`

Validated product/package commit: `3dfbc2219f18102e33c6fa8390070c72676fcb03`

Official CI run: `31937679811` — PASS

Official package run: `31937679804` — PASS

GitHub Actions artifact ID: `9261117695`

Target: actual Intel x86_64 Mac / macOS Monterey 12.x

## Mission

Execute the only remaining release gate on the physical target Mac. Treat repository engineering, static analysis, mocked safety/recovery integration tests, Intel macOS CI contract checks, package build, and package install smoke test as already validated for the exact product identity above.

Do not reopen a solved layer unless new real-Mac evidence directly implicates it.

`main` remains READ-ONLY for Tunnel work.

The release remains `0.2.0-rc1` until every mandatory real-target class passes.

## Exact artifact identity

Install only:

`DevFixTunnel-0.2.0-rc1-macos-x86_64.pkg`

Expected package SHA-256:

`14ce1e763155f457142cadf311079ba9dff8fb81d4ac1d8e8450b2db3d06adff`

Portable archive SHA-256:

`4f212318bee6bd8485fbd3f6d43d66ad771dc617b270483ccf0fea3ce95dd919`

Downloaded GitHub Actions ZIP SHA-256:

`c20de89185b9bf79b86cea444a266da5d01b7f27ce35f044bd930c326aaa8c1b`

If the `.pkg` hash differs:

`STOP — ARTIFACT_IDENTITY_FAILURE`

Do not install or continue.

## Safety preflight

Before installation/connection record, but do not alter just to make the test pass:

- `sw_vers`
- `uname -m`
- current `scutil --proxy`
- current network service/default route
- any intentionally configured VPN/proxy/PAC state

If an unrelated enabled SOCKS/HTTP/HTTPS/PAC/auto-discovery proxy exists, System Proxy mode should fail closed rather than overwrite it.

A disabled but authenticated SOCKS configuration must also be preserved and should classify as `EXISTING_AUTHENTICATED_SOCKS_CONFIG`.

Do not remove unrelated network configuration merely to obtain a PASS.

## Phase A — install + ordinary connection

1. Verify exact package SHA-256.
2. Install the `.pkg` with the normal macOS installer command/UI.
3. Require `devfix-tunnel version` = `0.2.0-rc1`.
4. Require `devfix-tunnel doctor` PASS.
5. Save a pre-connect `scutil --proxy` snapshot.
6. Run `devfix-tunnel connect` and approve the normal administrator authorization request.
7. Require real Snowflake bootstrap to reach 100%.
8. Require routed HTTPS validation to pass.
9. Require status:
   - `State: CONNECTED`
   - `Mode: SYSTEM_PROXY`
   - `Health: OK`
10. Record connected `scutil --proxy` and confirm localhost SOCKS is active for the chosen macOS network service.
11. Run `devfix-tunnel connect` a second time. It must be idempotent and keep the same session instead of creating a new transport/guardian.
12. `devfix-tunnel open https://check.torproject.org/`
13. Confirm Safari can browse HTTPS through the route.
14. Confirm Chrome can browse at least one normal HTTPS page through the route.
15. Run `devfix-tunnel disconnect`.
16. Save post-disconnect `scutil --proxy`.
17. Require previous System Proxy state to match the recorded pre-connect state for fields DevFix Tunnel modified.

## Phase B — Tor process death recovery

1. Connect successfully again.
2. Obtain the Tor PID only from DevFix Tunnel-owned status/state evidence.
3. Terminate only that proven-owned PID.
4. Do not manually change System Proxy while waiting.
5. Require guardian to remove/restore the dead tunnel-owned localhost SOCKS proxy automatically.
6. Require failure classification equivalent to `TOR_PROCESS_DIED`.
7. Run `devfix-tunnel repair`.
8. Require a safe non-stranded System Proxy state.

Never kill a PID whose Tunnel ownership is not proven.

## Phase C — network-service change recovery

If practical on this Mac:

1. Connect successfully.
2. Change the active network service/path in a normal way.
3. Require the old service's tunnel-owned proxy to be restored.
4. Require the old session to stop claiming healthy routing.
5. Require classification equivalent to `NETWORK_SERVICE_CHANGED`.
6. Confirm no external/third-party proxy state was overwritten.
7. Run repair/disconnect as appropriate and return to a safe state.

If the physical Mac has no practical second service/path, report this class as `NOT RUN` with the exact reason; do not fabricate a PASS.

## Phase D — reboot/orphan recovery

1. Connect successfully.
2. Reboot the Mac without running `devfix-tunnel disconnect`.
3. After login, before reconnecting, inspect `scutil --proxy`.
4. Allow the recovery LaunchDaemon interval to run.
5. Require that a stale dead tunnel-owned localhost SOCKS proxy does not remain stranded.
6. Run `devfix-tunnel repair`.
7. Require final safe proxy state.

This physical reboot behavior cannot be certified by CI and is mandatory for stable promotion.

## Failure loop

For any failure:

1. Do not repeat blindly.
2. Preserve exact terminal output.
3. Run `devfix-tunnel logs 200`.
4. Record before/after `scutil --proxy` when relevant.
5. Assign one failure class.
6. Classify layer:
   - artifact/install
   - independent runtime
   - Snowflake bootstrap
   - routed validation
   - active network-service discovery
   - pre-existing proxy conflict
   - System Proxy apply/readback
   - root/user guardian boundary
   - ownership loss
   - restoration
   - browser behavior
   - reboot/orphan recovery
7. Create a remediation note/prompt on `feature/devfix-tunnel`.
8. Fix root cause only on the Tunnel branch.
9. If product/package bytes change, rerun official CI + package workflows and create a new exact artifact identity before retesting the Mac.
10. Re-run the failed real-Mac class plus any earlier regression-critical classes affected by the change.

## Stable promotion gate

Only after all mandatory real-Mac classes pass may `0.2.0-rc1` be promoted to `0.2.0`.

Promotion requires:

- version update to `0.2.0`
- fresh official CI PASS
- fresh package PASS
- fresh artifact SHA-256 lock
- updated engineering status
- no automatic merge into `main` unless the user explicitly authorizes that exact merge/backport

## Security rules

Never:

- disable SIP
- disable Gatekeeper globally
- disable TLS verification
- use permanent `curl -k`
- use `chmod 777`
- request password/token/PAT content in Chat
- kill an unproven PID
- overwrite externally changed proxy settings
- delete third-party proxy configuration to make a test pass
- call System Proxy mode a full packet-level VPN

## Required final report

Report every item as PASS / FAIL / NOT RUN:

- package SHA identity
- package install
- version
- doctor
- real Snowflake 100% bootstrap
- routed validation
- System Proxy apply/readback
- repeated connect idempotency
- Safari
- Chrome
- normal disconnect restoration
- Tor-death restoration
- repair
- network-service-change restoration
- reboot/orphan restoration
- final `scutil --proxy` safe state

Final release decision must be exactly one of:

- `KEEP RC1 — ACCEPTANCE INCOMPLETE`
- `FIX REQUIRED`
- `READY FOR 0.2.0 PROMOTION`

Do not declare stable from CI/package evidence alone.
