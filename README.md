# DevFix for Mac Intel

DevFix is a small, dependency-free CLI for diagnosing and reducing Homebrew/GitHub connectivity problems on older Intel Macs — especially when direct access to developer infrastructure is filtered, unreliable, or intermittently blocked.

**DevFix is not a VPN.** It uses an HTTP/SOCKS5 proxy or tunnel that you already have and applies it only to developer commands you choose. It also separates network failures from genuine old-macOS/Homebrew compatibility failures.

## Why this exists

A legacy Intel Mac can hit two very different classes of failure:

1. **Network path failures** — GitHub, Homebrew API, GHCR bottles, Ruby sources, or other downloads time out or are filtered.
2. **Compatibility failures** — the current package has no bottle for the OS/CPU, requires a newer macOS, or cannot build with the installed toolchain.

Retrying `brew update` cannot tell you which class you are in. DevFix can.

As of August 2026, Homebrew documents macOS Monterey-era Intel systems as a legacy/Tier-3 class and has announced a broader Intel phase-out. DevFix can improve the network path; it cannot reverse Homebrew or formula compatibility policy.

## Features

- No Homebrew dependency — useful even when Homebrew is the broken component.
- Works as a normal terminal command: `devfix`.
- HTTP, HTTPS, SOCKS5, and SOCKS5-with-remote-DNS proxy URLs.
- Direct vs proxy health checks for GitHub, GitHub API, Homebrew API, and GHCR.
- `devfix brew ...`, `devfix git ...`, `devfix curl ...`, and `devfix run ...` wrappers.
- Optional Homebrew API/artifact mirror support using Homebrew's documented environment variables.
- No global macOS network changes and no permanent global Git proxy changes.
- Proxy credentials are redacted from status output.
- Installer/uninstaller, man page, tests, Intel-macOS CI, `.pkg` builder, tarball, and SHA-256 checksums.

## Install

### Option A — repository installer

Download/clone the repository, then:

```sh
cd devfix_for_macintel
./install.sh
```

This installs:

```text
/usr/local/bin/devfix
/usr/local/share/man/man1/devfix.1
```

Homebrew is not required.

### Option B — `.pkg`

The GitHub Actions **Package** workflow builds:

```text
DevFix-1.0.0.pkg
DevFix-1.0.0.tar.gz
SHA256SUMS
```

The CI-created package is unsigned unless a Developer ID Installer certificate is added separately. On a personal machine, the repository installer is the simplest path.

## 60-second setup

First see whether your existing VPN/proxy client exposes a local proxy:

```sh
devfix proxy detect
```

Or configure it explicitly, for example:

```sh
devfix proxy set socks5h://127.0.0.1:7890
```

Then diagnose both paths:

```sh
devfix doctor
```

Use Homebrew through DevFix:

```sh
devfix brew update
devfix brew install ffmpeg
```

Use any other installer through the same environment:

```sh
devfix run <command> <args...>
```

## Typical output

```text
DevFix 1.0.0
System
  OS                     Darwin
  Architecture           x86_64
  macOS                  12.7.x
  Command Line Tools     installed

Direct network
  GitHub                 FAIL (timeout/DNS/TLS/connect)
  GitHub API             FAIL (timeout/DNS/TLS/connect)
  Homebrew API           OK (HTTP 200)
  Homebrew bottles       FAIL (timeout/DNS/TLS/connect)

Proxy network
  GitHub                 OK (HTTP 200)
  GitHub API             OK (HTTP 200)
  Homebrew API           OK (HTTP 200)
  Homebrew bottles       REACHABLE (HTTP 401 expected)

Assessment
  Proxy path is materially healthier than the direct path.
```

## Commands

```text
devfix doctor [--offline]
devfix proxy set <url>
devfix proxy detect
devfix proxy status
devfix proxy enable|disable
devfix proxy clear
devfix on | off

devfix run <command> [args...]
devfix brew [args...]
devfix git [args...]
devfix curl [args...]

devfix env
devfix env --unset
devfix test-url [--direct|--proxy] <url>

devfix mirror set-api <url>
devfix mirror set-artifact <url>
devfix mirror status
devfix mirror clear

devfix config show|path
devfix version
devfix help
```

## `on` versus current-shell exports

`devfix on` means subsequent commands launched **through DevFix** use the configured proxy:

```sh
devfix on
devfix brew update
```

A child process cannot modify your existing shell. If you intentionally want the current terminal session to inherit the variables:

```sh
eval "$(devfix env)"
```

Remove them later with:

```sh
eval "$(devfix env --unset)"
```

## Homebrew mirrors

A proxy is usually the first choice. DevFix also supports Homebrew's documented mirror variables for environments that have a trusted caching/proxy repository:

```sh
devfix mirror set-api https://trusted.example/homebrew-api
devfix mirror set-artifact https://trusted.example/homebrew
```

DevFix intentionally ships with **no third-party mirror configured**. An artifact mirror can distribute executable code; choose it yourself and use only infrastructure you trust.

## What DevFix can fix

| Problem | Can DevFix help? |
|---|---|
| `brew update` cannot reach GitHub | Yes, if a working upstream proxy/tunnel is available |
| Homebrew API timeouts | Yes, proxy or trusted API mirror |
| GHCR/bottle downloads blocked | Yes, proxy or trusted artifact mirror |
| `git clone/fetch` over HTTPS fails because of network filtering | Yes |
| `curl`/Ruby installer downloads fail because of the same network path | Usually yes |
| Intermittent direct routing to developer endpoints | Helps diagnose and route selected commands |
| Formula requires a newer macOS | No |
| No compatible bottle exists for Intel/old macOS | No (source builds may or may not work) |
| Xcode Command Line Tools are missing/too old | Diagnoses it; does not fabricate a compatible toolchain |
| Source build itself is broken | No; DevFix helps prove the network is not the cause |

## Constrained/filtered networks

DevFix is designed for networks where some developer domains work directly while others time out or are denied. It does not force the whole Mac through a tunnel. That makes it useful when you want only Homebrew/Git/curl traffic to use an existing local proxy.

It does **not** provide an upstream VPN server, hide all system traffic, or make claims about access to services that block users for policy/account/region reasons.

## Configuration and security

Default config:

```text
~/.config/devfix/config
```

DevFix creates it with restrictive permissions where the filesystem supports them. If you save a proxy URL containing `user:password@host`, those credentials exist in that file. Status output redacts them.

DevFix does not:

- disable TLS verification;
- install root certificates;
- change `/etc/hosts`;
- alter macOS system proxy settings;
- write a global Git proxy setting;
- automatically trust third-party Homebrew mirrors.

See [SECURITY.md](SECURITY.md).

## Uninstall

```sh
./uninstall.sh
```

Configuration is preserved by default. Remove it too with:

```sh
./uninstall.sh --purge
```

## Development

Run syntax checks and tests without Homebrew:

```sh
bash -n bin/devfix install.sh uninstall.sh scripts/*.sh tests/*.sh
./tests/test_devfix.sh
```

Build a tarball on macOS/Linux:

```sh
./scripts/build-dist.sh
```

Build a macOS installer package on macOS:

```sh
./scripts/build-pkg.sh
```

## References

- Homebrew manual: proxy variables, `HOMEBREW_API_DOMAIN`, and `HOMEBREW_ARTIFACT_DOMAIN`: <https://docs.brew.sh/Manpage>
- Homebrew support tiers: <https://docs.brew.sh/Support-Tiers>
- GitHub-hosted runner reference: <https://docs.github.com/en/actions/reference/runners/github-hosted-runners>

## Design principle

DevFix should fail safely. It prefers scoped process environment variables over permanent system changes, never chooses a third-party software mirror on the user's behalf, and never reports a compatibility failure as a network success story.
