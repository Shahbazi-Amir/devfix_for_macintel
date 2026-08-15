# Security Policy

DevFix treats network circumvention as a security-sensitive function.

## Invariants

- TLS certificate verification is never intentionally disabled.
- DevFix does not install root CAs, modify `/etc/hosts`, disable SIP, or disable Gatekeeper.
- System-wide proxy, DNS, and firewall settings are not modified.
- Proxy credentials are redacted from human-readable status/log output.
- Runtime state and logs are created with restrictive user permissions where possible.
- DevFix logs command category and failure class, not complete user command arguments.

## Bundled Tor software

Release artifacts embed a pinned official Tor Expert Bundle for macOS x86_64. The build retrieves Tor's published SHA-256 manifest and rejects a bundle whose digest does not match.

This checksum verification is performed during release build. Users should also verify DevFix's published `SHA256SUMS` after downloading a release.

## Reporting

Do not post logs containing personal network information publicly. Security reports should include the smallest reproducible example and should redact credentials, tokens, home-directory names, and private repository URLs.
