# DevFix Tunnel 0.2.0-rc1 — Engineering Status Lock

Date: 2026-08-16

Repository: `Shahbazi-Amir/devfix_for_macintel`

Development branch: `feature/devfix-tunnel`

Stable DevFix branch: `main` — READ-ONLY for Tunnel work

## Release-candidate code identity

Validated release-candidate code/docs commit:

`4399864d5e9e4f677cc6ef4fff24cbec5d5f8423`

This commit contains the post-remediation Tunnel implementation and the intentional validation-gate documentation write that retriggered GitHub Actions after the remediation commit was pushed by `GITHUB_TOKEN`.

## Official CI gate

Workflow: `DevFix Tunnel CI`

Run ID: `31937195189`

Result: PASS

Validated jobs:

- Tunnel syntax: PASS
- ShellCheck: PASS
- Tunnel System Proxy fixture/integration tests: PASS
- Intel macOS command contract: PASS
- Tunnel integration tests on Intel macOS runner: PASS
- inherited stable DevFix regression on Ubuntu: PASS
- inherited stable DevFix regression on Intel macOS: PASS

## Package gate

Workflow: `DevFix Tunnel Package`

Run ID: `31937195201`

Result: PASS

Validated stages:

- official Tor Expert Bundle acquisition/checksum pipeline: PASS
- portable archive build: PASS
- macOS x86_64 `.pkg` build: PASS
- artifact hashing: PASS
- package installation smoke test on Intel macOS runner: PASS
- installed `devfix-tunnel` version check: PASS
- installed guardian version check: PASS
- packaged Tor/lyrebird executable checks: PASS
- LaunchDaemon installation check: PASS
- `devfix-tunnel doctor`: PASS
- stable DevFix source preservation: PASS
- artifact upload: PASS

## Artifact identity

GitHub Actions artifact ID: `9260987956`

Artifact name:

`DevFixTunnel-0.2.0-rc1-macos-x86_64`

Artifact ZIP SHA-256:

`41da15b8765dff06ba6e1d05da1d8506e524ffc90ef02c5f8cc4abdb1c12a0f8`

Contained files and independently re-verified SHA-256 values:

- `DevFixTunnel-0.2.0-rc1-macos-x86_64.pkg`
  - SHA-256: `706180e2cbb85cecb60a777f0603555e7dbbd069a749a5af25e84cf38601f616`
- `DevFixTunnel-0.2.0-rc1-macos-x86_64.tar.gz`
  - SHA-256: `e92bfb0bb01ac50c100c5e30fc266cc974414db97dc75e87178451daf7b5803e`
- `SHA256SUMS.txt`

`sha256sum -c SHA256SUMS.txt` against the downloaded artifact contents: PASS.

## Closed engineering failure classes

The following issues were identified, documented, fixed, and revalidated:

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

No test was suppressed or weakened to obtain green CI.

## Product boundary

This release candidate implements safe **macOS System Proxy mode** over the independent DevFix Tunnel Snowflake/Tor runtime for Safari, Chrome, and other proxy-aware applications.

It is not represented as a packet-level full-device VPN.

A future true full-device VPN remains a separate NetworkExtension/packet-tunnel milestone.

## Remaining release gate

The only remaining gate before promoting `0.2.0-rc1` to stable `0.2.0` is:

`REAL_TARGET_MAC_ACCEPTANCE`

It must run on the actual Intel x86_64 macOS Monterey target because GitHub Actions cannot certify the user's real network, Snowflake session behavior, current System Proxy state, Safari/Chrome behavior, sleep/network transitions, or reboot/orphan restoration on that physical Mac.

Required real-Mac acceptance classes:

- install `.pkg`
- `doctor`
- real Snowflake bootstrap and validation
- System Proxy apply/readback
- Safari browsing
- Chrome browsing
- normal disconnect restoration
- Tor-process death automatic proxy restoration
- network-service-change restoration
- reboot/orphan recovery
- uninstall safety, after functional acceptance if desired

Until those real-Mac gates pass, correct label is `0.2.0-rc1`, not stable `0.2.0`.
