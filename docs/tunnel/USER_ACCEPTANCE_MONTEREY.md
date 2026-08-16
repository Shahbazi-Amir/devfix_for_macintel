# DevFix Tunnel — Intel Monterey Acceptance Gate

After CI/package PASS, install `DevFixTunnel-0.2.0-rc1-macos-x86_64.pkg` on the real Intel Monterey Mac and run:

```bash
set -u

echo "===== VERSION ====="
devfix-tunnel version

echo "===== DOCTOR ====="
devfix-tunnel doctor

echo "===== BEFORE ====="
devfix-tunnel status || true
scutil --proxy

echo "===== CONNECT ====="
devfix-tunnel connect

echo "===== CONNECTED STATUS ====="
devfix-tunnel status

echo "===== SYSTEM PROXY ====="
scutil --proxy

echo "===== OPEN TOR CHECK ====="
devfix-tunnel open https://check.torproject.org/

echo "Verify Safari/Chrome HTTPS browsing, then press Enter."
read -r _

echo "===== DISCONNECT ====="
devfix-tunnel disconnect

echo "===== AFTER ====="
devfix-tunnel status || true
scutil --proxy
```

Expected connected contract: `State: CONNECTED`, `Mode: SYSTEM_PROXY`, `Health: OK`.

## Tor crash recovery

Reconnect, get the owned Tor PID from `devfix-tunnel status`, terminate only that PID, wait three seconds, then verify `scutil --proxy` no longer points at the dead tunnel and run `devfix-tunnel repair`.

## Network change

While connected, change the active network service if practical. The old service proxy must be restored and the session must report `NETWORK_SERVICE_CHANGED` instead of claiming healthy routing.

## Reboot/orphan recovery

Connect, reboot without disconnecting, then check `scutil --proxy`. The periodic/boot recovery LaunchDaemon must prevent a stale dead localhost SOCKS proxy from remaining owned after reboot.

Report Safari, Chrome, disconnect restore, Tor-crash restore, network-change, and reboot recovery as PASS/FAIL/NOT RUN plus `devfix-tunnel logs 200`. Do not paste passwords, tokens or Keychain contents.
