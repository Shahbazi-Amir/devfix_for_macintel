# DevFix Tunnel — System Proxy Design

Status: **DESIGN ONLY — NOT IMPLEMENTED IN TRANSPORT-CORE MILESTONE**

## Goal

Allow applications that honor macOS System Proxy settings (including normal browser use) to route through the tunnel-owned local SOCKS listener without requiring per-app configuration.

This mode must be called **System Proxy**, not a full VPN.

## Safety algorithm

1. Discover candidate network services using supported macOS mechanisms; never hard-code `Wi-Fi`.
2. Determine the active/relevant service deliberately.
3. Read current proxy/PAC configuration.
4. Classify existing state as `NONE`, `OWNED_BY_DEVFIX_TUNNEL`, `THIRD_PARTY_PROXY`, `PAC_CONFIGURATION`, or `UNKNOWN_CONFLICT`.
5. If a third-party/unknown conflict cannot be composed safely, stop without changing settings.
6. Persist an atomic pre-change snapshot under the tunnel state root.
7. Persist a unique session/ownership marker.
8. Apply the minimum settings required for localhost SOCKS.
9. Read settings back and verify that expected tunnel-owned state is active.
10. Validate routed HTTPS.
11. Only then report System Proxy mode connected.

## Restore algorithm

On normal disconnect or recovery:

1. Load snapshot and ownership metadata.
2. Read current system settings.
3. Verify the current settings still match the tunnel-owned post-change state.
4. If they do, restore the exact pre-change snapshot.
5. Read settings back and verify restoration.
6. Clear proxy ownership metadata only after successful restoration.
7. If settings changed externally, do not overwrite them blindly; report a restore conflict and preserve evidence.

## Emergency repair

Future command:

```text
devfix-tunnel proxy restore
```

may restore only configuration demonstrably owned by DevFix Tunnel. It must not act as a generic “reset all network settings” command.

## Required test classes before implementation can be called PASS

- no existing proxy;
- existing SOCKS proxy;
- existing HTTP/HTTPS proxy;
- PAC configuration;
- renamed Wi-Fi service;
- multiple network services;
- proxy changed externally while connected;
- process crash after snapshot but before apply;
- process crash after apply;
- disconnect twice;
- network change/sleep-wake.

No System Proxy implementation may be released if a tested crash can strand the Mac pointing at a dead localhost proxy without a working recovery path.
