# DevFix Tunnel UI Preview

This branch adds a minimal native macOS menu-bar UI on top of the physically validated `0.3.0-rc3` controller. It does not duplicate Tor, transport, proxy ownership, or guardian logic.

## Target

- Intel x86_64 Mac
- macOS Monterey 12.x or newer
- installed DevFix Tunnel `0.3.0-rc3` CLI at `/usr/local/bin/devfix-tunnel`

## UI capabilities

The menu-bar app shows:

- controller state;
- active mode (`SOCKS` or `SYSTEM_PROXY`);
- transport / active network service / health;
- elapsed connection time;
- cached exit IP and country after an explicit exit refresh.

Actions:

- Connect SOCKS Only;
- Connect System Proxy;
- Open Selective Chrome;
- Disconnect;
- Refresh Exit IP / Country;
- Open Tor Check;
- Copy SOCKS address;
- Repair;
- Refresh Status.

## Privileged System Proxy operations

The validated RC3 controller deliberately owns all System Proxy safety and guardian behavior. This first UI preview does **not** collect an administrator password or implement a second privileged-helper path.

`Connect System Proxy` and `Repair` therefore open Terminal and run the existing controller there, allowing the normal macOS/sudo authorization path to remain unchanged. Status, SOCKS-only connect, disconnect, exit inspection, and Selective Chrome are controlled directly by the menu-bar app.

A later UI milestone may replace the brief Terminal authorization step with a properly designed privileged helper. It must preserve the existing ownership/restore/fail-closed guarantees rather than bypass them.

## Build

On an Intel macOS builder with Xcode Command Line Tools:

```bash
bash tunnel/scripts/build-ui-app.sh
```

Outputs:

```text
build/tunnel-ui/DevFix Tunnel.app
build/tunnel-ui/DevFixTunnel-0.3.0-rc3-ui-preview-macos-x86_64.zip
```

The preview app is ad-hoc signed for local testing. Production distribution/notarization is a separate release step.

## Scope boundary

This UI preview is intentionally separate from future Smart/Split routing and future full-device NetworkExtension VPN work. Those should be developed on later branches after the UI/controller contract is proven on the real target Mac.
