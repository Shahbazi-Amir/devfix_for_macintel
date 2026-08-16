# MASTER ENGINEERING PROMPT — DEVFIX TUNNEL
## Build a Safe, Independent macOS Censorship-Circumvention Product from the Proven DevFix Foundation

> Target development branch: `feature/devfix-tunnel`
>
> Stable source branch: `main`
>
> Primary target: Intel x86_64 Mac / macOS Monterey 12.x
>
> Product working name: **DevFix Tunnel**

---

# 0. Mission

Build a reliable, reversible, security-conscious macOS censorship-circumvention application that reuses the proven networking foundations of DevFix without turning the stable DevFix CLI into a system-wide VPN and without coupling Homebrew/developer-tool behavior to general browser/system routing.

The new product must begin from the current stable `main` foundation but evolve independently on:

```text
feature/devfix-tunnel
```

The product should ultimately support general user traffic such as Safari, Chrome, Firefox, and other applications through a managed local Tor + Snowflake transport, while preserving a clear distinction between:

```text
DevFix          = developer CLI networking helper
DevFix Tunnel   = general macOS censorship-circumvention product
```

Do not break, redesign, or opportunistically refactor stable DevFix behavior merely because this branch originated from DevFix.

---

# 1. Non-Negotiable Branch Policy

`main` is the stable DevFix line.

For this mission:

```text
main = READ-ONLY
feature/devfix-tunnel = WRITE TARGET
```

Never commit, push, merge, force-push, or rewrite `main` while implementing DevFix Tunnel unless the user later gives explicit permission for a specific merge or backport.

Do not create a PR to `main` unless explicitly requested.

Do not merge the tunnel branch into `main` automatically.

Every tunnel commit must remain on:

```text
feature/devfix-tunnel
```

The starting branch SHA must be recorded in project documentation.

Before every write:

```text
verify current branch == feature/devfix-tunnel
verify target repo == Shahbazi-Amir/devfix_for_macintel
```

If either check fails:

```text
STOP
```

Do not attempt a convenient write elsewhere.

---

# 2. Environment Guardrails

The repository guardrails inherited from `main` remain active.

At minimum obey:

```text
docs/guardrails/01_GITHUB_CI_GUARDRAIL.md
docs/guardrails/02_MAC_DEVFIX_HOMEBREW_CLI_GUARDRAIL.md
docs/guardrails/03_GENERAL_EXECUTION_ENVIRONMENT_GUARDRAIL.md
```

Never conflate:

```text
Agent Workspace
User Mac
GitHub Connector/App
GitHub Actions Runner
```

Repository and CI operations should be GitHub-native when possible.

Real local macOS networking acceptance tests must eventually run on the actual target Mac; a Linux GitHub Actions success cannot certify macOS System Proxy, Keychain, NetworkExtension, browser behavior, or local route restoration.

Never ask the user to paste a PAT, password, GITHUB_TOKEN, or private credential into Chat.

---

# 3. Proven DevFix Foundation — Audit Before Reuse

Before implementing tunnel behavior, inspect the current branch and classify every relevant component into exactly one of these categories:

```text
REUSE_AS_IS
ADAPT_BEHIND_NEW_INTERFACE
DO_NOT_REUSE
```

The audit must include at least:

- Tor Expert Bundle packaging
- `lyrebird` / Snowflake transport startup
- Tor configuration generation
- SOCKS listener creation
- bootstrap progress parsing
- PID/process lifecycle management
- state files
- stale-process handling
- tor-data handling
- health checks
- endpoint validation
- retry/timeout behavior
- logging
- diagnostics
- install/uninstall scripts
- GitHub Actions packaging workflows
- architecture/macOS detection
- checksum verification
- proxy handling
- Homebrew wrappers
- Git wrappers
- curl wrappers
- arbitrary command wrappers
- error classification

Do not blindly copy implementation merely because it exists.

Write the audit to a branch-specific design document before major implementation.

---

# 4. Reuse Matrix — Required Initial Engineering Position

Unless source audit proves otherwise, use this as the default architectural position.

## 4.1 Prefer to reuse or extract

These foundations are candidates for reuse:

```text
Tor lifecycle concepts
Snowflake / lyrebird bootstrap
bundled Tor Expert Bundle strategy
upstream checksum verification
bootstrap status parsing
bounded timeouts
process PID validation
safe cleanup concepts
transport health reporting
architecture detection
macOS version detection
log redaction principles
failure-domain classification principles
```

Reuse through a clearly named tunnel component or shared core abstraction rather than making the new app call random DevFix CLI internals.

## 4.2 Adapt, do not copy blindly

These may need new interfaces:

```text
SOCKS endpoint ownership
Tor data directory ownership
state-machine persistence
connection status
restart logic
network-change handling
endpoint validation
crash recovery
installer payload layout
```

Tunnel state must be independent from DevFix state.

## 4.3 Do not use as the core of the tunnel

The following DevFix-specific behavior must not define the new product architecture:

```text
Homebrew wrapper logic
Homebrew compatibility diagnosis
brew-specific environment manipulation
Git-specific wrappers
curl-specific wrappers
process-scoped CLI-only routing
Developer endpoint list as the sole route validation contract
DevFix command naming/state files/PIDs as tunnel state
```

Those features may remain inherited in the repository history, but tunnel implementation should not depend on them.

---

# 5. Product Isolation Contract

DevFix Tunnel must not collide with DevFix.

Use distinct names for all tunnel-owned resources.

Suggested identities:

```text
Product: DevFix Tunnel
CLI: devfix-tunnel
App bundle: DevFix Tunnel.app
Bundle ID: choose a unique project-owned identifier
State root: ~/Library/Application Support/DevFixTunnel
Log root: ~/Library/Logs/DevFixTunnel
Cache root: ~/Library/Caches/DevFixTunnel
PID/state files: tunnel-specific
Launch agent/helper names: tunnel-specific
```

Do not overwrite:

```text
/usr/local/bin/devfix
~/Library/Application Support/DevFix
existing DevFix tor-data
existing DevFix PID/state files
```

Running DevFix and DevFix Tunnel must not corrupt each other.

If simultaneous Tor/SOCKS operation is unsupported, detect it and fail clearly rather than sharing state implicitly.

---

# 6. Product Modes — Build in Phases

Do not claim “full VPN” before a real packet-tunnel architecture exists.

Implement capabilities in explicit phases.

## Phase A — Local transport engine

Deliver a tunnel-owned Tor + Snowflake process exposing a local SOCKS endpoint.

Requirements:

```text
connect
disconnect
status
restart
logs
doctor
```

No system proxy changes yet.

Acceptance requires reliable process lifecycle, bootstrap reporting, bounded timeouts, validation, and cleanup.

## Phase B — macOS System Proxy MVP

Add a reversible system proxy mode using supported macOS network configuration mechanisms.

Goal:

```text
Safari / Chrome / Firefox and applications honoring macOS proxy settings
```

can use the tunnel without manual per-app proxy configuration.

This phase is a **System Proxy mode**, not yet a true packet-level VPN.

## Phase C — Crash-safe and network-change-safe operation

Make proxy state restoration reliable across:

```text
normal disconnect
application crash
Tor crash
Snowflake bootstrap failure
network service change
Wi-Fi reconnect
hotspot change
sleep/wake
system reboot recovery where practical
```

## Phase D — Native macOS GUI / menu-bar app

Add user-facing controls only after backend lifecycle is dependable.

## Phase E — True Packet Tunnel

Evaluate and implement a macOS `NetworkExtension` / `NEPacketTunnelProvider` architecture for actual packet-level routing.

Do not fake a packet VPN by calling System Proxy mode “VPN”.

A NetworkExtension may require Apple signing, entitlements, provisioning, and application packaging. Treat those as explicit dependencies, not implementation details to bypass.

---

# 7. System Proxy MVP Requirements

For the first useful general-user mode, implement a crash-safe macOS proxy manager.

Never hard-code the network service name as `Wi-Fi`.

Discover active/eligible network services with supported macOS tools/APIs.

Before changing anything, snapshot all proxy-related settings that DevFix Tunnel may modify.

The snapshot must capture enough state to restore exactly what existed before connection.

Potential settings include, as applicable:

```text
SOCKS proxy enable state
SOCKS host
SOCKS port
HTTP proxy enable state
HTTP host/port if touched
HTTPS proxy enable state
HTTPS host/port if touched
proxy bypass domains if touched
PAC state if touched
```

Prefer changing the minimum number of settings required.

Do not destroy a user's existing corporate/VPN/proxy configuration.

If an existing proxy configuration is present and safe automatic composition is not possible:

```text
STOP AND REPORT CONFLICT
```

Do not silently overwrite it.

On disconnect, restore the exact snapshot.

Restoration must be idempotent.

Repeated disconnect must be safe.

---

# 8. SOCKS and DNS Design

The local transport endpoint should use an unprivileged localhost port unless a stronger reason exists.

Bind locally only, not on all interfaces.

Default expectation:

```text
127.0.0.1:<dynamic-or-controlled-port>
```

Do not expose an unauthenticated SOCKS proxy to the LAN.

Investigate macOS proxy DNS behavior and browser behavior explicitly.

DNS leakage must be tested rather than assumed absent.

For modes where hostnames are resolved by the application before reaching SOCKS, document limitations accurately.

Do not make unsupported anonymity claims.

---

# 9. Transport State Machine

Implement an explicit connection state machine.

At minimum distinguish:

```text
DISCONNECTED
STARTING
BOOTSTRAPPING
BOOTSTRAPPED
VALIDATING
CONNECTED
DEGRADED
RESTORING
FAILED
```

Do not reduce everything to connected/disconnected.

Bootstrap below 100% and validation-after-100% are different failure classes.

Examples:

```text
Snowflake stalls at 10% or 30%
→ TRANSPORT_BOOTSTRAP_FAILURE

Tor reaches 100% but external route validation fails
→ ROUTE_VALIDATION_FAILURE
```

Persist only the state needed for safe recovery.

On startup, detect stale state and reconcile it with actual process/network state.

State file claims must never override real process/network evidence.

---

# 10. Snowflake Reliability Model

Snowflake is stochastic.

Do not interpret one failed session as proof of a code defect.

Use bounded retries with explicit reason codes.

Each retry must be a deliberate new attempt, not an infinite loop.

Record:

```text
attempt number
bootstrap milestones
elapsed wall-clock time
failure class
whether Tor process survived
whether SOCKS became reachable
validation result
```

Do not reset persistent Tor state automatically on every failure.

If fresh tor-data is required for recovery:

```text
backup/quarantine old data
create fresh state
verify recovery
only then consider deleting old backup
```

Never destroy useful diagnostic state before a root cause can be inspected.

---

# 11. Wall-Clock Timeout Contract

Timeouts must use real elapsed wall-clock/monotonic time.

Do not implement a timeout by counting polling iterations and assuming sleep duration was exact.

Each long operation must have:

```text
start timestamp
current timestamp
bounded deadline
clear timeout error
```

Transport bootstrapping, route validation, cleanup, and restoration must not hang indefinitely.

---

# 12. Route Validation

General tunnel validation must not be limited to Homebrew/GitHub endpoints.

Design validation in layers.

Example layers:

```text
L1: local Tor process alive
L2: local SOCKS listener reachable
L3: SOCKS TCP request succeeds
L4: DNS/hostname path behaves as expected
L5: known HTTPS endpoint succeeds with valid TLS
L6: optional exit-IP observation succeeds
```

Use more than one validation endpoint where practical to avoid a single third-party outage being classified as tunnel failure.

Do not disable certificate verification.

Do not use `curl -k` as production behavior.

An HTTP `401` or another expected authenticated response may prove transport reachability if the endpoint contract explicitly expects it; distinguish reachability from application authorization.

---

# 13. Exit IP Display

The product may optionally display the current observed public exit IP.

If implemented:

- query through the active tunnel;
- use reputable, replaceable endpoints;
- tolerate endpoint failure;
- never treat exit-IP lookup as the sole connection criterion;
- state clearly that an observed exit IP is not a guarantee of anonymity.

Do not expose the user's direct public IP unnecessarily in logs.

---

# 14. macOS Network Service Discovery

System Proxy mode must support realistic macOS configurations.

Test at least:

```text
Wi-Fi
Ethernet when available
USB/tethering network service
multiple configured services
inactive services
service renaming
```

Do not assume the first listed network service is active.

Before changing proxy state, determine the relevant active service(s) deliberately.

If there is ambiguity, fail safely or request user selection through the UI/CLI rather than modifying every service blindly.

---

# 15. Existing Proxy Conflict Policy

Before enabling Tunnel System Proxy mode, inspect existing settings.

Classify them:

```text
NONE
OWNED_BY_DEVFIX_TUNNEL
THIRD_PARTY_PROXY
PAC_CONFIGURATION
UNKNOWN_CONFLICT
```

Only modify automatically when ownership/restoration is unambiguous.

For a third-party proxy/PAC/VPN conflict:

- do not overwrite it silently;
- report the exact conflict;
- preserve the original settings;
- provide an explicit safe user choice if a supported coexistence mode exists.

---

# 16. Privilege Boundary

Avoid running the whole application as root.

Use least privilege.

If privileged network changes require authorization, isolate them in the smallest possible helper/action.

Never use:

```text
chmod 777
disabled SIP
disabled Gatekeeper
persistent password storage
sudo password captured by the app
```

If a privileged helper is introduced later, define:

```text
strict command surface
input validation
code-signing requirements
ownership and permissions
IPC authorization
upgrade/uninstall behavior
```

---

# 17. Security Requirements

Non-negotiable:

```text
TLS verification remains enabled
no custom root CA installation
no `/etc/hosts` manipulation
no global DNS corruption
no disabling SIP
no disabling Gatekeeper
no disabling firewall/security controls
no secret/token logging
no credential hard-coding
```

The local SOCKS listener must not be reachable from other machines.

Temporary files must have safe permissions.

Logs must redact sensitive proxy credentials and avoid full browsing-history logging.

Do not log every destination hostname by default.

---

# 18. Privacy Model

Document accurately what the tunnel protects and what it does not.

Do not promise:

```text
perfect anonymity
zero DNS leaks without evidence
protection against malware
protection from endpoint compromise
guaranteed availability
full traffic routing in System Proxy mode
```

Clearly distinguish:

```text
System Proxy mode
vs
Packet Tunnel mode
```

If an application ignores system proxy settings, System Proxy mode may not route it.

That limitation must be visible in docs/UI.

---

# 19. Native GUI Strategy

Do not start with a large GUI rewrite.

First build a testable backend API/CLI.

Suggested backend commands:

```text
devfix-tunnel connect
devfix-tunnel disconnect
devfix-tunnel status
devfix-tunnel restart
devfix-tunnel doctor
devfix-tunnel logs
devfix-tunnel proxy status
devfix-tunnel proxy restore
devfix-tunnel transport test
devfix-tunnel ip
```

The future GUI/menu-bar app should call a well-defined backend/service interface rather than duplicate Tor and state logic.

Initial GUI should expose only reliable operations:

```text
Connect
Disconnect
Status
Mode
Current route/exit indicator
Diagnostics
```

Avoid feature-heavy UI before lifecycle safety is proven.

---

# 20. NetworkExtension / Packet Tunnel Phase

True system-wide packet routing should be treated as a separate engineering milestone.

Research current Apple documentation at implementation time because APIs, entitlements, signing, and deployment requirements can change.

Use primary Apple documentation for technical decisions.

Do not invent entitlement availability.

Expected design space includes:

```text
NetworkExtension framework
NEPacketTunnelProvider
app + extension architecture
packet routing
DNS settings
IPv4/IPv6 routes
sleep/wake lifecycle
provider IPC
signing/provisioning
```

If Apple Developer signing or entitlement access becomes a hard requirement, report it as a real dependency rather than weakening macOS security.

Do not call the project blocked until supported non-packet System Proxy mode is independently functional.

---

# 21. IPv4 and IPv6

Do not assume IPv6 is absent.

Test explicitly.

For each connection mode determine:

```text
IPv4 route behavior
IPv6 route behavior
DNS behavior
whether IPv6 can bypass the intended proxy/tunnel
```

If a mode cannot safely handle IPv6, document it and design a supported mitigation rather than silently claiming full coverage.

Do not globally disable IPv6 as a casual workaround.

---

# 22. Kill-Switch Policy

Do not implement a dangerous “kill switch” early by corrupting default routes or firewall rules.

If a future kill-switch is desired, treat it as a separate feature with:

```text
explicit opt-in
reversible changes
crash recovery
reboot recovery
network-change handling
clear ownership markers
unit/integration tests
manual escape instructions
```

MVP should prefer safe disconnect/restoration over aggressive network blocking.

---

# 23. Crash Recovery Contract

System Proxy mode must be designed so that a crash does not permanently leave the Mac pointing at a dead localhost proxy.

Required strategy:

1. Snapshot original settings before modification.
2. Persist tunnel-owned restore metadata atomically.
3. Mark ownership only after snapshot is durable.
4. Apply proxy settings.
5. On normal disconnect, restore and clear ownership state.
6. On startup, detect incomplete prior session.
7. If the proxy still points to DevFix Tunnel and the tunnel is not healthy, restore the prior snapshot.
8. Never restore over settings that changed externally after the snapshot without conflict detection.

Add an emergency command:

```text
devfix-tunnel proxy restore
```

that safely repairs only settings demonstrably owned by DevFix Tunnel.

---

# 24. Atomic State Writes

All important state files must use atomic replace semantics.

Avoid partial JSON/text writes that can leave recovery impossible after a crash.

Store:

```text
schema version
tunnel session id
owned process ids
ports
network service identifier/name
pre-change proxy snapshot
post-change expected proxy state
timestamps
```

Do not store secrets unless genuinely required.

If schema changes, implement migration or fail clearly.

---

# 25. Process Ownership

Never kill a process merely because its executable name is `tor` or `lyrebird`.

Before terminating anything, prove ownership using combinations such as:

```text
recorded PID
process start identity/time if available
expected executable path
session-specific torrc/state path
parent/session metadata
```

Do not terminate Tor Browser or another user's Tor service.

---

# 26. Port Ownership

Do not assume a hard-coded SOCKS port is free.

Either:

```text
allocate an available controlled port
```

or safely detect conflicts.

Store the selected port in session state.

Never kill an unrelated process to reclaim a port automatically.

---

# 27. Tor Data Isolation

DevFix Tunnel must use a separate Tor data directory from DevFix.

Recommended structure:

```text
~/Library/Application Support/DevFixTunnel/tor-data
```

Set restrictive permissions.

Do not reuse DevFix `tor-data` directly.

Do not destroy Tor state on ordinary disconnect.

Provide explicit repair/rotate behavior with backup semantics.

---

# 28. Installer and Packaging Isolation

Do not overwrite the stable DevFix package identity.

Create distinct assets, for example:

```text
DevFixTunnel-<version>-macos-x86_64.pkg
DevFixTunnel-<version>-macos-x86_64.tar.gz
```

Use distinct install destinations where appropriate.

If shared upstream Tor binaries are packaged, preserve license notices and checksum verification.

Never silently download unverified executable binaries at runtime when they can be securely bundled at release build time.

---

# 29. Versioning

DevFix Tunnel must have its own version line.

Do not call the first tunnel build DevFix `2.0.5` simply because DevFix is 2.x.

Example:

```text
DevFix Tunnel 0.1.0-alpha
```

Keep product version and stable DevFix version independent.

---

# 30. Repository Layout

Prefer a clearly isolated branch structure such as:

```text
tunnel/
  core/
  macos/
  cli/
  app/
  tests/

docs/tunnel/
packaging/tunnel/
scripts/tunnel/
```

Do not scatter tunnel code through Homebrew wrapper functions unless a shared abstraction is truly appropriate.

A shared core can be extracted only after proving the extraction does not alter stable DevFix semantics.

Because `main` is read-only during tunnel work, shared-core extraction should initially happen only on the tunnel branch.

---

# 31. Phase 0 — Repository and Architecture Audit

Before writing product behavior:

1. Record branch and base SHA.
2. Inventory repo structure.
3. Read current `README.md`, `SECURITY.md`, tests, packaging, workflows, and `bin/devfix`.
4. Identify all Tor/Snowflake lifecycle code.
5. Identify all DevFix-specific Homebrew/Git/curl code.
6. Produce the reuse matrix.
7. Identify state paths and collision risks.
8. Identify licensing/third-party bundle requirements.
9. Identify currently supported macOS target assumptions.
10. Write architecture decision records for System Proxy MVP and later Packet Tunnel.

Do not begin by editing `bin/devfix` indiscriminately.

---

# 32. Phase 1 — Tunnel Transport Core

Build a tunnel-owned transport core with automated tests.

Required capabilities:

```text
start bundled Tor + Snowflake
select local SOCKS port
report bootstrap progress
real wall-clock timeout
validate SOCKS route
status
restart
disconnect
owned-process cleanup
stale-state recovery
separate logs/state/data dirs
```

No macOS System Proxy modification until this phase passes.

Acceptance test on target Mac:

```text
connect reaches 100%
SOCKS request succeeds
disconnect leaves no owned listener/process
stable DevFix still functions independently
```

---

# 33. Phase 2 — System Proxy MVP

After transport core PASS:

1. Detect active network service.
2. Snapshot current proxy configuration.
3. Enable only required proxy settings pointing to tunnel SOCKS.
4. Verify Safari/Chrome/Firefox HTTPS reachability through the tunnel.
5. Verify observed exit differs where appropriate.
6. Disconnect.
7. Restore exact prior proxy settings.
8. Verify direct browsing returns.

Test with pre-existing proxy settings before release.

---

# 34. Phase 3 — Recovery and Resilience

Test intentionally hostile lifecycle events:

```text
kill Tor while connected
kill devfix-tunnel process
close Terminal
sleep/wake Mac
change Wi-Fi
switch to hotspot
internet disappears during bootstrap
Snowflake stalls below 100%
validation endpoint fails
port becomes occupied
proxy settings changed externally mid-session
```

The goal is not “never fail.”

The goal is:

```text
fail safely
report accurately
restore owned system state
never strand the user offline because of stale proxy settings
```

---

# 35. Phase 4 — GUI

Only after backend phases pass on real Mac:

- build menu-bar app or small native UI;
- keep UI thin;
- display true backend state;
- do not fake “Connected” before validation;
- show bootstrap progress;
- show recoverable failure details;
- include a Restore Network Settings action limited to tunnel-owned state.

Accessibility and readable status text are required.

---

# 36. Phase 5 — Packet Tunnel

After System Proxy product is stable:

- research Apple NetworkExtension requirements using current primary docs;
- document signing/entitlement prerequisites;
- prototype PacketTunnelProvider separately;
- add routes/DNS carefully;
- maintain a clean rollback path;
- retain System Proxy mode as a fallback if appropriate.

Do not delete the working proxy product merely because Packet Tunnel is more elegant.

---

# 37. Testing Strategy

Maintain multiple layers.

## Unit tests

Test:

```text
state transitions
time calculations
proxy snapshot serialization
proxy restore diff logic
PID ownership validation
port parsing
bootstrap parser
failure classification
redaction
```

## Integration tests without changing real system network

Use fixtures/mocks for:

```text
networksetup output
existing proxy configurations
multiple network services
crash-recovery state
Tor logs
```

## Real Mac acceptance tests

Run only when required and with explicit reversible steps.

Validate:

```text
Intel x86_64
macOS Monterey 12.x
Safari
Chrome
Firefox
IPv4
IPv6 behavior
DNS behavior
sleep/wake
Wi-Fi reconnect
hotspot/network change
existing proxy conflict
normal disconnect
forced crash recovery
```

Never claim real Mac PASS from GitHub Actions alone.

---

# 38. CI Strategy

GitHub Actions should verify repository-centric behavior:

```text
shell/static checks
unit tests
fixtures
packaging integrity
checksum verification
linting
security scans when appropriate
artifact reproducibility
```

Use minimum `GITHUB_TOKEN` permissions.

Do not require local `gh` for CI.

Use macOS GitHub runners only when they genuinely test portable macOS code; still distinguish them from the user's Monterey Intel hardware because runner OS/hardware may differ.

---

# 39. Download and Supply-Chain Security

For Tor/lyrebird/third-party runtime payloads:

- use authoritative upstream source;
- pin expected version in release tooling;
- verify published checksum/signature where available;
- fail closed on mismatch;
- record source/version/license;
- preserve `THIRD_PARTY_NOTICES`.

Do not silently switch to untrusted mirrors.

Do not disable TLS verification because an upstream fetch fails.

---

# 40. Logs and Diagnostics

Logs should answer lifecycle questions without becoming browsing-history surveillance.

Record:

```text
session id
product version
OS/arch
selected mode
transport state transitions
bootstrap milestones
owned PIDs/ports where safe
network service identifier
proxy ownership transitions
error class
elapsed times
restore result
```

Do not log:

```text
passwords
tokens
proxy credentials
full browsing URLs by default
full destination history
```

Add redaction tests.

---

# 41. Doctor Command

`devfix-tunnel doctor` should distinguish environment problems.

Potential output areas:

```text
OS/architecture support
bundled Tor/lyrebird presence
binary integrity
writable state dirs
port availability
network service discovery
current proxy state
stale tunnel ownership state
transport direct/Snowflake reachability
existing proxy/PAC conflicts
system clock sanity when relevant
```

Do not attribute censorship as a certainty from a failed endpoint probe.

Use wording such as:

```text
BLOCKED_OR_UNREACHABLE
```

unless stronger evidence exists.

---

# 42. Error Model

Use explicit machine-readable failure classes.

At minimum consider:

```text
UNSUPPORTED_OS
UNSUPPORTED_ARCH
TRANSPORT_BINARY_MISSING
TRANSPORT_INTEGRITY_FAILURE
SNOWFLAKE_BOOTSTRAP_FAILURE
TOR_PROCESS_FAILURE
SOCKS_LISTENER_FAILURE
ROUTE_VALIDATION_FAILURE
DNS_BEHAVIOR_FAILURE
PROXY_DISCOVERY_FAILURE
EXISTING_PROXY_CONFLICT
PROXY_APPLY_FAILURE
PROXY_RESTORE_FAILURE
STALE_STATE_CONFLICT
PORT_CONFLICT
PERMISSION_DENIED
NETWORK_CHANGED
TIMEOUT
UNKNOWN
```

Errors should include safe next action.

---

# 43. No False Success

Never report `CONNECTED` only because Tor printed 100%.

Required connection success contract:

```text
transport bootstrapped
AND local listener validated
AND configured routing mode successfully applied
AND route validation passed
```

For System Proxy mode, also verify expected proxy settings are active.

If validation is partial:

```text
DEGRADED
```

not `CONNECTED`.

---

# 44. No False “VPN” Label

Before Packet Tunnel phase exists and passes:

Use labels such as:

```text
Tunnel
System Proxy
Snowflake Route
```

Do not market System Proxy mode as a full-device VPN.

When Packet Tunnel exists, document exactly which traffic/routes it covers.

---

# 45. Performance

Tor/Snowflake can be slow.

Measure rather than promise speed.

Track:

```text
bootstrap time
validation time
request latency
large-download throughput where useful
failure/retry counts
```

Do not optimize throughput by weakening TLS or bypassing validation.

Avoid routing traffic through Snowflake when the user selected a direct mode that is already valid, if direct mode is part of the product design.

---

# 46. Direct Mode

If DevFix Tunnel offers direct/bypass mode, make its semantics explicit.

Possible modes:

```text
DIRECT
SNOWFLAKE
AUTO
```

`AUTO` must not silently claim censorship detection from a single timeout.

It may decide based on reachability/health, but diagnostics should say what was observed rather than asserting why a network failed.

---

# 47. External Proxy Support

External proxy support can be retained as an optional transport adapter, but it must not become required for normal use.

Credentials in proxy URLs must be redacted.

Do not store proxy credentials in plaintext unless explicitly required and securely designed.

Built-in Snowflake remains the primary no-external-VPS path.

---

# 48. Compatibility Priority

Primary acceptance platform:

```text
MacBookPro11,4 class Intel hardware
macOS Monterey 12.x
x86_64
```

Do not abandon Monterey simply because CI runs on newer macOS.

Architect code so later support for Apple Silicon is possible:

```text
architecture-specific payload selection
no unnecessary x86 assumptions in high-level state logic
separate package artifacts when needed
```

But do not claim Apple Silicon support until tested.

---

# 49. Existing DevFix Regression Protection

Even though development occurs on a separate branch, inherited DevFix behavior must not be accidentally destroyed without reason.

Run existing test suites regularly.

Any intentional change to inherited DevFix code must include:

```text
why tunnel needs it
why isolation was not enough
regression tests
impact on devfix CLI in this branch
```

Prefer adding new tunnel code over rewriting stable DevFix code.

---

# 50. Git Discipline

Before each logical commit:

```text
verify branch
inspect diff
run relevant tests
git diff --check
ensure no secrets
```

Use focused commit messages.

Do not bundle unrelated cleanup into security/network lifecycle commits.

Do not force-push unless explicitly authorized.

At milestones report:

```text
branch
commit SHA
files changed
tests run
known limitations
next gate
```

---

# 51. Release Gate

Do not produce a user-facing tunnel release merely because it compiles.

A System Proxy alpha release requires at minimum:

```text
transport core PASS
connect/disconnect PASS
real SOCKS validation PASS
proxy snapshot PASS
proxy apply PASS
proxy restore PASS
crash recovery PASS
existing proxy conflict protection PASS
Safari PASS
Chrome PASS
Firefox PASS or documented blocker
IPv4 behavior documented
IPv6 behavior tested/documented
DNS behavior tested/documented
no stale proxy after normal disconnect
no stale proxy after tested crash case
existing DevFix unaffected
installer/uninstaller tested
security checklist PASS
```

If any critical restoration test fails:

```text
RELEASE = NO
```

---

# 52. Packet Tunnel Release Gate

A future true Packet Tunnel release additionally requires:

```text
Apple entitlement/signing requirements resolved
PacketTunnelProvider lifecycle tested
route table verified
DNS settings verified
IPv4 verified
IPv6 verified
sleep/wake verified
network-change verified
extension crash behavior verified
uninstall/disable behavior verified
```

Do not infer these from System Proxy tests.

---

# 53. Forbidden Shortcuts

Never solve development problems with these shortcuts:

```text
disable SIP
disable Gatekeeper
disable TLS verification
curl -k in production
install arbitrary root CA
chmod 777
kill all tor processes
hard-code Wi-Fi service name
overwrite existing proxy without snapshot
leave proxy enabled after failure
call System Proxy a full VPN
reuse DevFix state directory
share DevFix PID/state files
request PAT/password in Chat
make `main` changes without explicit user authorization
```

---

# 54. Root-Cause Rule

When a test fails:

1. Preserve exact output.
2. Classify the failure domain.
3. Identify the layer that failed.
4. Form a specific hypothesis.
5. Change only what tests that hypothesis.
6. Re-run relevant lower-level and regression tests.

Do not enter:

```text
change random setting
→ rerun
→ change unrelated setting
→ reinstall everything
```

loops.

---

# 55. Documentation Requirements

Maintain branch-specific documentation under:

```text
docs/tunnel/
```

At minimum create over time:

```text
ARCHITECTURE.md
REUSE_MATRIX.md
STATE_MACHINE.md
SYSTEM_PROXY_DESIGN.md
SECURITY_MODEL.md
RECOVERY_MODEL.md
TEST_PLAN.md
KNOWN_LIMITATIONS.md
NETWORK_EXTENSION_PLAN.md
```

Documentation must reflect actual implementation, not aspirational claims presented as finished features.

---

# 56. Initial Deliverables — Before Large Implementation

The first development milestone after this prompt must produce:

1. Repository audit.
2. Reuse matrix.
3. Tunnel directory structure.
4. Separate tunnel state/config/log path contract.
5. State-machine design.
6. System Proxy design with snapshot/restore algorithm.
7. Threat/security model.
8. Test plan.
9. Minimal tunnel-owned CLI skeleton.
10. Tests proving no collision with stable DevFix paths.

Do not build a GUI before these exist.

---

# 57. First Functional Milestone

The first real functional milestone must be:

```text
devfix-tunnel connect
→ starts tunnel-owned Snowflake/Tor
→ reaches bootstrap completion
→ validates local SOCKS route
→ reports CONNECTED

devfix-tunnel status
→ reports actual state

devfix-tunnel disconnect
→ terminates only owned processes
→ leaves DevFix untouched
```

No system proxy changes in this milestone.

This creates a safe foundation for later general browser routing.

---

# 58. Second Functional Milestone

Only after Milestone 1 passes on target Mac:

```text
devfix-tunnel connect --mode system-proxy
```

should:

1. start the transport;
2. validate SOCKS;
3. snapshot the relevant network service proxy state;
4. apply tunnel-owned proxy state;
5. validate routed HTTPS;
6. report connected.

Then:

```text
devfix-tunnel disconnect
```

must restore the exact prior proxy state.

If restore cannot be guaranteed:

```text
MILESTONE 2 = FAIL
```

---

# 59. Human Acceptance on Target Mac

For dangerous/reversible network-state milestones, final acceptance requires real user-Mac evidence.

Provide one complete copy-paste test block whenever practical.

Do not repeatedly ask for one command at a time if the test can safely be grouped.

The test block must state:

```text
what will change
what success looks like
what failure looks like
how recovery works
```

If network restoration is not yet proven, do not ask the user to run a test that may strand connectivity without an emergency restore path.

---

# 60. Final Engineering Principle

The project must optimize for:

```text
reliability
reversibility
isolation
clear ownership
accurate status
security
real macOS behavior
```

not merely “traffic passed once.”

The hardest requirement is not starting Tor.

The hardest requirement is ensuring that every connection, failure, crash, network change, and disconnect leaves the user's Mac in a known, recoverable state.

---

# 61. Immediate Agent Instructions

Start work in this exact order:

```text
1. Verify repository and branch.
2. Record the branch base SHA from stable main.
3. Read all inherited guardrails.
4. Audit current DevFix source/tests/package layout.
5. Produce REUSE_MATRIX.md.
6. Produce ARCHITECTURE.md.
7. Produce STATE_MACHINE.md.
8. Produce SYSTEM_PROXY_DESIGN.md.
9. Produce SECURITY_MODEL.md.
10. Produce TEST_PLAN.md.
11. Create isolated `tunnel/` implementation skeleton.
12. Add collision/regression tests.
13. Implement transport-core milestone only.
14. Run repository/CI tests.
15. Report evidence and unresolved risks.
16. Only after transport-core acceptance, begin System Proxy mode.
```

Do not jump directly to GUI.

Do not jump directly to NetworkExtension.

Do not modify `main`.

Do not claim a full VPN before the Packet Tunnel gate is actually passed.

---

# 62. Required End-of-Milestone Report

Every milestone report must include:

```text
Repository
Branch
Base SHA
Final branch SHA

Files changed
Architecture decisions
What was reused from DevFix
What was intentionally isolated

Tests run
Test results
CI run IDs
Real Mac tests run/not run

Transport status
Proxy state changes, if any
Restoration status
Security checks

Known limitations
Unverified assumptions
Next allowed milestone
```

If a required test has not been run, say:

```text
NOT VERIFIED
```

Never silently convert missing evidence into PASS.

---

# FINAL CONTRACT

```text
Stable DevFix must remain stable.
DevFix Tunnel must own its own state, processes, proxy configuration, packaging, and lifecycle.
System Proxy mode is not a full VPN.
True full-device routing requires a real Packet Tunnel architecture.
Every system-network change must be reversible and ownership-aware.
No security protection is disabled to make development easier.
No `main` write occurs without explicit future user permission.
```

Begin with architecture/audit and the isolated transport core, not with a GUI and not with a destructive system-wide network hack.
