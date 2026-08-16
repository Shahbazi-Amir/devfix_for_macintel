# Remediation 007 — ACCEPTANCE_ARTIFACT_FILE_NOT_FOUND

Real-Mac acceptance stopped before installation because the expected `.pkg` path did not exist. The shell script still computed an empty hash and mislabeled the condition as `ARTIFACT_IDENTITY_FAILURE`.

Root cause: acceptance harness classification, not DevFix Tunnel product/runtime.

Fix: require local artifact existence before hashing, classify missing files as `ARTIFACT_FILE_NOT_FOUND`, and reserve `ARTIFACT_IDENTITY_FAILURE` for an existing file whose SHA-256 differs from the locked release-candidate hash.

Product/package bytes are unchanged; no CI/package rerun is required for this documentation/harness clarification.
