# Remediation 010 — SELECTIVE_CHROME_HEALTH_SHELLCHECK

Date: 2026-08-16

After adding health/policy compatibility checks and real-Tor config validation, official CI found two static-analysis issues before release:

- `SC2015` in the selective Chrome post-connect health assertion because it used `A && B || C`.
- `SC2209` in the new country-mismatch test because the temporary environment assignment was combined with a command/`&& fail` form that ShellCheck treated ambiguously.

Fix: use explicit `if` conditions for route health and explicit `export`/`unset` around the test-only country override. The health and mismatch assertions remain mandatory; no lint rule or test is suppressed.
