# Remediation 011 — UPGRADE_RECOVERY_FAIL_OPEN

Date: 2026-08-16

A final upgrade-path audit found that the package `preinstall` and `postinstall` scripts invoked guardian recovery with `|| true`. That was acceptable for early smoke packaging but is not strong enough for a network product: if an older tunnel-owned System Proxy session cannot be safely recovered, an upgrade must not silently continue and replace runtime/helper files.

The upgrade path is changed to fail closed:

- preinstall requires the installed guardian's recovery operation to succeed when an older guardian exists;
- preinstall refuses to replace the Tor runtime while a DevFix Tunnel Tor process is still active and asks for a normal disconnect first;
- postinstall requires the newly installed guardian recovery pass to succeed before completing recovery-daemon setup;
- portable install performs equivalent connected-session safety checks before replacing installed files.

No running process is force-killed by the installer. No third-party proxy state is overwritten to make an upgrade succeed.
