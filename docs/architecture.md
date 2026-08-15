# DevFix 2.x Architecture

## Data path

```text
brew / git / curl / developer command
               |
          DevFix wrapper
               |
      +--------+---------+
      |                  |
    direct          local SOCKS
                         |
                   Tor daemon
                         |
                     lyrebird
                         |
                     Snowflake
                         |
                  Tor / Internet
```

DevFix deliberately routes only the child process it launches. It does not install a Network Extension and does not become a system-wide VPN.

## Transport interface

Each transport conceptually implements:

- availability
- start
- stop
- status
- endpoint
- healthcheck

The current implementations are `direct`, `snowflake`, and optional `external-proxy`.

## Snowflake runtime

Release packages embed the official Tor Expert Bundle under `/usr/local/libexec/devfix/tor`. The runtime writes per-user state under `~/Library/Application Support/DevFix` and logs under `~/Library/Logs/DevFix`.

The daemon lifecycle is owned by DevFix. PID/state files use restrictive permissions. `disconnect` terminates the owned Tor process and `repair` removes stale runtime state.

## Bootstrap trust

End users do not download Tor during first use. GitHub Actions downloads a pinned Tor Expert Bundle from Tor Project's official archive, retrieves Tor's checksum manifest over HTTPS, validates SHA-256, and embeds the verified payload into the release artifacts.

## Failure model

Network reachability and Homebrew compatibility are independent axes. A working Snowflake route does not imply that a formula supports Monterey. DevFix therefore classifies command errors separately from transport failures.
