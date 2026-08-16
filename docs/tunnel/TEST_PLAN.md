# DevFix Tunnel — Test Plan

## Automated transport-core tests

- state directory is distinct from DevFix;
- tor-data directory is distinct from DevFix;
- default SOCKS range differs from DevFix;
- `version` and `help` work without Tor runtime;
- `doctor` reports missing runtime rather than mutating the system;
- atomic state fields are parsed correctly;
- stale/non-owned live PID is never killed;
- owned-process disconnect is idempotent;
- free-port selection never kills an occupying process;
- bootstrap parser selects latest percentage;
- stall and total timeout are wall-clock based;
- 100% bootstrap does not skip routed HTTPS validation;
- failed validation does not report CONNECTED;
- existing DevFix state fixtures are untouched.

## CI

Linux CI is appropriate for shell/static/fixture tests only. It cannot certify Monterey System Proxy behavior.

Required CI checks:

```text
bash -n tunnel/cli/devfix-tunnel
bash tests/test_devfix_tunnel.sh
git diff --check
existing DevFix test suite
```

## Real Intel Monterey acceptance — transport core

When a packaged/working branch is ready on the target Mac:

1. confirm existing `devfix` still works;
2. run `devfix-tunnel doctor`;
3. connect using tunnel-owned Snowflake;
4. observe bootstrap to 100%;
5. verify routed HTTPS through the reported SOCKS endpoint;
6. verify status reports owned/alive PID;
7. disconnect;
8. verify the tunnel listener/process is gone;
9. verify DevFix state and DevFix connectivity remain intact.

## Future System Proxy acceptance

Must additionally test Safari, Chrome, Firefox, IPv4, IPv6 behavior, DNS behavior, exact proxy snapshot/restore, pre-existing proxy conflicts, sleep/wake, network changes, and crash recovery.

## Evidence rule

A GitHub Actions PASS is not a real-Mac networking PASS. Missing real-Mac evidence must be reported as `NOT VERIFIED`.
