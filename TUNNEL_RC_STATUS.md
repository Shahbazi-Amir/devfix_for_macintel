# DevFix Tunnel 0.2.0-rc1 — V4 Engineering Status Lock

Date: 2026-08-16

Repository: `Shahbazi-Amir/devfix_for_macintel`

Development branch: `feature/devfix-tunnel`

Stable DevFix branch: `main` — READ-ONLY for Tunnel work

## Release-candidate validated code identity

Validated code/package commit:

`3dfbc2219f18102e33c6fa8390070c72676fcb03`

This is the exact branch code identity on which both official V4 workflows passed and from which the V4 package artifact was built.

Later root-level status/prompt documentation commits may advance the branch ref without changing the validated Tunnel product/package bytes. The validated product identity remains the SHA above until product bytes change and both gates are rerun.

## Official CI gate

Workflow: `DevFix Tunnel CI`

Run ID: `31937679811`

Head SHA: `3dfbc2219f18102e33c6fa8390070c72676fcb03`

Result: PASS

Validated jobs/classes:

- Tunnel shell syntax: PASS
- ShellCheck: PASS
- full Tunnel System Proxy fixture/integration matrix: PASS
- same-mode connect idempotency: PASS
- cross-mode transition refusal/non-destruction: PASS
- restart mode preservation: PASS
- existing SOCKS conflict preservation: PASS
- existing HTTP conflict preservation: PASS
- disabled authenticated SOCKS configuration fail-closed preservation: PASS
- Tor-process death restoration: PASS
- external proxy ownership-loss preservation: PASS
- active network-service change restoration: PASS
- guardian user-marker privilege-boundary assertion: PASS
- Intel macOS `networksetup`/`route` command contract: PASS
- Intel macOS target-UID privilege-drop command form: PASS
- Tunnel integration tests on Intel macOS runner: PASS
- inherited stable DevFix regression on Ubuntu: PASS
- inherited stable DevFix regression on Intel macOS: PASS

## Package gate

Workflow: `DevFix Tunnel Package`

Run ID: `31937679804`

Head SHA: `3dfbc2219f18102e33c6fa8390070c72676fcb03`

Result: PASS

Validated stages:

- official Tor Expert Bundle acquisition/checksum pipeline: PASS
- portable archive build: PASS
- macOS x86_64 `.pkg` build: PASS
- artifact hashing: PASS
- `.pkg` install smoke test on Intel macOS runner: PASS
- installed `devfix-tunnel` version check: PASS
- installed guardian version check: PASS
- packaged Tor/lyrebird executable checks: PASS
- LaunchDaemon installation check: PASS
- installed `devfix-tunnel doctor`: PASS
- stable DevFix source preservation: PASS
- artifact upload: PASS

## V4 artifact identity

GitHub Actions artifact ID:

`9261117695`

Artifact name:

`DevFixTunnel-0.2.0-rc1-macos-x86_64`

GitHub artifact digest / independently downloaded ZIP SHA-256:

`c20de89185b9bf79b86cea444a266da5d01b7f27ce35f044bd930c326aaa8c1b`

Contained files and independently re-verified SHA-256 values:

- `DevFixTunnel-0.2.0-rc1-macos-x86_64.pkg`
  - SHA-256: `14ce1e763155f457142cadf311079ba9dff8fb81d4ac1d8e8450b2db3d06adff`
- `DevFixTunnel-0.2.0-rc1-macos-x86_64.tar.gz`
  - SHA-256: `4f212318bee6bd8485fbd3f6d43d66ad771dc617b270483ccf0fea3ce95dd919`
- `SHA256SUMS.txt`

Independent verification after downloading the GitHub Actions artifact:

`sha256sum -c SHA256SUMS.txt` = PASS for both `.pkg` and `.tar.gz`.

## Closed engineering failure classes

The following failure classes were found, root-caused, fixed, documented, and revalidated:

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

No product test, security rule, ownership check, or restore check was suppressed or weakened to make CI green.

## V4 hardening guarantees before real-Mac acceptance

- same-mode reconnect is idempotent;
- SOCKS/System cross-mode switching requires explicit disconnect;
- restart preserves current mode unless explicitly overridden;
- System Proxy operations remain fail-closed on third-party proxy conflicts;
- dormant authenticated SOCKS state is not overwritten;
- privileged guardian marker file I/O is delegated to the validated target user identity in production;
- only tunnel-owned proxy state is eligible for automatic restoration;
- externally changed proxy state is not blindly overwritten;
- previous observable SOCKS enabled/server/port state is checked during restoration;
- independent Tor/lyrebird runtime is packaged under the Tunnel namespace;
- stable DevFix remains separate and regression-tested.

## Product boundary

This release candidate is a safe **macOS System Proxy circumvention product** for Safari, Chrome, and other applications that honor macOS System Proxy settings.

It is not a packet-level full-device VPN and must not be marketed or reported as one.

A future true full-device VPN is a separate NetworkExtension / packet-tunnel milestone.

## Only remaining release gate

The only remaining gate before proposing promotion from `0.2.0-rc1` to stable `0.2.0` is:

`REAL_TARGET_MAC_ACCEPTANCE`

It must run on the actual Intel x86_64 macOS Monterey target because GitHub Actions cannot certify the user's real network/Snowflake behavior, actual current macOS proxy configuration, Safari/Chrome behavior, sleep/network transitions, or reboot/orphan restoration on that physical machine.

Required real-Mac acceptance classes:

- exact `.pkg` SHA verification
- installation
- `doctor`
- real Snowflake bootstrap and route validation
- System Proxy apply/readback
- Safari HTTPS browsing
- Chrome HTTPS browsing
- normal disconnect restoration
- repeated same-mode connect behavior
- Tor-process death automatic proxy restoration
- network-service-change restoration when practical
- reboot/orphan recovery
- final safe proxy state

Until those classes pass, correct release label is `0.2.0-rc1`, not stable `0.2.0`.
