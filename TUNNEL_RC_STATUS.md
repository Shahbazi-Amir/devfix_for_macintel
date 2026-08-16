# DevFix Tunnel 0.3.0-rc1 — V5 Engineering Status Lock

Date: 2026-08-16

Repository: `Shahbazi-Amir/devfix_for_macintel`

Development branch: `feature/devfix-tunnel`

Stable DevFix branch: `main` — READ-ONLY for Tunnel work

## Release-candidate product identity

Exact validated product/package commit:

`e896afaacc3f3d241577a6614a6e5140166f4536`

This is the exact code identity on which both final official V5 workflows passed and from which the locked V5 artifact was built.

Root-level status/prompt documentation may advance the branch ref after this commit without changing the validated Tunnel product/package bytes. The validated product identity remains the SHA above until any file affecting product, tests, build, package, or workflow gates changes and the gates are rerun.

## Why V5 replaced 0.2.0-rc1

Physical Intel Monterey acceptance of `0.2.0-rc1` proved package identity, installation, runtime presence, doctor, repair safety, and fail-closed proxy behavior. However two controlled real Snowflake sessions both stalled at 10% after broker rendezvous with repeated WebRTC `DataChannel.OnOpen` timeouts.

The old candidate depended on one hard-coded Snowflake bridge definition even though the same official Tor Expert Bundle shipped a maintained `pt_config.json` containing multiple bridge families.

V5 therefore removes the single hard-coded transport dependency and makes the exact packaged Tor bundle the source of truth for the runtime bridge catalog.

## Final official CI gate

Workflow: `DevFix Tunnel CI`

Run ID: `31941348516`

Head SHA: `e896afaacc3f3d241577a6614a6e5140166f4536`

Result: **PASS**

Validated classes include:

- shell syntax: PASS
- ShellCheck without suppressing new findings: PASS
- V5 transport fixture/integration matrix: PASS
- two failed Snowflake candidates followed by successful meek fallback: PASS
- Snowflake WebRTC failure classification: PASS
- per-attempt transport logging: PASS
- fresh attempt state/data isolation: PASS
- Foreign-only torrc policy: PASS
- Iran/unknown exit exclusion configuration: PASS
- preferred exit-country validation: PASS
- `devfix-tunnel exit` fixture verification: PASS
- `devfix-tunnel run` child-only proxy environment: PASS
- System Proxy fail-closed activation: PASS
- same-mode connect idempotency: PASS
- cross-mode transition refusal: PASS
- restart mode preservation: PASS
- existing SOCKS/HTTP/PAC conflict preservation: PASS
- disabled authenticated SOCKS preservation: PASS
- Tor-process death restoration: PASS
- external proxy ownership-loss non-destruction: PASS
- active network-service change restoration: PASS
- guardian root/user marker privilege boundary: PASS
- Selective Chrome exact SOCKS proxy flag: PASS
- Selective Chrome isolated profile: PASS
- Selective Chrome DNS resolver isolation flag: PASS
- Selective Chrome WebRTC non-proxied-UDP restriction: PASS
- Selective Chrome reuses only compatible healthy routes: PASS
- Selective Chrome refuses degraded routes: PASS
- Selective Chrome refuses incompatible exit policy/country: PASS
- Selective Chrome forwards explicit transport/exit options: PASS
- Selective Chrome rejects Foreign-only + Iran conflict: PASS
- Intel macOS command contract: PASS
- full Tunnel fixture tests on Intel macOS runner: PASS
- Selective Chrome tests on Intel macOS runner: PASS
- inherited stable DevFix regression on Ubuntu: PASS
- inherited stable DevFix regression on Intel macOS: PASS

## Final official package gate

Workflow: `DevFix Tunnel Package`

Run ID: `31941348518`

Head SHA: `e896afaacc3f3d241577a6614a6e5140166f4536`

Result: **PASS**

Validated stages include:

- official Tor Expert Bundle acquisition/checksum verification: PASS
- Tor-core-aligned official GeoIP/GeoIPv6 source acquisition/checksum verification: PASS
- bundle-native runtime catalog generation: PASS
- catalog contains >=2 Snowflake, >=1 meek, >=1 obfs4: PASS
- real packaged Tor `--verify-config` for Snowflake + GeoIP + Foreign-only + preferred exit: PASS
- real packaged Tor `--verify-config` for meek + GeoIP + Foreign-only + preferred exit: PASS
- real packaged Tor `--verify-config` for obfs4 + GeoIP + Foreign-only + preferred exit: PASS
- portable archive build: PASS
- macOS x86_64 `.pkg` build: PASS
- artifact hashing: PASS
- package installation smoke test on Intel macOS runner: PASS
- strict fail-closed postinstall recovery path: PASS
- installed `devfix-tunnel` version check: PASS
- installed `devfix-tunnel-chrome` existence/syntax check: PASS
- installed guardian check: PASS
- installed Tor/lyrebird checks: PASS
- installed GeoIP/GeoIPv6 checks: PASS
- installed runtime catalog checks: PASS
- installed recovery LaunchDaemon check: PASS
- installed `devfix-tunnel doctor`: PASS
- real Tor config parser run again against installed package: PASS
- stable DevFix source preservation at `2.0.4`: PASS
- artifact upload: PASS

## Locked V5 artifact identity

GitHub Actions artifact ID:

`9262108863`

Artifact name:

`DevFixTunnel-0.3.0-rc1-macos-x86_64`

GitHub artifact digest / independently downloaded ZIP SHA-256:

`0e4c9d6d3db77b8110deaeec18b98a9efde3f5e97e471c9ec83963b209bd562f`

Contained files and independently verified SHA-256 values:

- `DevFixTunnel-0.3.0-rc1-macos-x86_64.pkg`
  - SHA-256: `4a88daa4eb75ee7c19505e60938683a735830d78072d97d16ce3db91c397f537`
- `DevFixTunnel-0.3.0-rc1-macos-x86_64.tar.gz`
  - SHA-256: `5c37e685d96bb8e4f1d4b6294a63792cf96fbef5199e888010d89b708edd9a4f`
- `SHA256SUMS.txt`
  - SHA-256: `239fa0c63e0985e34786fdd72de1658dc276d3d2719a4b2ee1b5a02889a3dcbf`

Independent `SHA256SUMS.txt` verification against the downloaded artifact contents: **PASS**.

## Independent artifact content audit

The final downloaded artifact was independently inspected after the official workflows passed.

Confirmed inside the delivered V5 bytes:

- product version `0.3.0-rc1`;
- current Tor Expert Bundle runtime;
- transport catalog generated from the exact bundled `pt_config.json`;
- catalog counts: Snowflake `2`, meek `1`, obfs4 `7`;
- old runtime `DEFAULT_SNOWFLAKE_BRIDGE` hard-coded source is absent;
- Tor GeoIP and GeoIPv6 databases are present;
- Tor GeoIP source metadata is present;
- Tor core version for aligned GeoIP source: `0.4.9.11`;
- official Tor source SHA-256 used for GeoIP extraction: `2e6c1720118c812acf0079fd47cf91b6bfaba5d766c321c4d3d2a28d6a11a8ed`;
- Foreign-only configuration support is present;
- `devfix-tunnel exit` is present;
- `devfix-tunnel run` is present;
- Selective Chrome launcher is present;
- Selective Chrome dedicated profile/proxy/DNS/WebRTC controls are present;
- upgrade recovery is fail-closed;
- stable DevFix remains independently versioned and untouched.

## V5 transport behavior

Default connection policy:

```text
transport = auto
exit policy = foreign-only
```

Bounded transport order starts with the current bundle-native candidates:

```text
Snowflake candidate 1
→ Snowflake candidate 2
→ meek_lite candidate 1
→ bounded obfs4 candidates
```

Each candidate receives:

- a fresh Tor process;
- a fresh attempt-specific Tor data directory;
- its own attempt log;
- bounded bootstrap/stall handling.

A failed candidate is stopped before fallback continues.

**macOS System Proxy is not enabled until one candidate reaches Tor bootstrap 100% and routed HTTPS validation succeeds.**

## Exit policy

Default V5 torrc policy includes:

```text
GeoIPExcludeUnknown 1
ExcludeExitNodes {ir},{??}
```

A preferred country may be requested with:

```bash
devfix-tunnel connect --exit-country de
```

The product does not claim a commercial/residential/static IP. Tor path selection and live relay availability still apply, so the live route should be verified with:

```bash
devfix-tunnel exit
```

## Application coverage

### System Proxy

`devfix-tunnel connect system` targets Safari, Chrome, VS Code/Electron, and other software that honors macOS System Proxy.

### Selective Chrome

`devfix-tunnel-chrome` creates/reuses a validated SOCKS-only route and launches a dedicated Chrome/Chromium profile through it while leaving the ordinary Chrome profile and macOS System Proxy unchanged.

The selective process receives:

```text
--proxy-server=socks5://127.0.0.1:<port>
--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1
--force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

This is Chrome over the Tunnel, not Tor Browser and not a claim of Tor Browser anti-fingerprinting.

### Process-scoped CLI

`devfix-tunnel run <command> [args...]` sets `ALL_PROXY`/`all_proxy` only for the child process. It does not edit shell startup files or globally proxy the user's shell.

## Product boundary

`0.3.0-rc1` is **not** a packet-level full-device VPN.

A true full-device macOS implementation remains a separate NetworkExtension / `NEPacketTunnelProvider` milestone requiring a packet-forwarding engine, DNS/IPv4/IPv6 handling, Apple Network Extension entitlement, signing/provisioning, and physical target acceptance.

V5 is intentionally useful now as:

- safe macOS System Proxy circumvention;
- split/selective tunneled Chrome;
- process-scoped CLI routing.

## Network-outage boundary

Multi-transport fallback can improve resilience against censorship, blocked endpoints, restrictive NAT/firewalls, and individual transport failure. It cannot manufacture an external path when the underlying network has zero reachable route to every outside bridge/rendezvous/relay/server.

## Closed engineering failure classes

The following classes were found, root-caused, fixed or correctly bounded, documented, and revalidated where product changes were applicable:

1. `SYSTEM_PROXY_NOT_IMPLEMENTED`
2. `CRASH_CAN_STRAND_PROXY`
3. `PROXY_OWNERSHIP_CONFLICT`
4. `NETWORK_SERVICE_HARDCODING`
5. `SHARED_RUNTIME_COUPLING`
6. `NO_INSTALLER_OR_RECOVERY_DAEMON`
7. `NO_CONFLICT_TEST_MATRIX`
8. `NO_RELEASE_ARTIFACT`
9. `SHELLCHECK_SC2015`
10. `WORKFLOW_YAML_PARSE`
11. `REMEDIATION_PATCH_SYNTAX`
12. `CI_RETRIGGER_SUPPRESSED_BY_GITHUB_TOKEN`
13. `MODE_TRANSITION_NOT_IDEMPOTENT`
14. `RESTART_MODE_DRIFT`
15. `ROOT_USER_STATE_TOCTOU`
16. `DISABLED_AUTHENTICATED_SOCKS_CONFIG`
17. `RESTORE_VERIFICATION_TOO_WEAK`
18. `TEST_STATIC_PATTERN_SC2016`
19. `GITHUB_WORKFLOW_WRITE_PERMISSION`
20. `ARTIFACT_FILE_NOT_FOUND_ACCEPTANCE_CLASSIFICATION`
21. `REAL_SNOWFLAKE_BOOTSTRAP_STALL_10`
22. `SNOWFLAKE_WEBRTC_DATACHANNEL_FAILURE` — addressed by bundle-native bounded multi-transport fallback; physical V5 retest still required
23. `V5_BUILD_SCRIPT_EXEC_BIT`
24. `V5_SHELLCHECK_SC2015_SC2086_SC2016`
25. `SELECTIVE_CHROME_PORT_CAPTURE_STDOUT`
26. `SELECTIVE_CHROME_HEALTH_SHELLCHECK`
27. `UPGRADE_RECOVERY_FAIL_OPEN`

No product security check, restore ownership check, failure classifier, or test was disabled to obtain green CI.

## Only remaining release gate

The only remaining gate before proposing stable `0.3.0` is:

`REAL_TARGET_MAC_ACCEPTANCE_V5`

It must run on the actual Intel x86_64 macOS Monterey 12.7.6 target because CI cannot certify the user's live Iranian network, real bridge reachability, actual current System Proxy state, browser behavior, or physical reboot/orphan recovery.

Mandatory real-target classes:

- exact V5 `.pkg` hash verification;
- safe upgrade from installed `0.2.0-rc1`/current state;
- V5 `doctor` including catalog + GeoIP;
- real `auto` transport fallback behavior;
- real Tor bootstrap 100% + HTTPS route validation;
- live Foreign-only exit verification;
- System Proxy apply/readback;
- Safari HTTPS;
- normal Chrome HTTPS in System mode;
- System Proxy disconnect restoration;
- Selective Chrome split-routing test with ordinary Chrome left direct;
- representative process-scoped CLI test;
- Tor-process death restoration in System mode;
- network-service-change restoration when practical;
- reboot/orphan restoration;
- final safe proxy state.

Until those physical target classes pass, correct label is `0.3.0-rc1`, not stable `0.3.0`.
