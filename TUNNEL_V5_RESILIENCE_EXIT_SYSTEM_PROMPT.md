# MASTER ENGINEERING PROMPT — DEVFIX TUNNEL V5 RESILIENCE / EXIT / SYSTEM COVERAGE

Date: 2026-08-16
Repository: `Shahbazi-Amir/devfix_for_macintel`
Branch: `feature/devfix-tunnel`
Stable branch: `main` — READ-ONLY

## Evidence that triggers V5

Physical Intel macOS Monterey 12.7.6 acceptance produced two independent real Snowflake failures. Both reached pluggable transport and broker rendezvous, then repeatedly failed with `timeout waiting for DataChannel.OnOpen` and stalled at 10% until the bounded 180s stall timeout. System Proxy remained unchanged and safe after failure/repair.

The packaged Tor Expert Bundle already contains `pt_config.json` with current Tor-maintained built-in bridge definitions: two Snowflake bridge configurations, meek_lite, obfs4, webtunnel plugin registration, and conjure metadata. RC1 incorrectly hard-coded a legacy Snowflake bridge instead of consuming the current bundle configuration.

## Mission

Build the next release candidate so a restrictive network is not dependent on one hard-coded Snowflake rendezvous/WebRTC path. Increase application coverage without falsely claiming full packet-level VPN behavior, add foreign-exit policy controls, and preserve all proxy ownership/recovery guarantees.

## Version

Product-byte changes in this prompt require a new candidate: `0.3.0-rc1`.

## Mandatory V5 changes

### 1. Bundle-native transport catalog

- Remove the hard-coded Snowflake bridge as the default source of truth.
- During package build, parse the exact bundled `pluggable_transports/pt_config.json` and generate a simple immutable runtime catalog under the Tunnel namespace.
- Record source bundle version/hash in the generated catalog metadata.
- Runtime must not require jq or Python.

### 2. Auto transport fallback

`connect` defaults to transport `auto` with bounded attempts:

1. current bundled Snowflake bridge A;
2. current bundled Snowflake bridge B;
3. current bundled meek_lite bridge;
4. bounded subset of current bundled obfs4 built-ins.

Each attempt owns a fresh Tor process, fresh torrc, separate attempt log, and a fresh per-attempt Tor data directory. Failed attempts must be stopped before moving to the next candidate.

No System Proxy mutation is allowed before one candidate reaches Tor bootstrap 100% and routed HTTPS validation passes.

Do not retry the exact same failed candidate indefinitely.

### 3. Explicit transport control

Support:

- `--transport auto`
- `--transport snowflake`
- `--transport meek`
- `--transport obfs4`

Status must report the successful transport and candidate index.

### 4. Failure classification

Classify the transport failure based on evidence. At minimum distinguish:

- `SNOWFLAKE_WEBRTC_DATACHANNEL_FAILURE`
- `BROKER_RENDEZVOUS_FAILURE`
- `TRANSPORT_PROCESS_FAILURE`
- `BOOTSTRAP_STALL`
- `ROUTE_VALIDATION_FAILURE`
- `ALL_TRANSPORTS_FAILED`

Keep per-attempt logs so failures are diagnosable after fallback succeeds.

### 5. GeoIP packaging and foreign-exit policy

Package Tor IPv4/IPv6 GeoIP databases from an official Tor Project release aligned with the bundled Tor core version and verify the download checksum.

Support:

- default `--foreign-only` behavior that excludes Iran exits and unknown-country exits;
- `--allow-any-exit` opt-out;
- `--exit-country <cc>` as a preferred exit-country request;
- a small default preferred foreign pool may be offered, but documentation must not claim exact country guarantee unless post-connect verification proves it.

Foreign-only is a safety/circumvention policy, not anonymity marketing.

### 6. Exit identity command

Add `devfix-tunnel exit`.

It must query the Tor Project Tor Check API through the local SOCKS route, require `IsTor=true`, extract the public exit IP, and map IPv4 to the packaged local GeoIP database when possible. Report:

- exit IP;
- detected country code when known;
- whether foreign-only policy is satisfied.

Do not log exit identity persistently by default.

### 7. Process-scoped CLI coverage

Add `devfix-tunnel run <command> [args...]` for tools that do not reliably consume macOS System Proxy but honor standard proxy variables. It must export only to the child process:

- `ALL_PROXY=socks5h://127.0.0.1:<port>`
- `all_proxy=...`

Do not globally mutate shell startup files.

### 8. System Proxy coverage remains honest

Current `system` mode continues to use safe macOS System SOCKS Proxy and can cover Safari, Chrome, VS Code/Electron and other applications that honor macOS proxy settings. Do not state that every process/UDP packet is tunneled.

### 9. Full-device VPN track

Create a separate architecture document for a future NetworkExtension/`NEPacketTunnelProvider` implementation.

Do not block V5 System Proxy product on that track.

Document that Apple requires the `com.apple.developer.networking.networkextension` entitlement and an appropriately signed/provisioned app for a real Packet Tunnel Provider. Until those signing inputs exist and a packet forwarding engine is implemented, do not label V5 as a full-device VPN.

### 10. Network-outage truthfulness

Document that no VPN/proxy can create external connectivity when the underlying network has no reachable path to any outside rendezvous/server. Multi-transport fallback improves censorship/NAT resilience; it cannot defeat a physically or nationally disconnected upstream with zero reachable external path.

## Safety invariants

Preserve all RC1/V4 guarantees:

- fail-closed System Proxy activation;
- snapshot before proxy mutation;
- restore only tunnel-owned proxy state;
- do not overwrite third-party proxy/PAC state;
- Tor PID ownership proof;
- user/root marker boundary;
- crash/reboot recovery;
- main remains untouched;
- no SIP/Gatekeeper/TLS disabling;
- no chmod 777;
- no PAT/password collection.

## CI gates

Mandatory automated gates before physical-Mac retest:

- bash syntax PASS;
- ShellCheck PASS without suppressing new findings;
- generated transport catalog includes >=2 snowflake candidates, meek and obfs4 from the exact bundle;
- legacy hard-coded Snowflake bridge is not the runtime default;
- auto fallback advances after controlled candidate failure;
- no System Proxy activation before transport validation;
- per-attempt state/data directories are isolated;
- foreign-only torrc includes GeoIP files and Iran/unknown exclusion policy;
- exit-country input validation;
- `run` child environment tests;
- all prior guardian/restore/conflict tests PASS;
- inherited stable DevFix tests PASS on Ubuntu and Intel macOS;
- package smoke test PASS on Intel macOS;
- package contains bridge catalog + geoip + geoip6;
- stable DevFix source preservation PASS.

## Physical target gate after CI/package

Do not ask the user to retest until a new exact package SHA is locked.

On the physical Monterey Mac, first test default `auto` transport. Record which transport succeeds. Only after transport + route validation pass may System Proxy/browser tests continue.

If Snowflake repeats DataChannel failure but meek or obfs4 succeeds, V5 transport fallback is considered to have solved the real failure class.

## Final release wording

Correct pre-acceptance label: `0.3.0-rc1`.

Do not promote to stable until real target tests cover connect, exit policy, Safari, Chrome, representative app/CLI, disconnect restore, Tor crash, and reboot/orphan recovery.
