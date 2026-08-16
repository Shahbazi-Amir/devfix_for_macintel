# DevFix Tunnel — Full-device VPN Roadmap

## Current product boundary

The V5 product remains a safe macOS System Proxy + process-scoped SOCKS routing product. It is useful for Safari, Chrome, VS Code/Electron and other applications that honor macOS proxy settings, plus explicit CLI child processes launched with `devfix-tunnel run`.

It is not a packet-level full-device VPN.

## Why a true full-device VPN is a different layer

A real macOS packet tunnel uses Apple NetworkExtension. `NEPacketTunnelProvider` receives IP packets from a virtual interface and the provider must forward/encapsulate them through a remote/tunnel transport, then inject received packets back into the network stack.

Apple requires the `com.apple.developer.networking.networkextension` entitlement for this class. Distribution outside the Mac App Store also requires an appropriately Developer-ID-signed/provisioned app with the Network Extension capability.

Therefore this repository must not claim a production full-device VPN until those signing/provisioning inputs and a packet forwarding engine are present and tested.

## Proposed architecture

```text
macOS applications / system services
            |
            v
 NetworkExtension Packet Tunnel
            |
            v
   packet forwarding engine
            |
      +-----+------------------+
      |                        |
      v                        v
 Tor/Snowflake path      future server-backed path
 (TCP-oriented)          (TCP/UDP as protocol allows)
```

## Engineering phases

1. Keep System Proxy mode production-safe and useful now.
2. Build a separate Xcode host app + Packet Tunnel Provider target.
3. Add entitlement-aware CI that compiles unsigned source but never claims deployability without provisioning.
4. Select/implement packet-to-proxy forwarding. Tor is SOCKS/TCP-oriented; UDP/DNS behavior must be explicitly designed rather than silently leaked direct.
5. Add route include/exclude policy and kill-switch semantics.
6. Add DNS policy and IPv4/IPv6 tests.
7. Add sleep/wake, Wi-Fi change, captive portal and reboot tests.
8. Sign/provision with the user's Apple Developer identity only when available; never request private certificate material or passwords in Chat.
9. Run physical Monterey acceptance before calling it a full-device VPN.

## Important outage limitation

No software tunnel can create external Internet connectivity when the underlying network has no reachable route to any outside rendezvous, bridge, relay or server. Multi-transport circumvention can survive filtering and some restrictive NAT/firewall conditions, but not a complete upstream disconnection with zero reachable external path.
