# Remediation 008 — V5_BUILD_SCRIPT_EXEC_BIT

Date: 2026-08-16

The first official V5 package run failed before GeoIP download because the newly created `tunnel/scripts/fetch-geoip.sh` did not carry an executable mode when created through the repository contents API. `fetch-tor-bundle.sh` attempted to execute the path directly and macOS returned `Permission denied`.

This is a packaging/build orchestration failure, not a runtime transport or System Proxy failure.

Fix: invoke the helper explicitly through `/bin/bash` so package correctness does not depend on executable mode metadata for this internal build helper. No test or security gate is suppressed.
