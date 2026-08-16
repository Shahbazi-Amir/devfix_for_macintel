# Mac / DevFix / Homebrew / CLI Guardrail
## Permanent Agent Constraint — Intel Monterey Package and Developer Tool Operations

Use this guardrail before any local Mac task involving Homebrew, DevFix, curl, Git, GitHub CLI, FFmpeg, FFprobe, Ruby, Python, Node, build tools, package installation, dependency download, or CLI upgrades.

## 1. Scope and target machine

This project targets an Intel/x86_64 Mac running macOS Monterey 12, with Homebrew under `/usr/local`. Treat Homebrew on macOS 12 as compatibility-sensitive. A Tier 3 warning is not itself a failure.

Do not automatically remove Homebrew, switch package managers, upgrade macOS, reinstall Xcode/CLT, or weaken macOS security because Homebrew reports Monterey/Tier 3.

## 2. Separate environments

Never assume the User Mac shares credentials, binaries, PATH, files, cache, network route, or package state with Agent Workspace, GitHub Actions Runner, or GitHub Connector/App.

## 3. Default Homebrew route

For Homebrew operations on this Mac prefer:

```bash
devfix brew <command>
```

Examples:

```bash
devfix brew update
devfix brew outdated
devfix brew install <formula>
devfix brew cleanup
devfix brew doctor
```

Use raw `brew` only for a deliberate diagnostic or when explicitly justified.

## 4. Upgrade policy

Never recommend blind `brew upgrade` / `devfix brew upgrade` before:

```bash
devfix brew outdated
```

If nothing is outdated, a bulk upgrade is unnecessary. `brew update` refreshes metadata; `brew upgrade` upgrades installed Homebrew-managed packages.

## 5. Diagnose the failure domain first

Classify a failure before retrying:

```text
A. Network / proxy / TLS
B. Snowflake bootstrap
C. Route validation
D. Formula metadata
E. Upstream URL / HTTP 404 / 405
F. Source-build requirement
G. macOS/SDK/compiler compatibility
H. Dependency failure
I. Package-manager ownership/link conflict
```

Do not translate every download failure into “the internet is broken.” A formula URL returning 404/405 or a source build failing on Monterey may be an upstream/compatibility issue rather than DevFix.

## 6. DevFix / Snowflake rules

Connect with:

```bash
devfix connect snowflake
```

Treat it as successful only after:

```text
Connected with built-in Snowflake.
```

and after the shell prompt returns. Do not type the next command while startup is still running.

Disconnect with:

```bash
devfix disconnect
```

Use routed wrappers as appropriate:

```bash
devfix brew ...
devfix git ...
devfix curl ...
devfix run ...
```

## 7. Snowflake failure classification

Failure below 100% is a bootstrap/transport failure. Reaching 100% and then failing endpoint validation is a route-validation failure. Do not conflate them.

Snowflake is stochastic; one bad session is not enough reason to reinstall DevFix, cut a new DevFix release, change Tor settings, or wipe unrelated configuration. Read the exact stage/log first and use bounded, hypothesis-driven retries.

## 8. Tor state/cache

Do not casually delete persisted Tor state. If fresh-state testing is required, backup/quarantine existing `tor-data`, create a fresh directory, preserve the backup until replacement is verified, then clean up intentionally.

## 9. Direct vs Homebrew-managed tools

Never assume a command in `/usr/local/bin` is Homebrew-managed. Before install/upgrade, check the executable path, version, and package-manager ownership when appropriate.

A tool may have been installed by Homebrew, as an official direct binary, by a signed/pkg installer, manually, or by another package manager.

## 10. Direct installs are valid

Tools such as `gh`, `ffmpeg`, and `ffprobe` may be intentionally installed directly when current Homebrew formulas require fragile source builds on Intel Monterey. Do not overwrite a working direct install merely to make package ownership uniform.

A direct binary is acceptable when the source is trusted, architecture and minimum macOS are compatible, checksum/signature is verified when available, and runtime functionality is verified.

## 11. Updating direct-installed tools

`brew upgrade` does not update tools Homebrew does not own. For direct-installed tools: check path/version, verify the current stable release from the authoritative source, confirm Intel/x86_64 compatibility, verify checksum/signature when available, download to a temporary location, validate, replace only after validation, re-verify functionality, and remove temporary files.

## 12. GitHub CLI on the Mac

For repository automation, local `gh` is optional; follow the GitHub/CI guardrail. For local use:

```bash
which gh
gh --version
gh auth status
```

If authentication is missing, use GitHub OAuth/device flow. Never ask for a PAT to be pasted into Chat. Do not reinstall a valid direct `gh` through Homebrew just because auth is missing.

## 13. FFmpeg / FFprobe validation

A version string is not a complete functional test. When relevant, encode a short test media file and inspect it with `ffprobe`. If real encode/probe succeeds, treat the binaries as functional.

## 14. Homebrew Portable Ruby

Do not confuse Homebrew Portable Ruby with system Ruby. If `devfix brew config` reports valid Homebrew Ruby and Homebrew commands run, do not reinstall Ruby because an unrelated formula failed.

## 15. Download policy

Use finite retries, record exact HTTP/curl errors, avoid waiting hours for a small file at unusable speed, use HTTP/1.1 only when HTTP/2 instability is demonstrated, and compare Direct vs DevFix routes when useful. Not every destination should be forced through Snowflake.

## 16. Network changes

Do not change Wi-Fi, hotspot, ISP, VPN/proxy state, or route during Tor bootstrap, Snowflake startup, large downloads, package installation, or source dependency fetches. If the network changes, start a clean attempt before drawing architectural conclusions.

## 17. Security policy

Do not solve package/network issues by weakening security. Avoid disabling SIP/Gatekeeper/TLS verification, permanent `curl -k`, `chmod 777`, hard-coded credentials, unknown scripts piped into a root shell, or destructive state removal without backup.

## 18. Before installing a new tool

Before saying `brew install X`, determine whether X already exists, its version/path/owner, whether Homebrew has a compatible Intel Monterey bottle, whether a source build and extra dependencies will be required, whether an authoritative direct binary exists, and which route is lower risk.

## 19. Avoid retry loops

Every retry must correspond to a new explicit hypothesis. Do not use the pattern install → fail → repeat → reinstall package manager → random config changes.

## 20. Cleanup and reporting

Do not delete direct-installed binaries simply because Homebrew does not own them. Remove temporary downloads after successful installation and keep backups until replacements are verified.

For meaningful local tool work, report tool/version/architecture/path, installation method, ownership, verification performed, route used (Direct or DevFix Snowflake), and future update method. For failures, report exact step/error/resource/HTTP status when known, classification, and safe next action.

## Final rule

```text
“Homebrew is installed” does not mean “every tool must be installed by Homebrew.”
“A Homebrew install failed” does not mean “DevFix or the internet is broken.”
Identify the failure domain first, then choose the lowest-risk method compatible with Intel Monterey.
```
