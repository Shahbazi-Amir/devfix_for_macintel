# DevFix for Mac Intel

DevFix is a self-contained command-line networking helper for older Intel Macs used for software development. It is designed for cases where Homebrew, GitHub, Homebrew bottles, Ruby downloads, FFmpeg dependencies, or similar developer resources are unreachable or unreliable from the user's network.

**DevFix 2.x does not require an existing VPN, proxy, or VPS.** Its macOS release package bundles the Tor Project's official x86_64 Tor Expert Bundle and uses the built-in Snowflake pluggable transport when direct access fails.

## What DevFix is

- A process-scoped network route manager for `brew`, `git`, `curl`, and arbitrary CLI commands.
- A network and compatibility diagnostic tool for Intel macOS.
- A self-contained Snowflake/Tor client for developer traffic.
- A conservative wrapper that does not disable TLS verification or rewrite macOS system networking.

## What DevFix is not

- It is not a system-wide consumer VPN.
- It does not route Safari or every app on the Mac.
- It cannot make software compatible with an unsupported macOS version.
- It cannot guarantee that Snowflake will work on every network or at every moment.

## Target systems

Primary target:

- Intel x86_64 Mac
- MacBook Pro 2015 class hardware
- macOS Monterey 12.x

The bundled Tor software currently supports macOS 10.15 and later. Homebrew treats older macOS releases such as Monterey as legacy/Tier 3, so some formula failures may be compatibility problems rather than network problems.

## Installation

### Recommended: macOS installer

Download the release artifact named:

```text
DevFix-2.0.0-macos-x86_64.pkg
```

Open it and complete the macOS installer. The package installs:

```text
/usr/local/bin/devfix
/usr/local/libexec/devfix/tor/
/usr/local/share/devfix/
/usr/local/share/man/man1/devfix.1
```

The package is currently not Developer ID signed/notarized unless a signing certificate is configured in the release pipeline. Do not bypass macOS security globally; use the normal macOS per-file approval flow if Gatekeeper asks for confirmation.

### Portable tarball

The release also contains a self-contained tarball. Extract it and run:

```bash
./install.sh
```

This installs the same payload and does not require Homebrew.

## Quick start

```bash
devfix doctor
devfix connect
devfix brew update
```

`connect` defaults to `auto`:

1. Test direct access to GitHub, Homebrew API, and Homebrew bottles.
2. If direct access works, use it with no tunnel.
3. If direct access is incomplete, start the bundled Snowflake/Tor transport.
4. If the user explicitly configured an external proxy, it remains available as an optional advanced fallback.

## Homebrew

```bash
devfix brew update
devfix brew upgrade
devfix brew install ffmpeg
```

DevFix applies routing only inside the Homebrew process tree. It does not permanently change macOS System Proxy settings.

If Homebrew fails, DevFix classifies common failures such as:

```text
DNS_FAILURE
TLS_FAILURE
TIMEOUT
NETWORK_BLOCKED
HOMEBREW_COMPATIBILITY
PACKAGE_UNSUPPORTED
BUILD_FAILURE
XCODE_CLT_FAILURE
DISK_SPACE
UNKNOWN
```

## Git and curl

```bash
devfix git clone https://github.com/OWNER/REPO.git
devfix git fetch
devfix curl https://example.com/file
```

Any other CLI command can be run inside the active route:

```bash
devfix run ruby-install ...
devfix run npm install
```

## Connection controls

```bash
devfix connect
devfix connect snowflake
devfix connect direct
devfix status
devfix restart
devfix disconnect
devfix repair
```

## Transport controls

```bash
devfix transport list
devfix transport status
devfix transport test direct
devfix transport test snowflake
devfix transport auto
```

Available transport model:

- `direct`: no tunnel; preferred when all critical developer endpoints are reachable.
- `snowflake`: built-in Tor + Snowflake route bundled in the installer.
- `external-proxy`: optional user-supplied HTTP/SOCKS proxy, not required for normal use.

## How Snowflake works here

Tor Project documents Snowflake as a censorship-circumvention pluggable transport that can be used without obtaining bridge addresses. DevFix runs the bundled `tor` daemon with the bundled `lyrebird` transport and exposes a local SOCKS endpoint only to DevFix-managed processes.

The release build downloads the official Tor Expert Bundle from Tor Project's package archive, verifies its SHA-256 against Tor's published checksum manifest, and then embeds it into the `.pkg` and portable tarball.

## Doctor

```bash
devfix doctor
devfix doctor --verbose
```

Doctor reports:

- architecture and macOS version
- Git, curl, Homebrew, and Xcode CLT presence
- direct reachability to GitHub, Homebrew API, bottles, and Ruby downloads
- built-in transport availability
- active DevFix route
- Homebrew legacy compatibility warning

A failed direct probe means an endpoint is unreachable; it is not by itself proof that censorship is the cause. DevFix deliberately reports `NETWORK_BLOCKED_OR_UNREACHABLE` rather than making an unsupported attribution.

## Optional external proxy

Not required, but retained for advanced use:

```bash
devfix proxy set socks5h://127.0.0.1:1080
devfix connect external-proxy
```

Credentials in proxy URLs are redacted from status output and logs.

## Logs

```bash
devfix logs
devfix logs --tail 200
```

DevFix logs lifecycle and failure classifications, not full command arguments. Tor's notice log is kept separately. Avoid posting logs publicly without reviewing them first.

## Security principles

DevFix does **not**:

- use `curl -k`
- disable Git TLS verification
- disable Gatekeeper or SIP
- install custom root certificates
- edit `/etc/hosts`
- permanently change macOS DNS or System Proxy settings
- silently choose third-party Homebrew mirrors

See [SECURITY.md](SECURITY.md).

## Uninstall

```bash
sudo /usr/local/share/devfix/uninstall.sh
```

Or:

```bash
devfix uninstall
```

Program files are removed while user state/logs are kept. To also delete state and logs:

```bash
devfix uninstall --purge
```

## Limitations

- Snowflake depends on volunteer and Tor infrastructure and is not guaranteed to connect on every network.
- Tor routes are normally slower than direct broadband and may be noticeably slower for large Homebrew bottles or FFmpeg downloads.
- Homebrew on Monterey/Intel is a legacy configuration; DevFix cannot create bottles that upstream does not publish or fix source code that no longer builds on that OS.
- The current installer is unsigned unless Apple Developer signing credentials are configured.

## Upstream references

- Tor Project Snowflake: `https://snowflake.torproject.org/`
- Tor Project bridge/transport documentation: `https://support.torproject.org/little-t-tor/circumvention/using-bridges/`
- Tor Expert Bundle downloads: `https://www.torproject.org/download/tor/`
- Homebrew support tiers: `https://docs.brew.sh/Support-Tiers`

## License

DevFix source is MIT licensed. Bundled Tor Project components remain under their upstream licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
