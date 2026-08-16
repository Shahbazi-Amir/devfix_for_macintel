# Remediation 007 — REAL_SNOWFLAKE_BOOTSTRAP_STALL_10

Date: 2026-08-16
Target: physical Intel x86_64 Mac, macOS Monterey 12.7.6
Release candidate: 0.2.0-rc1

## Evidence

The package hash matched the locked release artifact and installation/doctor/version all passed on the physical target Mac. The first real System Proxy acceptance attempt then failed before System Proxy activation while the independent Snowflake/Tor transport was bootstrapping:

```text
Starting DevFix Tunnel Snowflake transport...
Bootstrapped 0%
Bootstrapped 10%
Error: SNOWFLAKE_BOOTSTRAP_FAILURE: bootstrap stalled at 10% for 180s.
```

## Classification

`REAL_SNOWFLAKE_BOOTSTRAP_STALL_10`

Layer: Snowflake bootstrap / transport establishment.

This is not yet evidence of installer, System Proxy, guardian, or restore failure because the failure occurred before the System Proxy guardian was activated.

## Required investigation before any product-byte change

1. Capture `devfix-tunnel status` after the failure.
2. Capture `scutil --proxy` and verify the pre-test proxy state was not changed.
3. Capture `devfix-tunnel logs 200` and the Tor transport log.
4. Determine whether the Tor process is fully stopped and whether state is `FAILED` or safely disconnected.
5. Compare the real failure characteristics with the known stochastic Snowflake bootstrap behavior previously observed in stable DevFix.
6. Do not classify a single below-100 bootstrap attempt as a code defect without evidence.
7. If a controlled second attempt succeeds without product-byte changes, classify the first event as transient Snowflake transport failure and continue acceptance.
8. If repeated failures show stale-state/session coupling, design an independent Tunnel retry/rotation policy. Any such implementation must preserve fail-closed proxy activation and must not reuse writable DevFix state.

## Safety rule

Do not activate System Proxy until Snowflake reaches 100% and routed HTTPS validation passes. Do not manually force proxy settings to make the acceptance test proceed.
