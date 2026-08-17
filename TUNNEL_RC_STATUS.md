# DevFix Tunnel 0.3.0-rc3 — Engineering Status Lock

Date: 2026-08-16

Repository: `Shahbazi-Amir/devfix_for_macintel`

Development branch: `feature/devfix-tunnel`

Stable DevFix branch: `main` — READ-ONLY for Tunnel work.

## Exact validated RC3 identity

Final shared gate SHA:

`5142badc0da48953dcc2cdecb6f080ef6fac27e6`

Both official Tunnel workflows passed on this exact SHA.

## Why RC3 replaced RC2

Physical Intel Monterey testing of `0.3.0-rc2` exhausted the full transport catalog and preserved fail-closed System Proxy behavior, but exposed two additional resilience problems.

### REAL_MAC_COLD_DIRECTORY_CACHE_EACH_FALLBACK

Later obfs4 candidates reached 45–50%, obtained bridge descriptors and a usable consensus, but each fallback used a fresh attempt DataDirectory. Because Tor directory cache followed the per-attempt state, useful consensus/cert/microdescriptor progress was discarded when a candidate was terminated.

RC3 keeps disposable per-attempt DataDirectories but introduces a persistent user-owned `CacheDirectory` under DevFix Tunnel state. The cache survives candidate fallback, disconnect, and later sessions. `AvoidDiskWrites 0` allows normal directory cache persistence.

### REAL_MAC_DESCRIPTOR_PHASE_TOO_AGGRESSIVE

Physical RC2 obfs4 candidates 6 and 7 reached `Bootstrapped 50% (loading_descriptors)`. The logs subsequently reported that the current consensus contained exit nodes and Tor could build exit/internal paths, but the controller terminated each candidate after 240 seconds without a percentage change.

RC3 retains short early-failure limits but increases late directory-phase grace:

- initial stage: 90 seconds without progress;
- handshake stage: 180 seconds;
- consensus stage: 360 seconds;
- directory/descriptors stage from >=40%: 900 seconds;
- total attempt ceiling: 1200 seconds.

Late directory stalls are separately classified as `DIRECTORY_INFO_STALL`.

System Proxy remains disabled until bootstrap reaches 100% and routed HTTPS validation passes.

## Physical RC2 safety result

The failed RC2 physical run left `scutil --proxy` in the original non-tunneled state. No Tunnel-owned System SOCKS Proxy was enabled because no transport reached the activation gate. Therefore the failed run did not globally switch the Mac to a dead proxy or change system-wide routed public IP through DevFix Tunnel.

## Official RC3 CI gate

Workflow: `DevFix Tunnel CI`

Run ID: `31968158519`

Head SHA: `5142badc0da48953dcc2cdecb6f080ef6fac27e6`

Result: **PASS**

Validated on Ubuntu and Intel macOS as applicable:

- syntax and ShellCheck: PASS;
- all System Proxy/guardian/restore/conflict tests: PASS;
- Selective Chrome suite: PASS;
- RC2 full-catalog/bridge-policy regressions: PASS;
- RC3 persistent CacheDirectory fallback regression: PASS;
- RC3 cache survives disconnect and a later session: PASS;
- RC3 late-directory bounded grace regression: PASS;
- inherited stable DevFix regression: PASS on Ubuntu and Intel macOS;
- macOS command contract: PASS.

## Official RC3 package gate

Workflow: `DevFix Tunnel Package`

Run ID: `31968158366`

Head SHA: `5142badc0da48953dcc2cdecb6f080ef6fac27e6`

Result: **PASS**

Validated stages:

- official Tor Expert Bundle acquisition and checksum: PASS;
- Tor-aligned GeoIP acquisition/checksum: PASS;
- transport catalog generation: PASS (`snowflake>=2`, `meek>=1`, `obfs4>=7`);
- real packaged Tor parser for Snowflake/meek/obfs4 with GeoIP exit policy and separate CacheDirectory: PASS;
- macOS x86_64 portable archive: PASS;
- macOS x86_64 `.pkg`: PASS;
- install smoke test on Intel macOS: PASS;
- installed version `0.3.0-rc3`: PASS;
- installed persistent CacheDirectory configuration: PASS;
- installed `AvoidDiskWrites 0`: PASS;
- installed descriptor-stage 900-second policy: PASS;
- installed doctor: PASS;
- stable DevFix source remains `2.0.4`: PASS;
- artifact upload: PASS.

## Locked RC3 artifact

GitHub Actions artifact ID: `9269052322`

Artifact name: `DevFixTunnel-0.3.0-rc3-macos-x86_64`

GitHub artifact ZIP digest / independent ZIP SHA-256:

`c7f9e2174cbaaae66c34d63353378c67609a095195218e9504b093339c608b47`

Contained files:

- `DevFixTunnel-0.3.0-rc3-macos-x86_64.pkg`
  - SHA-256: `cc6d1f624a20d4ae3cb8d7c0be0fbf8a26844df87a589a4267f24a9c67a5ae5b`
- `DevFixTunnel-0.3.0-rc3-macos-x86_64.tar.gz`
  - SHA-256: `495d74a8dbeaab863043a4404e7bde697cf3f170fe32b627ecc60fde4b147c75`

Independent verification of `SHA256SUMS.txt`: **PASS** for both package files.

## Product boundary

`0.3.0-rc3` remains a Tor/SOCKS + safe macOS System Proxy/selective-app product, not a packet-level NetworkExtension VPN. Full-device routing remains a separate milestone.

## Physical Intel Monterey acceptance — 2026-08-17

The exact locked RC3 package was installed on the real Intel x86_64 Monterey target and exercised against the target network.

Observed physical results:

- package SHA-256 identity: PASS;
- upgrade/install: PASS;
- `devfix-tunnel version` = `0.3.0-rc3`: PASS;
- `doctor`: PASS;
- SOCKS-only route gate: PASS;
- Snowflake candidate 1 reached Tor bootstrap 100%: PASS;
- routed HTTPS validation through SOCKS: PASS;
- live Tor exit verification returned foreign exit `23.151.8.10` / `us`: PASS;
- System Proxy remained unchanged during the SOCKS-only route gate: PASS;
- System Proxy mode on the active `Wi-Fi` service: PASS;
- ordinary Chrome browsing while System Proxy mode was active: PASS by user observation;
- normal disconnect restored the pre-session System Proxy state: PASS;
- simulated owned Tor-process death triggered guardian degradation `TOR_PROCESS_DIED` and restored `SOCKSEnable` to `0`: PASS;
- `repair` after simulated Tor death returned the controller to `State: DISCONNECTED`, `Mode: NONE`: PASS.

Additional observations:

- the persistent directory cache materially reduced later physical bootstrap time; later Snowflake sessions reused cached directory information and advanced from early handshake stages to `75%`/`100%` rapidly;
- one `devfix-tunnel exit` request during System Proxy acceptance hit a transient LibreSSL `SSL_ERROR_SYSCALL` against `check.torproject.org`; this did not prevent the already-proven SOCKS route, Chrome browsing, System Proxy activation, or safe restoration, but should remain a tracked reliability observation;
- Safari acceptance was not formally recorded as PASS in the captured evidence;
- network-service-change recovery and reboot/orphan recovery remain NOT RUN on the physical target.

## Remaining stable release gate

RC3 core transport, SOCKS routing, System Proxy activation/restoration, and Tor-death fail-safe recovery are physically validated on the target Mac.

Do not promote the product to stable `0.3.0` until the remaining physical acceptance items are explicitly closed:

1. Safari HTTPS browsing while System Proxy mode is active;
2. network-service-change recovery;
3. reboot/orphan recovery;
4. final review of the transient Tor Check SSL reliability observation.

UI work must be isolated from this RC3 core on a separate branch and must call the validated controller rather than duplicating Tor/guardian logic.
