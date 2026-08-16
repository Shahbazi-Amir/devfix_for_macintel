# 014 — REAL_MAC_PHASE_AWARE_BOOTSTRAP_STALL

Physical Monterey `0.3.0-rc1` reached Tor bootstrap 30% on obfs4 candidate 2 and was terminated after 90 seconds without a percentage change. Tor documents consensus loading as a phase that can take a while. Fix: retain a 90s initial stall limit, use 150s once relay-handshake progress reaches 10%, and 240s from consensus-request/loading progress (>=25%), while preserving the explicit `DEVFIX_TUNNEL_STALL_TIMEOUT` override for deterministic tests.
