# 013 — REAL_MAC_AUTO_CATALOG_TRUNCATION

Physical Monterey `0.3.0-rc1` showed auto mode stopped after five attempts: two Snowflake, one meek, and only two obfs4 candidates, despite seven packaged obfs4 candidates. Root cause: default `MAX_AUTO_ATTEMPTS=5`. Fix: default `0` means exhaust the finite packaged catalog; an explicit positive environment override may still bound attempts for tests/operators.
