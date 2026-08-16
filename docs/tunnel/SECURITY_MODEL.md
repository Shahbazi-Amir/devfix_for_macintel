# DevFix Tunnel — Security Model

## Security objectives

- Preserve macOS security protections.
- Limit network mutations to explicit tunnel-owned changes.
- Make changes reversible and ownership-aware.
- Keep the local SOCKS listener on localhost only.
- Avoid collection of browsing history and credentials.
- Never terminate unrelated Tor processes.

## Non-negotiable prohibitions

```text
no SIP disable
no Gatekeeper disable
no TLS verification disable
no production curl -k
no custom root CA installation
no chmod 777
no global /etc/hosts rewrite
no PAT/password/token in source or logs
no listening SOCKS on 0.0.0.0
no killing processes only by name
```

## Process threat boundary

A stale PID can point to an unrelated process after PID reuse. Therefore PID liveness alone is insufficient. Before termination the prototype compares the recorded PID with the expected tunnel Tor executable and tunnel-owned torrc path. If ownership cannot be proven, it refuses destructive cleanup.

## State and filesystem

Tunnel state, logs, and tor-data use a separate root from DevFix and are created under a restrictive umask. Atomic replacement is required for recovery-critical state.

## Privacy

Normal logs record lifecycle state, elapsed time, session/PID/port data, and failure classes. They must not become a destination URL/history log. Secrets and proxy credentials must be redacted.

## Future privileged operations

System Proxy or Packet Tunnel work must use least privilege. Do not run the whole UI/backend as root. If a helper becomes necessary, its command surface and authorization model require an explicit security review before use.

## Product claims

Do not claim perfect anonymity, guaranteed censorship resistance, guaranteed availability, or full-device traffic coverage in System Proxy mode. Tor/Snowflake and macOS application proxy behavior have real limitations that must remain visible in documentation.
