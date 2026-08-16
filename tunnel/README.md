# DevFix Tunnel

DevFix Tunnel is the independent macOS censorship-circumvention product built from the proven DevFix Tor/bridge foundation while keeping stable DevFix separate.

Current release candidate: `0.3.0-rc1`.

Primary target: Intel x86_64 Mac / macOS Monterey 12.x.

## Why V5 exists

Physical Monterey testing of `0.2.0-rc1` proved installation, runtime integrity, repair safety, and fail-closed proxy behavior, but two real Snowflake sessions stalled at 10% with repeated WebRTC `DataChannel.OnOpen` failures. The old candidate depended on one hard-coded Snowflake bridge definition even though the same official Tor Expert Bundle already shipped current Snowflake, meek_lite, and obfs4 bridge definitions.

V5 removes that single-route dependency. The exact packaged Tor bundle is now the source of truth for the transport catalog.

## Current architecture

```text
Internet connection
      |
      v
Transport auto-selection
  Snowflake A
      |
   failure -> Snowflake B
      |
   failure -> meek_lite
      |
   failure -> bounded obfs4 fallback
      |
      v
Tor bootstrap 100%
      |
Routed HTTPS validation
      |
      +------------------------+
      |                        |
      v                        v
local SOCKS               macOS System Proxy
(selective/CLI)            (proxy-aware apps)
```

System Proxy is **never enabled** until a transport reaches Tor bootstrap 100% and routed HTTPS validation passes.

Each transport candidate gets its own Tor process, data directory, and attempt log. Failed candidates are stopped before fallback continues.

## Transport controls

Default:

```bash
devfix-tunnel connect
```

uses:

```text
--transport auto
--foreign-only
```

Explicit choices:

```bash
devfix-tunnel connect --transport snowflake
devfix-tunnel connect --transport meek
devfix-tunnel connect --transport obfs4
```

The runtime bridge catalog is generated at package-build time from the exact official Tor Expert Bundle `pt_config.json`; the CLI does not carry the old hard-coded Snowflake bridge as its default source of truth.

## Foreign-exit policy

V5 packages Tor GeoIP/GeoIPv6 data aligned with the packaged Tor core version. The default policy excludes Iran and unknown-country exits:

```text
Foreign-only: ON
Exclude Iran: ON
Exclude unknown-country exits: ON
```

A preferred exit country may be requested:

```bash
devfix-tunnel connect --exit-country de
```

This is a Tor path preference, not a promise that a specific commercial/residential IP or a permanently fixed country address exists. Verify the live result after connection with:

```bash
devfix-tunnel exit
```

To opt out of the foreign-only policy:

```bash
devfix-tunnel connect --allow-any-exit
```

`--foreign-only --exit-country ir` is rejected as a conflicting policy.

## Application coverage

### System Proxy mode

```bash
devfix-tunnel connect system
```

safely applies the validated local SOCKS route to the active macOS System Proxy service. This is intended for Safari, Chrome, VS Code/Electron, and other applications that honor macOS proxy settings.

### Selective Chrome — one tunneled Chrome plus normal direct Chrome

For the common case where normal Chrome should stay direct while a second Chrome is tunneled:

```bash
devfix-tunnel-chrome https://example.com/
```

If no validated route exists, this launcher starts DevFix Tunnel in SOCKS-only `auto` + `foreign-only` mode. It then launches a separate Chrome/Chromium process using a dedicated profile under the DevFix Tunnel user-state directory.

The isolated Chrome process receives:

```text
--proxy-server=socks5://127.0.0.1:<tunnel-port>
--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1
--force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

This reduces direct DNS/WebRTC bypass risk for the selectively tunneled Chrome instance without changing macOS System Proxy or the user's ordinary Chrome profile. It is still Chrome over Tor, not Tor Browser; it does not inherit Tor Browser's anti-fingerprinting protections.

### Process-scoped CLI mode

Some developer tools do not reliably consume macOS System Proxy but do honor standard proxy environment variables. For those tools:

```bash
devfix-tunnel run <command> [args...]
```

sets `ALL_PROXY` and `all_proxy` only for that child process. It does not modify shell startup files or global environment state.

### SOCKS-only mode

```bash
devfix-tunnel connect socks
```

starts only the validated local SOCKS endpoint and does not change macOS System Proxy settings.

## Exit identity

While connected:

```bash
devfix-tunnel exit
```

queries Tor Check through the tunnel, requires the route to be recognized as Tor, reports the observed public exit IP, maps IPv4 against the packaged local Tor GeoIP database when possible, and reports whether the foreign-only policy is satisfied.

Exit identity is not persistently logged by default.

## Safety model

System Proxy activation remains fail-closed. Existing enabled SOCKS/HTTP/HTTPS/PAC/auto-discovery settings are not overwritten. Disabled authenticated SOCKS configuration is also treated as a conflict rather than destructively rewritten.

A privileged guardian snapshots prior proxy state, applies only tunnel-owned localhost SOCKS settings, verifies ownership, monitors Tor and the active network service, and restores on normal disconnect, Tor death, or network-service change. If another process changes the proxy while connected, DevFix Tunnel refuses to overwrite that external change.

A root LaunchDaemon detects orphaned tunnel-owned proxy sessions and performs conservative recovery.

Repeated same-mode `connect` is idempotent. Switching between SOCKS and System Proxy requires explicit disconnect. `restart` preserves the existing mode and routing policy.

## What this product is not

`0.3.0-rc1` is not represented as a packet-level full-device VPN.

System Proxy can cover a large class of macOS applications, selective Chrome gives an explicit split-browser workflow, and `devfix-tunnel run` covers explicit CLI child processes, but software that bypasses System Proxy and does not honor SOCKS/proxy configuration is not automatically captured.

A true full-device implementation is a separate NetworkExtension / `NEPacketTunnelProvider` milestone documented in `docs/tunnel/FULL_DEVICE_VPN_ROADMAP.md`. That path requires a packet forwarding engine plus Apple Network Extension entitlement/signing/provisioning before it can truthfully be called a deployable full-device VPN.

## Network outage limitation

DevFix Tunnel can improve resilience against censorship, blocked destinations, restrictive NAT/firewalls, and a failing Snowflake transport by switching transport families. It cannot manufacture external connectivity if the underlying network has zero reachable route to any outside bridge, relay, rendezvous service, or server.

## Core commands

```bash
devfix-tunnel doctor
devfix-tunnel connect
devfix-tunnel status
devfix-tunnel exit
devfix-tunnel run curl https://example.com
devfix-tunnel-chrome https://example.com/
devfix-tunnel open https://check.torproject.org/
devfix-tunnel disconnect
devfix-tunnel repair
devfix-tunnel logs 200
```

## Release gates

Before physical-Mac retesting, the exact product SHA must pass:

- syntax and ShellCheck without suppressing new findings;
- V5 multi-transport fallback tests;
- exit-policy/GeoIP tests;
- process-scoped `run` tests;
- selective Chrome command/flag/profile tests;
- all prior System Proxy ownership/restore/crash/conflict tests;
- Intel macOS command contract;
- inherited stable-DevFix regression on Ubuntu and Intel macOS;
- package build and install smoke test on Intel macOS;
- package checks for Tor runtime, transport catalog, GeoIP, selective Chrome launcher, guardian, and recovery LaunchDaemon;
- stable DevFix source-preservation check.

Stable promotion still requires physical Intel Monterey acceptance of the exact package artifact.
