# Security

## Proxy credentials

DevFix may store a proxy URL in `~/.config/devfix/config`. If the URL contains credentials, those credentials are therefore stored on disk. The configuration directory and file are created with restrictive permissions (`700` and `600` where supported), and user-facing status commands redact the credential portion.

Prefer a local proxy endpoint that does not require credentials when possible.

## Scope

DevFix does not install a certificate authority, disable TLS verification, change `/etc/hosts`, alter macOS system proxy settings, or modify global Git proxy configuration.

## Mirrors

DevFix never enables a third-party Homebrew mirror automatically. A configured artifact mirror can supply executable software, so users must choose and trust it explicitly.

## Reporting vulnerabilities

Please open a GitHub issue without including passwords, proxy credentials, private URLs, tokens, or other secrets. For sensitive reports, use GitHub's private vulnerability reporting if it is enabled for the repository.
