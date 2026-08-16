# DevFix Tunnel — Reuse Matrix

Base branch SHA: `38c013873ed85a5f92a1ec2da7283fdb4b62ac22`

## REUSE_AS_IS / read-only runtime dependency

- Verified Tor Expert Bundle payload location under `/usr/local/libexec/devfix/tor/` for the first prototype.
- `tor` and `lyrebird` binaries are consumed read-only; DevFix Tunnel never shares DevFix state or tor-data.
- Upstream bridge configuration and checksum/supply-chain principles are inherited until a controlled transport update is performed.
- Security principles: TLS verification stays enabled; no SIP/Gatekeeper weakening; no custom CA; no global `/etc/hosts` changes.

## ADAPT_BEHIND_NEW_INTERFACE

- Snowflake/Tor startup and bootstrap parsing.
- Real wall-clock bootstrap/stall timeouts.
- Local SOCKS port selection.
- Route validation through `socks5h`.
- Atomic state files.
- PID/process lifecycle and cleanup.
- Tor log handling and redaction principles.
- macOS/architecture diagnostics.

The adapted implementation lives under `tunnel/` and uses tunnel-owned names and paths.

## DO_NOT_REUSE as tunnel architecture

- Homebrew wrapper behavior.
- Homebrew compatibility/error diagnosis.
- Git/curl wrapper semantics.
- DevFix process-scoped environment injection as the general-routing mechanism.
- Developer-only endpoint list as the sole validation contract.
- DevFix PID/state/config/log/tor-data paths.
- `/usr/local/bin/devfix` command identity.

## Collision contract

DevFix Tunnel owns:

```text
~/Library/Application Support/DevFixTunnel
~/Library/Logs/DevFixTunnel
SOCKS default range 19150-19159
devfix-tunnel command identity
```

DevFix owns its existing paths independently. The tunnel prototype must never delete, rewrite, or treat DevFix state as its own.

## Known intentional dependency

The first transport-core milestone reuses the already-installed DevFix Tor runtime binaries to avoid duplicating a verified payload while architecture is stabilized. Packaging isolation is a later milestone: DevFix Tunnel will eventually ship its own versioned runtime payload and third-party notices.
