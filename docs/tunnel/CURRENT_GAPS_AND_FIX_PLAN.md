# DevFix Tunnel — Current Gaps, Fixes, and Completion Path

The alpha transport core was not yet a usable browser/system circumvention product. The completion work closes these failure classes:

- `SYSTEM_PROXY_NOT_IMPLEMENTED` → privileged System Proxy guardian.
- `CRASH_CAN_STRAND_PROXY` → per-session root guardian plus periodic/boot orphan recovery.
- `PROXY_OWNERSHIP_CONFLICT` → exact ownership signature; never overwrite external changes.
- `NETWORK_SERVICE_HARDCODING` → default-route interface mapped through `networksetup -listnetworkserviceorder`.
- `SHARED_RUNTIME_COUPLING` → independent Tor/lyrebird package under `/usr/local/libexec/devfix-tunnel`.
- `NO_INSTALLER_OR_RECOVERY_DAEMON` → `.pkg`, portable tarball, uninstall path, LaunchDaemon.
- `NO_CONFLICT_TEST_MATRIX` → mocked normal/conflict/crash/network-change tests.
- `NO_RELEASE_ARTIFACT` → Intel macOS package workflow.

## Release-candidate completion definition

`0.2.0-rc1` is ready for the user only when transport, System Proxy snapshot/apply/restore, conflict handling, Tor-crash recovery, network-service change recovery, independent runtime packaging, installer smoke test, inherited DevFix regression, and package artifact creation all PASS.

The only allowed remaining stable gate is `REAL_TARGET_MAC_ACCEPTANCE`.

## End-state roadmap

Stage A: System Proxy release candidate for Safari/Chrome/proxy-aware apps.

Stage B: real Intel Monterey acceptance and fix loop until `0.2.0` stable.

Stage C: native menu-bar UX around the proven controller.

Stage D: true full-device VPN using Apple NetworkExtension/NEPacketTunnelProvider plus a packet-forwarding engine. System Proxy mode must not be marketed as a packet-level VPN.

`main` remains read-only for Tunnel development; all Tunnel changes stay on `feature/devfix-tunnel`.
