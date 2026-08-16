# Remediation 009 — SELECTIVE_CHROME_PORT_CAPTURE_STDOUT

Date: 2026-08-16

The first official CI run that included the selective Chrome launcher failed on both Ubuntu and Intel macOS with:

`FAIL: Chrome SOCKS proxy flag missing`

Root cause: `PORT=$(ensure_socks_route)` captured all stdout emitted by `ensure_socks_route`. When the launcher had to establish a SOCKS route, its progress message and the `devfix-tunnel connect` output were written to stdout along with the numeric port. The resulting Chrome `--proxy-server` value was malformed even though the underlying SOCKS connection state itself was valid.

Fix: reserve stdout from `ensure_socks_route` exclusively for the numeric port. Route progress and child `connect` output to stderr. Keep the exact proxy-flag assertion unchanged so this bug cannot regress silently.

No security check or test is suppressed.
