# MASTER EXECUTION PROMPT — DEVFIX TUNNEL REAL MAC ACCEPTANCE V5

Date: 2026-08-16

Repository: `Shahbazi-Amir/devfix_for_macintel`

Branch: `feature/devfix-tunnel`

Stable branch: `main` — READ-ONLY for Tunnel work

Release candidate: `0.3.0-rc1`

Exact validated product/package commit:

`e896afaacc3f3d241577a6614a6e5140166f4536`

Official CI run:

`31941348516` — PASS

Official Package run:

`31941348518` — PASS

GitHub Actions artifact ID:

`9262108863`

Target:

Actual Intel x86_64 Mac / macOS Monterey 12.7.6.

## Mission

Execute the only remaining release gate on the physical target Mac for the exact locked V5 package artifact.

Treat repository engineering, static analysis, mocked safety/recovery tests, real packaged-Tor configuration parsing, Intel macOS CI, package construction, package installation smoke testing, and artifact integrity as already validated for the exact product SHA above.

Do not reopen a solved layer unless physical-Mac evidence directly implicates it.

Do not change `main`.

Do not promote the version to stable until all mandatory physical acceptance classes pass.

## Exact artifact identity

Install only:

`DevFixTunnel-0.3.0-rc1-macos-x86_64.pkg`

Expected package SHA-256:

`4a88daa4eb75ee7c19505e60938683a735830d78072d97d16ce3db91c397f537`

Expected portable archive SHA-256:

`5c37e685d96bb8e4f1d4b6294a63792cf96fbef5199e888010d89b708edd9a4f`

Expected GitHub Actions ZIP SHA-256:

`0e4c9d6d3db77b8110deaeec18b98a9efde3f5e97e471c9ec83963b209bd562f`

If the `.pkg` is missing, classify:

`ARTIFACT_FILE_NOT_FOUND`

If the file exists but the hash differs, classify:

`ARTIFACT_IDENTITY_FAILURE`

Do not install a hash-mismatched package.

## Known physical-Mac history

The target previously installed `0.2.0-rc1` successfully. Its package/hash/version/doctor gates passed, but two controlled Snowflake attempts stalled at 10% with repeated WebRTC `DataChannel.OnOpen` failures.

The old candidate correctly left macOS System Proxy unchanged, Tor stopped cleanly, repair succeeded, and the original proxy state remained safe.

V5 is specifically designed to eliminate dependence on that single transport path by using the exact current Tor Expert Bundle bridge catalog and bounded fallback.

## V5 transport policy to verify

Default connection uses:

```text
transport = auto
exit policy = foreign-only
```

Expected bounded family order begins:

```text
Snowflake candidate 1
→ Snowflake candidate 2
→ meek_lite candidate 1
→ bounded obfs4 candidate(s)
```

A Snowflake `DataChannel.OnOpen` failure is allowed to occur. The user must not manually retry or intervene while V5 auto-fallback is progressing.

A failed candidate must be stopped before the next candidate starts.

macOS System Proxy must remain untouched until one transport candidate:

1. reaches Tor bootstrap 100%; and
2. passes routed HTTPS validation.

If Snowflake still fails but meek/obfs4 succeeds automatically, this is a V5 success for the old real failure class.

## Safety preflight before upgrade

Record, but do not alter merely to make the test pass:

- `sw_vers`
- `uname -m`
- current `scutil --proxy`
- current `devfix-tunnel status`
- any currently running DevFix Tunnel Tor process
- any intentionally configured third-party SOCKS/HTTP/HTTPS/PAC/VPN state

The V5 installer is fail-closed:

- it must refuse to replace Tunnel runtime files while a Tunnel Tor process is active;
- old guardian recovery must succeed before upgrade;
- new guardian recovery must succeed after upgrade;
- the recovery LaunchDaemon must activate successfully.

Do not force-kill unrelated PIDs to make upgrade proceed.

If the old Tunnel is in a stale/degraded state, use its normal `repair` path and verify proxy safety before retrying installation.

## Phase A — exact package upgrade and V5 preflight

1. Verify exact package SHA-256.
2. Record `scutil --proxy` before install.
3. Verify no active Tunnel Tor runtime is serving a live session.
4. Install/upgrade the `.pkg` through the normal macOS installer flow.
5. Require:
   - `devfix-tunnel version` = `0.3.0-rc1`;
   - `devfix-tunnel doctor` PASS;
   - doctor reports Tor runtime OK;
   - lyrebird OK;
   - transport catalog OK with at least 2 Snowflake, 1 meek and 1 obfs4;
   - GeoIP IPv4 OK;
   - GeoIP IPv6 OK;
   - guardian/networksetup/route/sudo OK.
6. Verify `devfix-tunnel-chrome` exists and responds to `--help`.
7. Confirm pre-connect `scutil --proxy` still matches the recorded safe state.

## Phase B — real default System Proxy / auto-fallback

1. Save a fresh pre-connect `scutil --proxy` snapshot.
2. Run:

```bash
devfix-tunnel connect
```

3. Do not interrupt normal auto-fallback merely because a Snowflake candidate reports a bounded failure.
4. Require eventual success from one catalog candidate.
5. Require the successful candidate to reach bootstrap 100% and routed HTTPS validation PASS before System Proxy activation.
6. Require:

```text
State: CONNECTED
Mode: SYSTEM_PROXY
Health: OK
Transport: <actual winning family/candidate>
Exit policy: FOREIGN_ONLY
```

7. Save connected `scutil --proxy`.
8. Confirm the selected active macOS network service uses the tunnel-owned localhost SOCKS proxy.
9. Run a second identical `devfix-tunnel connect`; require idempotent reuse rather than a second session/guardian.
10. Run:

```bash
devfix-tunnel exit
```

11. Require:
   - Tor Check recognizes the route as Tor;
   - a public Tor exit IP is reported;
   - exit country is known when local IPv4 GeoIP mapping is possible;
   - Foreign-only verification is PASS;
   - Iran must not be accepted as a valid Foreign-only exit.
12. Open Tor Check through `devfix-tunnel open` and verify Safari HTTPS browsing.
13. Verify ordinary Chrome HTTPS browsing while System Proxy mode is active.
14. Run normal disconnect.
15. Compare post-disconnect proxy state with pre-connect state for all fields DevFix Tunnel owns/modifies.
16. Require no dead localhost SOCKS System Proxy to remain.

## Phase C — preferred foreign exit test

After a clean disconnect, test one preferred foreign country, initially `de`:

```bash
devfix-tunnel connect --exit-country de
```

Requirements:

- connection still uses bounded auto transport fallback;
- Foreign-only remains enabled;
- status reports preferred exit country `de`;
- `devfix-tunnel exit` reports the live exit identity.

Do not treat Tor `ExitNodes` preference as a commercial VPN guarantee. If the exact preferred country is unavailable but the route remains safely foreign and Tor configuration is valid, record the live behavior truthfully rather than fabricating a country match.

Disconnect and require proxy restoration again.

## Phase D — Selective Chrome split-routing acceptance

Goal: prove the user can have ordinary Chrome direct and a separate tunneled Chrome without changing macOS System Proxy.

1. Begin DISCONNECTED with a safe `scutil --proxy` snapshot.
2. In ordinary Chrome, record a normal direct public-IP observation using a normal IP-check service of the user's choice. Do not persist this IP in repository logs.
3. Launch:

```bash
devfix-tunnel-chrome https://check.torproject.org/
```

4. If no Tunnel route exists, the launcher must establish SOCKS-only `auto` + Foreign-only routing.
5. Require `devfix-tunnel status` to show:

```text
State: CONNECTED
Mode: SOCKS
Health: OK
```

6. Require `scutil --proxy` to remain equal to the pre-launch System Proxy snapshot.
7. The isolated Chrome profile must open through Tor.
8. Ordinary Chrome must remain direct/unmodified by this launcher.
9. Verify the isolated Chrome profile is separate from the ordinary Chrome profile.
10. Optional country-control acceptance:

```bash
devfix-tunnel disconnect
devfix-tunnel-chrome --exit-country de https://check.torproject.org/
```

11. Require incompatible/degraded existing Tunnel routes to be refused rather than silently reused.
12. Disconnect after the selective test.

Important: Selective Chrome is Chrome over Tor. It is not Tor Browser and does not claim Tor Browser anti-fingerprinting protections.

## Phase E — process-scoped CLI acceptance

Goal: cover developer applications/CLI tools without globally changing the user's shell.

1. Start SOCKS-only mode or reuse a healthy compatible SOCKS route.
2. Run a representative child command through:

```bash
devfix-tunnel run <command> [args...]
```

3. Confirm the child receives the Tunnel SOCKS route and can reach a target that requires the routed path.
4. Confirm `ALL_PROXY`/`all_proxy` were not permanently written into shell startup files or global user environment.
5. When System Proxy mode is not active, a separately executed ordinary direct command must remain outside the process-scoped wrapper.
6. Disconnect safely.

## Phase F — Tor process death recovery in System Proxy mode

1. Connect successfully in System Proxy mode.
2. Obtain the Tor PID only from DevFix Tunnel-owned status/state evidence.
3. Prove ownership before any termination.
4. Terminate only that owned Tor PID.
5. Do not manually edit macOS proxy settings while waiting.
6. Require the guardian to restore/remove the dead tunnel-owned localhost proxy automatically.
7. Require failure classification equivalent to `TOR_PROCESS_DIED`.
8. Run `devfix-tunnel repair`.
9. Require a safe, non-stranded System Proxy state.

Never kill a PID whose Tunnel ownership is not proven.

## Phase G — network-service change recovery

If practical on the physical Mac:

1. Connect successfully in System Proxy mode.
2. Change the active network path/service normally, for example between available Wi-Fi/Ethernet/hotspot paths.
3. Require the old network service's tunnel-owned proxy to be restored.
4. Require the old session to stop claiming healthy routing.
5. Require classification equivalent to `NETWORK_SERVICE_CHANGED`.
6. Confirm no third-party proxy state was overwritten.
7. Repair/disconnect as appropriate and return to a safe state.

If no practical second service exists, report `NOT RUN` with the exact reason. Do not fabricate a PASS.

## Phase H — reboot/orphan recovery

1. Connect successfully in System Proxy mode.
2. Reboot without running normal `disconnect`.
3. After login, before reconnecting, inspect `scutil --proxy`.
4. Allow the recovery LaunchDaemon interval to run.
5. Require a stale dead tunnel-owned localhost SOCKS proxy not to remain stranded.
6. Run `devfix-tunnel repair` if state cleanup is still needed.
7. Require final safe proxy state.

This physical reboot behavior cannot be certified by GitHub Actions and is mandatory before stable promotion.

## Failure loop

For every physical failure:

1. Do not blindly repeat the same attempt.
2. Preserve exact command/output.
3. Capture `devfix-tunnel status`.
4. Capture `devfix-tunnel logs 300`.
5. Capture `scutil --proxy` when proxy state is relevant.
6. Assign a single primary failure class.
7. Classify the layer:
   - artifact/install/upgrade
   - bundled runtime/catalog/GeoIP
   - Snowflake WebRTC/broker
   - meek
   - obfs4
   - auto-fallback orchestration
   - bootstrap
   - routed validation
   - exit policy/verification
   - active network-service discovery
   - pre-existing proxy conflict
   - System Proxy apply/readback
   - guardian ownership/restore
   - Selective Chrome
   - process-scoped CLI
   - browser behavior
   - reboot/orphan recovery
8. Add a remediation note/prompt on `feature/devfix-tunnel`.
9. Fix the root cause only on the Tunnel branch.
10. If any product/package/build/workflow byte changes, rerun the official CI + package gates and lock a new exact artifact identity before asking for another physical test.
11. Re-run the failed physical class plus earlier regression-critical classes affected by the fix.

## Full-device VPN boundary

Do not turn physical acceptance of System Proxy/Selective Chrome/CLI modes into a false claim of a packet-level VPN.

A true full-device VPN remains the separate NetworkExtension / `NEPacketTunnelProvider` milestone described in:

`docs/tunnel/FULL_DEVICE_VPN_ROADMAP.md`

That milestone requires Apple Network Extension entitlement/signing/provisioning and a packet-forwarding/DNS/IPv4/IPv6 design before physical deployment can be called a full-device VPN.

## Network outage boundary

Do not claim that V5 can create Internet access if the underlying access network has literally zero reachable route to every outside bridge/rendezvous/relay/server.

V5 multi-transport fallback is designed to improve resilience when some censorship paths/protocols/endpoints fail, not to violate a total upstream disconnection.

## Security rules

Never:

- disable SIP;
- disable Gatekeeper globally;
- disable TLS verification;
- use permanent `curl -k`;
- use `chmod 777`;
- request passwords/PAT/tokens in Chat;
- kill an unproven PID;
- overwrite externally changed proxy settings;
- delete third-party proxy/PAC configuration merely to make a test pass;
- globally edit shell startup proxy variables for process-scoped routing;
- call current V5 a packet-level full-device VPN.

## Stable promotion gate

Only after all mandatory physical V5 classes PASS may `0.3.0-rc1` be promoted to stable `0.3.0`.

Stable promotion requires:

- physical acceptance record;
- version update to `0.3.0`;
- fresh official CI PASS;
- fresh package PASS;
- fresh exact artifact hashes;
- updated engineering status lock;
- no automatic merge into `main` unless the user explicitly authorizes that exact merge/backport.

## Required final report

Report each as PASS / FAIL / NOT RUN:

- exact V5 package identity;
- safe upgrade from installed old candidate;
- version;
- doctor/catalog/GeoIP;
- real auto transport fallback;
- winning real transport/candidate;
- Tor 100% bootstrap;
- routed HTTPS validation;
- Foreign-only exit verification;
- preferred-country behavior;
- System Proxy apply/readback;
- repeated-connect idempotency;
- Safari;
- ordinary Chrome in System mode;
- normal System Proxy disconnect restoration;
- Selective Chrome split-routing;
- ordinary Chrome remains direct during Selective Chrome test;
- process-scoped CLI routing;
- Tor-death restoration;
- repair;
- network-service-change restoration;
- reboot/orphan restoration;
- final `scutil --proxy` safe state.

Final decision must be exactly one of:

- `KEEP 0.3.0-rc1 — ACCEPTANCE INCOMPLETE`
- `FIX REQUIRED`
- `READY FOR 0.3.0 PROMOTION`

Do not declare stable from CI/package evidence alone.
