# DevFix Tunnel 0.3.0-rc2 — Engineering Status Lock

Date: 2026-08-16

Repository: `Shahbazi-Amir/devfix_for_macintel`

Development branch: `feature/devfix-tunnel`

Stable DevFix branch: `main` — READ-ONLY for Tunnel work

## Exact validated RC2 identity

Final shared gate SHA:

`1e56a6006be661dd1b4d743dd4aa98992c1e22a3`

Both official Tunnel workflows passed on this exact SHA. Root-level status/acceptance documentation may advance the branch ref without changing the locked product/package identity above.

## Why RC2 replaced RC1

Physical Intel Monterey testing of `0.3.0-rc1` produced three concrete failure classes:

1. `REAL_MAC_UNKNOWN_BRIDGE_EXCLUSION`
   - Snowflake and meek repeatedly logged `Not using bridge ... it is in ExcludeNodes` while Foreign-only mode was enabled.
   - RC2 changes the policy to `GeoIPExcludeUnknown 0` plus explicit `ExcludeExitNodes {ir},{??}`, so unknown-country entry bridges are not globally excluded while Iran/unknown exits remain excluded.

2. `REAL_MAC_AUTO_CATALOG_TRUNCATION`
   - RC1 stopped after five attempts: 2 Snowflake + 1 meek + only 2 obfs4, despite 7 packaged obfs4 candidates.
   - RC2 defaults `MAX_AUTO_ATTEMPTS` to `0`, meaning exhaust the finite packaged catalog. A positive explicit override can still bound attempts.

3. `REAL_MAC_PHASE_AWARE_BOOTSTRAP_STALL`
   - RC1 killed an obfs4 route after it reached 30% (`Loading networkstatus consensus`) and then showed no percentage change for 90 seconds.
   - RC2 uses phase-aware default no-progress limits: 90s initial, 150s after >=10%, 240s from >=25%. The explicit `DEVFIX_TUNNEL_STALL_TIMEOUT` override remains available for deterministic tests.

RC1 must not be promoted to stable.

## Official RC2 CI gate

Workflow: `DevFix Tunnel CI`

Run ID: `31964265658`

Head SHA: `1e56a6006be661dd1b4d743dd4aa98992c1e22a3`

Result: **PASS**

Validated classes include:

- syntax: PASS
- ShellCheck without suppressing findings: PASS
- original System Proxy/guardian/restore/conflict suite: PASS
- V5 Snowflake-to-meek fallback fixture: PASS
- exit-policy/GeoIP fixture suite: PASS
- process-scoped `run` suite: PASS
- Selective Chrome suite: PASS
- RC2 physical-failure regression: PASS on Ubuntu
- RC2 physical-failure regression: PASS on Intel macOS
- regression proves auto mode reaches attempt 6 / obfs4 candidate 3 after five prior failures: PASS
- regression proves `GeoIPExcludeUnknown 0` + `ExcludeExitNodes {ir},{??}`: PASS
- regression proves phase-aware stall policy is present: PASS
- inherited stable DevFix regression: PASS on Ubuntu
- inherited stable DevFix regression: PASS on Intel macOS

## Official RC2 package gate

Workflow: `DevFix Tunnel Package`

Run ID: `31964265651`

Head SHA: `1e56a6006be661dd1b4d743dd4aa98992c1e22a3`

Result: **PASS**

Validated stages include:

- portable archive build: PASS
- bundle-native transport catalog generation: PASS
- catalog minimums: Snowflake >=2, meek >=1, obfs4 >=7: PASS
- real packaged Tor parser accepts Snowflake + RC2 GeoIP/exit policy: PASS
- real packaged Tor parser accepts meek + RC2 GeoIP/exit policy: PASS
- real packaged Tor parser accepts obfs4 + RC2 GeoIP/exit policy: PASS
- macOS Intel `.pkg` build: PASS
- package install smoke test on Intel macOS runner: PASS
- installed version `0.3.0-rc2`: PASS
- installed Selective Chrome launcher: PASS
- installed Tor/lyrebird/GeoIP/catalog/recovery daemon: PASS
- installed `doctor`: PASS
- real Tor parser run again against installed package: PASS
- stable DevFix `2.0.4` source preservation: PASS
- artifact upload: PASS

## Locked RC2 artifact

GitHub Actions artifact ID:

`9268053298`

Artifact name:

`DevFixTunnel-0.3.0-rc2-macos-x86_64`

GitHub artifact digest / independently downloaded ZIP SHA-256:

`cd82d3f35cb29ca939ad7e3646f6fd9aaee859299c13537852f284854ac3396e`

Contained files and independently verified SHA-256 values:

- `DevFixTunnel-0.3.0-rc2-macos-x86_64.pkg`
  - `3844d5536013dfe0ff64cd8979a7430bca443a6e10a876c9c8c7462a2567dbe8`
- `DevFixTunnel-0.3.0-rc2-macos-x86_64.tar.gz`
  - `ca7855dbae9c1535aeb9af0d3025f20c222807e69bc1b791f5b543cf87d90b78`
- `SHA256SUMS.txt`
  - `8314a32d1381b8808647002cfcb2c24026bd9f81cdce32c2914b2f7207087785`

Independent `shasum -a 256 -c SHA256SUMS.txt`: **PASS** for both `.pkg` and `.tar.gz`.

## Independent artifact-content audit

The downloaded artifact was unpacked independently after both official workflows passed. Confirmed inside the delivered RC2 bytes:

- `TUNNEL_VERSION="0.3.0-rc2"`
- `GeoIPExcludeUnknown 0`
- `ExcludeExitNodes {ir},{??}`
- `MAX_AUTO_ATTEMPTS` default `0`
- handshake-stage stall default `150`
- consensus-stage stall default `240`
- transport catalog counts: Snowflake `2`, meek `1`, obfs4 `7`
- Tor GeoIP + GeoIPv6 files
- Selective Chrome SOCKS/DNS/WebRTC controls

## Safety result from the failed physical RC1 run

Even though every RC1 transport failed on the real Mac, macOS System Proxy remained disabled. This confirms the fail-closed activation boundary behaved correctly in that failure scenario.

## Product boundary

`0.3.0-rc2` is still not represented as a packet-level full-device VPN. It provides validated Tor/SOCKS routing, safe macOS System Proxy mode, Selective Chrome, and process-scoped CLI routing. A true full-device VPN remains a separate NetworkExtension milestone.

## Remaining release gate

Only `REAL_TARGET_MAC_ACCEPTANCE_RC2` remains before considering stable `0.3.0`.

The next physical run should focus first on the exact failure path just remediated: install the locked RC2 package, verify identity/version/doctor, run `auto`, and confirm whether a validated Tor route reaches 100%. Browser/crash/reboot acceptance should follow only after the route itself succeeds.

Until physical RC2 acceptance passes, the correct release label remains `0.3.0-rc2`, not stable `0.3.0`.
