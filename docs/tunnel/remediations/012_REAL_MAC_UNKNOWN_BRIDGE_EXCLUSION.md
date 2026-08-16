# 012 — REAL_MAC_UNKNOWN_BRIDGE_EXCLUSION

Physical Monterey `0.3.0-rc1` logs repeatedly reported `Not using bridge ... it is in ExcludeNodes` for Snowflake and meek while foreign-only mode was enabled. Root cause: `GeoIPExcludeUnknown 1` makes unknown-country nodes excluded in both node and exit selection. Fix: use `GeoIPExcludeUnknown 0` and keep explicit `ExcludeExitNodes {ir},{??}` so unknown exits remain rejected without excluding entry bridges.
