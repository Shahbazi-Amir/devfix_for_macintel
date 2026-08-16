# DevFix Tunnel 0.3.0-rc3 — Real Intel Monterey Route Acceptance

Use only the locked RC3 package built from product SHA `5142badc0da48953dcc2cdecb6f080ef6fac27e6`.

Expected package SHA-256:

`cc6d1f624a20d4ae3cb8d7c0be0fbf8a26844df87a589a4267f24a9c67a5ae5b`

## Purpose

This run validates only the route gate remediated from the physical RC2 failure. Do not perform browser/crash/reboot tests until route bootstrap reaches 100% and routed HTTPS validation passes.

RC3 changes under physical validation:

- persistent Tor directory CacheDirectory across fallback and later sessions;
- fresh per-attempt DataDirectory remains isolated/disposable;
- early transport failures remain bounded;
- >=40% directory/descriptors phase receives up to 900 seconds without percentage progress;
- total candidate ceiling is 1200 seconds;
- System Proxy is still not enabled before 100% + HTTPS validation.

## Required observations

1. Verify exact package SHA.
2. Safely disconnect/repair any older RC state.
3. Upgrade package.
4. Verify `DevFix Tunnel 0.3.0-rc3` and doctor.
5. Confirm directory cache is reported.
6. Capture `scutil --proxy` before connect.
7. Run default `devfix-tunnel connect` with no timeout overrides.
8. Do not interrupt 40/45/50% merely because it remains unchanged for several minutes; RC3 intentionally permits up to 900 seconds of no-progress in this phase.
9. If route succeeds, capture status, exit identity and system proxy.
10. If route fails, capture status, system proxy, doctor and 600 lines of Tunnel logs.
11. A failed route must leave System Proxy unchanged/non-tunnel-owned.

## Failure loop

Any physical failure becomes a new explicit failure class. Do not blindly retry the same configuration. Preserve logs, identify whether the failure is transport reachability, directory bootstrap, exit-policy construction, validation, or proxy activation, then remediate the owning layer and rebuild CI/package before another physical run.

Stable `0.3.0` is prohibited until route acceptance and subsequent browser/recovery acceptance pass on the actual Intel Monterey target.
