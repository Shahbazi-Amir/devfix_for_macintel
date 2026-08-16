# DevFix Tunnel — State Machine

The transport core uses explicit states:

```text
DISCONNECTED
   |
STARTING
   |
BOOTSTRAPPING
   |  \__ process exit / stall / timeout -> FAILED
   v
VALIDATING
   |  \__ routed HTTPS validation failure -> FAILED
   v
CONNECTED
   |
RESTORING
   |
DISCONNECTED
```

`DEGRADED` is a diagnostic state for future work when persisted state says connected but real process/network evidence no longer supports it.

## Rules

- State is evidence, not authority. Actual process/network state wins.
- State replacement is atomic.
- `BOOTSTRAPPING` below 100% is distinct from `VALIDATING` after 100%.
- Timeouts use real epoch/wall-clock elapsed time, not poll counts.
- A stale PID that points to a live process whose ownership cannot be proven is a hard safe-stop condition; it is never killed.
- Ordinary disconnect removes runtime state/torrc/PID files but preserves tunnel `tor-data` for reuse.
- Future System Proxy state adds a durable proxy snapshot and ownership marker before any macOS proxy mutation.

## Failure classes used by current milestone

```text
TRANSPORT_PROCESS_FAILURE
SNOWFLAKE_BOOTSTRAP_FAILURE
ROUTE_VALIDATION_FAILURE
TIMEOUT
PORT_CONFLICT
```

Future proxy-specific states/failures are defined in `SYSTEM_PROXY_DESIGN.md` and must not be introduced by silently changing this lifecycle contract.
