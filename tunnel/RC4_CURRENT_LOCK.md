# DevFix Tunnel 0.4.0-rc1 — Current RC Lock

Date: 2026-09-15

Repository: `Shahbazi-Amir/devfix_for_macintel`

Development branch: `feature/devfix-tunnel-smart-routing`

Base branch: `feature/devfix-tunnel-ui`

Stable DevFix branch: `main` — READ-ONLY for Tunnel work.

## Current release-candidate baseline

`0.4.0-rc1` is the current/latest DevFix Tunnel release-candidate baseline.

It is **not** promoted to stable. The previously validated `0.3.0-rc3` core remains historical physical evidence, while `0.4.0-rc1` adds Smart Routing and is the active RC for continued physical acceptance.

Exact build-source SHA:

`de07ac5b2feac27d52465382d73f48ee298a2adb`

Build-source commit:

`fix(tunnel-ui): publish 0.4.0-rc1 app artifact`

## CI gates on exact build-source SHA

The following GitHub Actions runs completed successfully on `de07ac5b2feac27d52465382d73f48ee298a2adb`:

- `CI` — Run `34980417505` — PASS
- `DevFix Tunnel CI` — Run `34980417462` — PASS
- `DevFix Tunnel Package` — Run `34980417616` — PASS
- `DevFix Tunnel UI` — Run `34980417473` — PASS

## Core/package artifact

Artifact name:

`DevFixTunnel-0.4.0-rc1-macos-x86_64`

Artifact ID:

`10401630715`

GitHub artifact digest:

`sha256:6b448a3c61783ca8ae89808023e3c791a5b214a0ebe711adb922814678c06345`

The package workflow builds and smoke-tests the Intel macOS package and portable archive for `0.4.0-rc1`.

## Native menu-bar UI artifact

Artifact name:

`DevFixTunnel-0.4.0-rc1-smart-routing-macos-x86_64`

Artifact ID:

`10400853940`

GitHub artifact digest:

`sha256:e9e6be0c356208077fd0f8f233a7fa8c4e8880208459e59a2c553c64ea6a779c`

Contained application ZIP:

`DevFixTunnel-0.4.0-rc1-smart-routing-macos-x86_64.zip`

Application ZIP SHA-256:

`4d340cb0178303e11bead0804a063d43bf3e30718292b1e75987800bcf3007ad`

The contained macOS application bundle is:

`DevFix Tunnel.app`

Target architecture / minimum OS:

- Intel `x86_64`
- macOS 12.0+

The app is a menu-bar (`LSUIElement`) application and uses the installed `/usr/local/bin/devfix-tunnel` controller rather than duplicating Tor/guardian logic.

## Smart Routing boundary

This RC preserves the validated RC3 transport/fallback design and adds browser-oriented Smart Routing:

- `.ir` destinations bypass the SOCKS proxy and remain direct;
- localhost, `.local`, link-local, and RFC1918 private destinations remain direct;
- other proxy-aware browser traffic uses the Tor SOCKS route while System Proxy mode is active;
- the guardian owns and restores both SOCKS proxy state and bypass-domain state;
- network identity tracks interface + gateway + network service before fail-open recovery.

## Physical acceptance status

Build, CI, package smoke tests, and UI bundle validation: **PASS**.

Physical Intel Monterey acceptance for this exact `0.4.0-rc1` artifact: **PENDING**.

Do not promote to stable until physical testing explicitly verifies at least:

1. native menu-bar app launch on the target Mac;
2. Safari and Chrome filtered-site access;
3. direct `.ir` access and local/private access;
4. disconnect restoration of SOCKS and the previous bypass list;
5. connected Wi-Fi-to-Hotspot/network-change recovery;
6. reboot/orphan recovery.

## Promotion guardrail

`main` remains unchanged by this RC lock.

Do not merge or promote `0.4.0-rc1` to stable solely because CI is green. This file records the current RC baseline and exact artifacts so physical acceptance can continue from a reproducible build.
