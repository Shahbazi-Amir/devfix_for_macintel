# Architecture

DevFix intentionally stays small and dependency-free so it can be useful when Homebrew itself is unhealthy.

## What DevFix is

DevFix is a command-line orchestration and diagnostics layer. It:

1. stores a user-selected HTTP/SOCKS5 proxy address with restrictive file permissions;
2. injects standard proxy environment variables into child processes;
3. injects optional, official Homebrew mirror environment variables;
4. probes critical Homebrew/GitHub endpoints directly and through the proxy;
5. reports local macOS/Homebrew/toolchain facts separately from network results.

## What DevFix is not

DevFix is not a VPN client, VPN protocol implementation, censorship-circumvention network, DNS resolver, certificate authority, or package manager. It never claims to make an incompatible Homebrew formula compatible with an old macOS release.

An upstream proxy or tunnel must already exist. This can be a local proxy exposed by a VPN/proxy client, a trusted remote HTTP proxy, or a SOCKS5 endpoint.

## Network scope

By default DevFix changes only the environment of processes it launches. It does **not** edit macOS System Settings, network services, `/etc` files, global Git configuration, or Homebrew internals.

This is deliberate: `devfix off` is deterministic, and an interrupted DevFix process cannot leave the whole machine routed through a stale proxy.

For the current interactive shell, `devfix env` prints explicit exports that the user may evaluate. The matching `devfix env --unset` removes them.

## Homebrew integration

Homebrew officially honors `http_proxy`, `https_proxy`, `all_proxy`, and related environment variables. DevFix also exposes Homebrew's supported `HOMEBREW_API_DOMAIN` and `HOMEBREW_ARTIFACT_DOMAIN` overrides for users who operate or trust a mirror.

No third-party mirror is bundled or selected automatically.

## Compatibility target

The primary target is Intel (`x86_64`) macOS, particularly legacy machines still running macOS Monterey/Ventura-era systems. The shell implementation avoids modern Bash-only features so it can run with the Bash version shipped by older macOS releases.

The diagnostic layer treats OS/package compatibility and network connectivity as separate failure domains. A healthy proxy cannot solve a formula that no longer has a compatible bottle or source build for the host OS.
