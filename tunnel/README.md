# DevFix Tunnel

DevFix Tunnel is the independent, general-user censorship-circumvention branch built from the proven DevFix Snowflake/Tor foundation.

Current release candidate: `0.2.0-rc1`.

Primary target: Intel x86_64 Mac / macOS Monterey 12.x.

## Product boundary

`DevFix` remains the developer CLI routing tool. `DevFix Tunnel` is the separate System Proxy product for Safari, Chrome, and other applications that honor macOS proxy settings.

DevFix Tunnel owns separate state, tor-data, PID files, SOCKS ports, root proxy ownership data, and its own packaged Tor/lyrebird runtime.

## Current architecture

Snowflake/Tor → local SOCKS5 → macOS System SOCKS Proxy → proxy-aware applications.

This is intentionally called **System Proxy mode**, not a full packet-level VPN.

## Core commands

```bash
devfix-tunnel doctor
devfix-tunnel connect
devfix-tunnel status
devfix-tunnel open https://check.torproject.org/
devfix-tunnel disconnect
devfix-tunnel repair
```

`connect` defaults to System Proxy mode. For SOCKS only:

```bash
devfix-tunnel connect socks
```

## Safety model

System Proxy activation is fail-closed. Existing enabled SOCKS/HTTP/HTTPS/PAC/auto-discovery settings are not overwritten. A privileged guardian snapshots the previous SOCKS state, applies only the tunnel-owned localhost SOCKS configuration, verifies ownership, monitors Tor and the active network service, and restores on disconnect/Tor death/network-service change. If another process changes the proxy while connected, DevFix Tunnel refuses to overwrite that external change.

A root LaunchDaemon periodically detects orphaned guardian sessions and restores only proxy state that DevFix Tunnel can prove it owns.

## Stable gate

`0.2.0-rc1` is a release candidate. Stable `0.2.0` requires real Intel Monterey acceptance: real Snowflake, System Proxy apply/readback, Safari/Chrome, disconnect restoration, Tor-crash restoration, sleep/network change, and reboot/orphan recovery.

A true full-device VPN remains a later NetworkExtension/NEPacketTunnelProvider milestone and must not be claimed before packet-level forwarding and DNS behavior are implemented and validated.
