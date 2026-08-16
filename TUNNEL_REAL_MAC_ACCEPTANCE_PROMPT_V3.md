# MASTER EXECUTION PROMPT — DEVFIX TUNNEL REAL MAC ACCEPTANCE V3

Repository: `Shahbazi-Amir/devfix_for_macintel`

Branch: `feature/devfix-tunnel`

Release candidate: `0.2.0-rc1`

Validated code commit: `4399864d5e9e4f677cc6ef4fff24cbec5d5f8423`

Target: actual Intel x86_64 Mac / macOS Monterey 12.x

## Mission

Execute the final physical-Mac acceptance gate without changing `main`. Treat GitHub/CI/package engineering as already validated. Do not reopen solved layers unless new evidence directly implicates them.

The release must remain `0.2.0-rc1` until every required real-target gate has passed.

## Exact package identity

Install only:

`DevFixTunnel-0.2.0-rc1-macos-x86_64.pkg`

Expected SHA-256:

`706180e2cbb85cecb60a777f0603555e7dbbd069a749a5af25e84cf38601f616`

If the hash differs:

`STOP — ARTIFACT_IDENTITY_FAILURE`

Do not install.

## Before installation

Record but do not change:

- macOS version
- architecture
- `scutil --proxy`
- current active network service
- existing VPN/proxy state
- current DevFix status if relevant

If an unrelated third-party SOCKS/HTTP/HTTPS/PAC proxy is already active, do not silently overwrite it. DevFix Tunnel should fail closed in System Proxy mode; that is expected safety behavior, not a reason to delete the user's existing network configuration.

## Basic acceptance sequence

1. Verify package SHA-256.
2. Install with normal macOS `installer` flow.
3. Verify `devfix-tunnel version` reports `0.2.0-rc1`.
4. Run `devfix-tunnel doctor`.
5. Record `scutil --proxy` before connection.
6. Run `devfix-tunnel connect` and allow administrator authorization when macOS asks.
7. Require real Snowflake bootstrap to reach 100% and routed validation to pass.
8. Require `devfix-tunnel status` to show:
   - `State: CONNECTED`
   - `Mode: SYSTEM_PROXY`
   - `Health: OK`
9. Record `scutil --proxy` while connected and verify the active service is using tunnel-owned localhost SOCKS.
10. Open `https://check.torproject.org/` through `devfix-tunnel open` and verify Safari browsing.
11. Verify at least one normal HTTPS page in Chrome.
12. Run `devfix-tunnel disconnect`.
13. Require previous System Proxy state to be restored; compare with the recorded pre-connect state.

## Safety acceptance sequence

### Tor crash recovery

- Connect successfully.
- Obtain the Tor PID only from `devfix-tunnel status`/owned state.
- Terminate only that owned PID.
- Wait for guardian recovery.
- Require the dead localhost SOCKS System Proxy to be removed/restored automatically.
- Require a failure marker/classification equivalent to `TOR_PROCESS_DIED`.
- Run `devfix-tunnel repair` and require a clean safe state.

### Network-service change

If practical, while connected change the active network service/network path (for example Wi-Fi to another available service) without altering unrelated security configuration.

Require:

- old service tunnel-owned proxy restored;
- session no longer claims healthy routing;
- failure classification equivalent to `NETWORK_SERVICE_CHANGED`;
- no third-party proxy overwritten.

### Reboot/orphan recovery

- Connect successfully.
- Reboot without running `disconnect`.
- After login, inspect `scutil --proxy` before reconnecting.
- The recovery LaunchDaemon must prevent a stale dead tunnel-owned localhost SOCKS proxy from remaining active after boot/recovery interval.
- Run `devfix-tunnel repair` and verify clean state.

## Failure loop

For any failure:

1. Capture exact command/output and `devfix-tunnel logs 200`.
2. Assign one failure class.
3. Determine whether the failed layer is:
   - artifact/install
   - independent runtime
   - Snowflake bootstrap
   - route validation
   - network-service discovery
   - proxy conflict
   - proxy apply/readback
   - guardian ownership
   - restoration
   - browser behavior
   - reboot recovery
4. Do not retry blindly.
5. Create a remediation prompt/note in the Tunnel branch.
6. Fix only `feature/devfix-tunnel`; `main` remains read-only.
7. Run CI + package workflows again if product bytes change.
8. Produce a new release-candidate artifact if package bytes change.
9. Re-run the affected real-Mac acceptance class plus regression-critical earlier classes.

## Stable promotion gate

Only after all real-Mac acceptance classes are PASS may version promotion to stable `0.2.0` be proposed.

Stable promotion must include:

- version update from `0.2.0-rc1` to `0.2.0`
- fresh CI PASS
- fresh package PASS
- new artifact hashes
- updated status record
- no automatic merge into `main` unless explicitly authorized by the user

## Security rules

Never:

- disable SIP
- disable Gatekeeper globally
- disable TLS verification
- use permanent `curl -k`
- use `chmod 777`
- request passwords/tokens in Chat
- kill a PID whose Tunnel ownership is not proven
- overwrite externally changed proxy settings
- call System Proxy mode a full packet-level VPN

## Final required report

Report:

- package SHA verification
- install PASS/FAIL
- doctor PASS/FAIL
- Snowflake bootstrap PASS/FAIL
- route validation PASS/FAIL
- System Proxy apply/readback PASS/FAIL
- Safari PASS/FAIL
- Chrome PASS/FAIL
- disconnect restore PASS/FAIL
- Tor-crash restore PASS/FAIL
- network-change restore PASS/FAIL/NOT RUN with reason
- reboot/orphan recovery PASS/FAIL
- final `scutil --proxy` safe-state result
- release decision: `KEEP RC1`, `FIX REQUIRED`, or `READY FOR 0.2.0 PROMOTION`

Do not declare stable based only on CI or package smoke tests.
