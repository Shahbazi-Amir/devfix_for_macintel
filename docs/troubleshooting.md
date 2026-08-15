# Troubleshooting

## `devfix connect` cannot establish Snowflake

Run:

```bash
devfix doctor --verbose
devfix logs --tail 200
```

Confirm that the installed payload contains both Tor and lyrebird. If both exist but Snowflake cannot bootstrap, the current network may also interfere with Snowflake infrastructure. DevFix does not retry forever or weaken TLS verification.

## `brew update` still fails after Snowflake connects

Look at the `DevFix diagnosis` line. `HOMEBREW_COMPATIBILITY`, `PACKAGE_UNSUPPORTED`, `BUILD_FAILURE`, and `XCODE_CLT_FAILURE` are not solved by a network tunnel.

## Homebrew bottle unavailable

On legacy Intel macOS, upstream may not publish a bottle. Homebrew may try a source build, which can fail because of compiler, SDK, or formula support. DevFix reports this separately.

## Stale connection

```bash
devfix repair
devfix connect
```

`repair` only removes DevFix-owned runtime state; it does not change system networking.

## Port collision

DevFix starts at local SOCKS port 19050 and searches the next few ports if needed. The selected port is shown by `devfix status`.

## Gatekeeper warning for the installer

The project cannot claim Developer ID signing unless the release workflow has a real Apple certificate. Do not disable Gatekeeper globally. Use macOS's normal per-app/package approval flow if you trust the downloaded artifact and checksum.
