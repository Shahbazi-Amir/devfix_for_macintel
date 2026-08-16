# 015 — REAL_MAC_COLD_DIRECTORY_CACHE_EACH_FALLBACK

Physical Monterey RC2 reached Tor bootstrap 45-50% on meek/obfs4, but every transport attempt used a fresh DataDirectory and failed attempts were deleted. Tor's default CacheDirectory follows DataDirectory, so cached consensus/certificates/microdescriptors were discarded with each fallback. RC3 separates CacheDirectory into a persistent user-owned directory while retaining fresh per-attempt DataDirectory state. `AvoidDiskWrites` is set to 0 so useful directory cache data can be persisted normally.
