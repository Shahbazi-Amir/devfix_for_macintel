# DevFix Tunnel — Architecture

## Product boundary

`DevFix` remains a developer-CLI route manager. `DevFix Tunnel` is an independent general macOS routing product developed only on `feature/devfix-tunnel`.

Current milestone architecture:

```text
User / future GUI
        |
  devfix-tunnel CLI
        |
 Tunnel lifecycle core
  |     |       |
state  logs   ownership
        |
 Tor + lyrebird
        |
 localhost SOCKS
  127.0.0.1:1915x
```

No macOS System Proxy changes occur in the transport-core milestone.

Future System Proxy milestone:

```text
Safari / Chrome / Firefox
          |
macOS System Proxy (owned + reversible)
          |
localhost SOCKS
          |
Tor + Snowflake
```

Future true packet-tunnel milestone must use a real Apple NetworkExtension/PacketTunnel design and must not be simulated by relabeling System Proxy mode as a VPN.

## State isolation

All writable tunnel state is separate:

```text
~/Library/Application Support/DevFixTunnel/
  run/
    state
    tor.pid
    torrc
  tor-data/

~/Library/Logs/DevFixTunnel/
  devfix-tunnel.log
  tor.log
```

## Ownership

The tunnel may stop only a process whose ownership can be proven from tunnel state plus the expected executable/torrc command line. It never kills processes merely because they are named `tor` or `lyrebird`.

## Connection success

`CONNECTED` requires:

1. owned Tor process alive;
2. bootstrap reaches 100%;
3. local SOCKS route validates with TLS verification enabled.

A 100% bootstrap without route validation is not success.

## Ports

The prototype scans only the controlled local range `19150-19159` and binds Tor SOCKS to `127.0.0.1`. It never exposes SOCKS on the LAN and never kills another process to reclaim a port.

## Runtime payload

The prototype reads the proven DevFix Tor/lyrebird binaries from `/usr/local/libexec/devfix/tor/` but never shares writable state. A later packaging milestone will make the tunnel runtime payload independently versioned and installed.
