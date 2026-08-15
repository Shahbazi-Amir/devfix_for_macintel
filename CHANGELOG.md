# Changelog

## 2.0.0 - 2026-08-15

- Rebuilt DevFix around a bundled Snowflake/Tor transport.
- Removed the requirement for an existing VPN, proxy, or VPS.
- Added automatic direct-to-Snowflake route selection.
- Added connection lifecycle, stale-state repair, logs, and transport commands.
- Added process-scoped wrappers for Homebrew, Git, curl, and arbitrary CLI tools.
- Added network versus macOS/Homebrew compatibility diagnostics.
- Added self-contained Intel macOS `.pkg` and tarball packaging with official Tor bundle checksum verification.
- Retained external proxy support only as an optional advanced fallback.

## 1.0.0

- Initial proxy-dependent diagnostic wrapper.
