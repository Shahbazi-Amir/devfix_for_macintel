# MASTER EXECUTION PROMPT — DEVFIX TUNNEL COMPLETION V2

Repository: `Shahbazi-Amir/devfix_for_macintel`

Write branch: `feature/devfix-tunnel`

Stable branch: `main` (READ-ONLY for Tunnel work)

## Mission

Continue until a release-candidate package is installable on the real Intel macOS Monterey target. Do not hand off unfinished engineering that can still be completed in GitHub/CI.

## Required closed failure classes

`SYSTEM_PROXY_NOT_IMPLEMENTED`, `CRASH_CAN_STRAND_PROXY`, `PROXY_OWNERSHIP_CONFLICT`, `NETWORK_SERVICE_HARDCODING`, `SHARED_RUNTIME_COUPLING`, `NO_INSTALLER_OR_RECOVERY_DAEMON`, `NO_CONFLICT_TEST_MATRIX`, `NO_RELEASE_ARTIFACT`.

Only `REAL_TARGET_MAC_ACCEPTANCE` may remain before stable `0.2.0`.

## System Proxy contract

Reach validated Snowflake SOCKS first; resolve active network service; snapshot SOCKS/HTTP/HTTPS/PAC/auto-discovery; fail closed on third-party proxy state; record ownership before mutation; apply only localhost SOCKS; verify readback; monitor with privileged guardian; restore on Tor death/network-service change; never overwrite external changes; restore before stopping Tor; provide repair; recover orphaned owned state after reboot.

## Runtime contract

Package independent `tor` and `lyrebird` under `/usr/local/libexec/devfix-tunnel/tor` from the official Tor Expert Bundle after SHA-256 verification against the Tor checksum manifest. Do not depend on `/usr/local/libexec/devfix`.

## Packaging contract

Produce `DevFixTunnel-<version>-macos-x86_64.pkg` and `.tar.gz`; install CLI, guardian, runtime, LaunchDaemon and docs; install-smoke-test the pkg on Intel macOS CI without enabling System Proxy on the runner.

## Test contract

Require syntax, ShellCheck, mocked System Proxy connect/restore, SOCKS-only isolation, existing proxy conflicts, Tor crash restoration, external ownership-loss preservation, network-service change restoration, missing-runtime classification, inherited DevFix regression on Linux and Intel macOS, and package build/install.

Never weaken a test to obtain green CI. Classify each failure, fix root cause, and rerun.

## Release naming

First System Proxy candidate: `0.2.0-rc1`. Stable `0.2.0` requires real Intel Monterey acceptance.

## Full-device boundary

Do not block System Proxy on NetworkExtension. A true packet VPN later requires Apple NetworkExtension entitlement, `NEPacketTunnelProvider`, signed identity, packet forwarding from `NEPacketTunnelFlow` into a SOCKS/Tor-compatible engine, and DNS/IPv4/IPv6 validation.

If another engineering task remains that can be completed without the user’s physical Mac, continue instead of handing it off.
