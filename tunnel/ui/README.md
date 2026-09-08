# DevFix Tunnel Smart Routing UI

This branch builds the native Intel macOS menu-bar app on top of the validated RC3 transport core and introduces the new `0.4.0-rc1` smart-routing layer.

## Behavior

- Safari, Chrome, and other applications that honor macOS System Proxy use the validated Tor route.
- `*.ir`, `ir`, localhost, `*.local`, link-local, and RFC1918 private-network destinations stay direct.
- The original proxy and bypass-domain settings are snapshotted and restored on disconnect, Tor death, detected network-path change, and orphan recovery.
- A Wi-Fi-to-Hotspot change is detected using interface + default gateway + network-service identity, even when the macOS service name remains `Wi-Fi`.

This is browser/system-proxy split routing, not a packet-level VPN. Applications that ignore macOS proxy settings are outside this mode.

## Installation boundary

The menu app calls the installed controller at `/usr/local/bin/devfix-tunnel`. Administrator authorization still occurs through the controller in Terminal so the existing guardian privilege boundary remains intact.

## Build

`bash tunnel/scripts/build-ui-app.sh`

Outputs:

- `build/tunnel-ui/DevFix Tunnel.app`
- `build/tunnel-ui/DevFixTunnel-0.4.0-rc1-smart-routing-macos-x86_64.zip`

The RC app is ad-hoc signed for physical testing. Stable promotion requires the real Intel Monterey network-change and reboot/orphan acceptance gates.
