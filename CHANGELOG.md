# Changelog

## 2.0.2 - 2026-08-15

- Fixed upgrades that could leave the bundled Tor directory root-only and make Snowflake look uninstalled.
- Normalized Tor payload permissions in source fetch, tar installation, package build, and package postinstall repair.
- Changed Tor notice logging to stdout with DevFix owning the log redirection, avoiding Monterey log-file initialization failures.
- Added progress-aware Snowflake bootstrap with a 10-minute hard limit and a 3-minute no-progress stall limit.
- Improved diagnostics for inaccessible versus missing Snowflake payloads and partial developer-network reachability.
- Added a package-upgrade regression test that reproduces the legacy root-owned mode-700 directory.

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
