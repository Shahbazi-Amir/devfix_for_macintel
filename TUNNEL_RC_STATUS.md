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

## Remaining release gate

The remaining gate before stable `0.3.0` is `REAL_TARGET_MAC_ACCEPTANCE_RC3` on the actual Intel Monterey target.

The first RC3 physical run should stop at the route gate: exact package identity, safe upgrade, doctor, auto transport bootstrap, and live exit verification. Browser/crash/reboot acceptance follows only after a transport reaches 100% and HTTPS validation succeeds.
