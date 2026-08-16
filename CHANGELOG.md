# Changelog

## 2.0.4 - 2026-08-16

- Fixed Snowflake post-bootstrap validation to probe the GHCR Registry API base endpoint (`/v2/`) instead of treating a repository root as a health endpoint.
- Made bootstrap and validation deadlines use real wall-clock time, so slow endpoint probes cannot silently stretch a nominal timeout into many minutes.
- Separated 100% Tor bootstrap from developer-route validation; 100% can no longer be misreported as a bootstrap stall.
- Added a dedicated `ROUTE_VALIDATION_FAILURE` diagnosis for the rare case where Tor is fully bootstrapped but required developer endpoints remain unreachable.
- Aligned `devfix brew` Snowflake routing with Homebrew's documented SOCKS environment by using process-scoped `all_proxy`/`ALL_PROXY` and clearing protocol-specific proxy variables for the brew subprocess.
- Added regressions for the exact GHCR health endpoint, successful 100% bootstrap validation, post-100% failure classification, and Homebrew SOCKS environment.

## 2.0.3 - 2026-08-15

- Fixed Tor managed-transport launch on Intel Monterey by removing a literal quote wrapper around the bundled lyrebird executable path.
- Added regression coverage for the exact `ClientTransportPlugin snowflake exec /usr/local/.../lyrebird` torrc form used by Tor Project documentation.
- Added fast failure classification when lyrebird repeatedly exits before Snowflake bootstrap, avoiding a long generic stall timeout for launch/configuration failures.

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
