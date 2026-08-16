# Remediation 003 — REMEDIATION_PATCH_SYNTAX

Runs `31936994080` and `31937053678` proved that injecting multiline fragments into legacy one-line shell functions is unsafe. Strategy changed to atomic full-function replacement using locally syntax/integration-tested multiline implementations for `recover_owned_proxy` and `cmd_apply`.
