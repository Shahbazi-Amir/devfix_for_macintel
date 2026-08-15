# Troubleshooting

## `brew update` times out

Run:

```sh
devfix doctor
```

If the direct path fails and the proxy path succeeds, use:

```sh
devfix brew update
```

If no proxy is configured, start your existing VPN/proxy client and run:

```sh
devfix proxy detect
```

or configure its local address explicitly:

```sh
devfix proxy set socks5h://127.0.0.1:7890
```

## GitHub works in a browser but Homebrew fails

Homebrew also needs its JSON API and bottle/container endpoints. `devfix doctor` checks GitHub, GitHub API, Homebrew API, and GHCR separately.

A `401` from the GHCR `/v2/` probe is treated as reachable because that registry endpoint normally requires authentication for deeper requests.

## `brew install ffmpeg` still fails through the proxy

Read the first actual error after connectivity is confirmed. Typical non-network causes include:

- no compatible bottle for the host macOS/CPU;
- source build requirements that the old OS/toolchain cannot satisfy;
- outdated or missing Xcode Command Line Tools;
- a formula/cask minimum macOS requirement;
- a package-specific build failure.

DevFix does not bypass those compatibility rules.

## Ruby downloads fail

Run the exact tool through DevFix:

```sh
devfix run ruby-install ...
devfix run rbenv install ...
devfix run curl https://cache.ruby-lang.org/
```

If the installer launches child processes normally, they inherit the proxy environment.

## `devfix on` did not change my current shell

A program cannot modify the environment of its parent shell. `devfix on` enables proxy use for commands launched **through DevFix**. To export variables into the current shell:

```sh
eval "$(devfix env)"
```

To clear them:

```sh
eval "$(devfix env --unset)"
```

## Proxy password contains special characters

Percent-encode characters that are not safe in URLs. The saved config is mode `600`, but credentials embedded in the URL still exist on disk. Prefer a local proxy without credentials when possible.

## Homebrew mirror overrides

DevFix supports Homebrew's official mirror variables but never chooses a third-party mirror for you:

```sh
devfix mirror set-api https://trusted.example/homebrew-api
devfix mirror set-artifact https://trusted.example/homebrew
```

Only use infrastructure you trust to distribute executable software. Clear overrides with:

```sh
devfix mirror clear
```
