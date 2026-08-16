# DevFix Tunnel 0.3.0-rc2 — Targeted Real Mac Acceptance V6

Date: 2026-08-16

Target: Intel x86_64 Mac / macOS Monterey 12.7.6

Validated package identity:

- product gate SHA: `1e56a6006be661dd1b4d743dd4aa98992c1e22a3`
- package SHA-256: `3844d5536013dfe0ff64cd8979a7430bca443a6e10a876c9c8c7462a2567dbe8`
- package name: `DevFixTunnel-0.3.0-rc2-macos-x86_64.pkg`

## Purpose

This run is intentionally narrower than earlier acceptance prompts. RC1 already proved package installation and fail-closed System Proxy behavior, but its real auto-transport path failed. RC2 specifically remediates:

- unknown-country entry bridges being excluded by the Foreign-only policy;
- auto fallback stopping after five candidates;
- a fixed 90-second stall cutoff being too aggressive at later bootstrap phases.

The first RC2 physical gate is therefore: **can the exact locked RC2 artifact establish a validated Tor route on the real target network without regressing fail-closed proxy safety?**

Do not continue into browser/crash/reboot acceptance until this gate passes.

## Expected RC2 differences

During `devfix-tunnel connect`:

- Foreign-only mode must not generate a sustained `Not using bridge ... it is in ExcludeNodes` loop merely because an entry bridge has unknown country.
- Auto mode is allowed to continue beyond attempt 5 and reach later obfs4 candidates.
- If bootstrap reaches >=10% with no progress, the normal default stall window is longer than the initial phase.
- If bootstrap reaches >=25% / consensus-loading territory, the normal default no-progress window is 240 seconds.
- macOS System Proxy must remain disabled until Tor reaches 100% and routed HTTPS validation succeeds.

## Run procedure

1. Locate the downloaded RC2 `.pkg`.
2. Verify exact SHA-256 before installation.
3. Safely disconnect/repair any old RC1 state.
4. Install RC2.
5. Verify `devfix-tunnel version` reports `0.3.0-rc2`.
6. Run `doctor`.
7. Capture proxy state before connect.
8. Run default `devfix-tunnel connect` without manually forcing a transport or shortening timeouts.
9. Do not interrupt fallback merely because Snowflake/meek fails. Allow the finite catalog to proceed.
10. On success, capture `status`, `exit`, and `scutil --proxy`.
11. On failure, capture `status`, `scutil --proxy`, and `logs 500`.
12. If route succeeds, proceed later to browser/Selective Chrome/process-scoped CLI/crash/reboot acceptance.

## Pass criteria for this targeted gate

A route-level PASS requires all of:

- exact package hash matched;
- installed version is RC2;
- doctor passes;
- a transport reaches Tor bootstrap 100%;
- routed HTTPS validation succeeds;
- `status` reports connected/healthy;
- live exit verification succeeds or provides actionable route-level evidence;
- System Proxy is only enabled after validated route readiness;
- no third-party proxy state is destructively overwritten.

A safe failure is not a route PASS, but the product must still leave macOS System Proxy unowned/unchanged and provide attempt logs for every candidate tried.

## Failure evidence required

If auto still fails, preserve:

- the full terminal output of the targeted block;
- `devfix-tunnel status`;
- `scutil --proxy`;
- `devfix-tunnel logs 500`.

The most important evidence is the newest transport-attempt logs, including the highest bootstrap percentage and any Tor warning/error immediately before the stall/failure.

## Stable promotion rule

Do not promote to stable `0.3.0` from CI alone. The exact RC2 artifact above must first pass this physical route gate, then the remaining browser/Selective Chrome/process-scoped CLI/crash/network-change/reboot acceptance classes.
