from pathlib import Path


def must_replace(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


cli = Path("tunnel/cli/devfix-tunnel")
s = cli.read_text()

for old, new, label in [
    ('TUNNEL_VERSION="0.3.0-rc2"', 'TUNNEL_VERSION="0.3.0-rc3"', "cli version"),
    ('TUNNEL_TOR_DATA_BASE="$TUNNEL_STATE_ROOT/tor-data"\n', 'TUNNEL_TOR_DATA_BASE="$TUNNEL_STATE_ROOT/tor-data"\nTUNNEL_TOR_CACHE_DIR="${DEVFIX_TUNNEL_CACHE_DIR:-$TUNNEL_STATE_ROOT/tor-cache}"\n', "cache dir constant"),
    ('BOOTSTRAP_TIMEOUT="${DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT:-420}"', 'BOOTSTRAP_TIMEOUT="${DEVFIX_TUNNEL_BOOTSTRAP_TIMEOUT:-1200}"', "bootstrap timeout"),
    ('STALL_TIMEOUT_HANDSHAKE="${DEVFIX_TUNNEL_STALL_TIMEOUT_HANDSHAKE:-150}"', 'STALL_TIMEOUT_HANDSHAKE="${DEVFIX_TUNNEL_STALL_TIMEOUT_HANDSHAKE:-180}"', "handshake timeout"),
    ('STALL_TIMEOUT_CONSENSUS="${DEVFIX_TUNNEL_STALL_TIMEOUT_CONSENSUS:-240}"\nVALIDATION_TIMEOUT=', 'STALL_TIMEOUT_CONSENSUS="${DEVFIX_TUNNEL_STALL_TIMEOUT_CONSENSUS:-360}"\nSTALL_TIMEOUT_DESCRIPTORS="${DEVFIX_TUNNEL_STALL_TIMEOUT_DESCRIPTORS:-900}"\nVALIDATION_TIMEOUT=', "descriptor timeout constant"),
    ('mkdir -p "$TUNNEL_STATE_ROOT" "$TUNNEL_RUN_DIR" "$TUNNEL_TOR_DATA_BASE" "$TUNNEL_LOG_DIR" ||', 'mkdir -p "$TUNNEL_STATE_ROOT" "$TUNNEL_RUN_DIR" "$TUNNEL_TOR_DATA_BASE" "$TUNNEL_TOR_CACHE_DIR" "$TUNNEL_LOG_DIR" ||', "ensure cache dir"),
    ('chmod 700 "$TUNNEL_STATE_ROOT" "$TUNNEL_RUN_DIR" "$TUNNEL_TOR_DATA_BASE" "$TUNNEL_LOG_DIR" 2>/dev/null || true', 'chmod 700 "$TUNNEL_STATE_ROOT" "$TUNNEL_RUN_DIR" "$TUNNEL_TOR_DATA_BASE" "$TUNNEL_TOR_CACHE_DIR" "$TUNNEL_LOG_DIR" 2>/dev/null || true', "cache permissions"),
]:
    s = must_replace(s, old, new, label)

s = must_replace(
    s,
    '  q_data=$(torrc_quote "$data_dir")\n  q_geoip=$(torrc_quote "$TUNNEL_GEOIP")',
    '  q_data=$(torrc_quote "$data_dir")\n  q_cache=$(torrc_quote "$TUNNEL_TOR_CACHE_DIR")\n  q_geoip=$(torrc_quote "$TUNNEL_GEOIP")',
    "cache torrc quote",
)

s = must_replace(
    s,
    'DataDirectory $q_data\nSocksPort 127.0.0.1:$port\nClientOnly 1\nAvoidDiskWrites 1',
    'DataDirectory $q_data\nCacheDirectory $q_cache\nSocksPort 127.0.0.1:$port\nClientOnly 1\nAvoidDiskWrites 0',
    "persistent cache torrc",
)

old = '''stall_timeout_for_percent() {
  percent="$1"
  if [ -n "$STALL_TIMEOUT_OVERRIDE" ]; then
    printf '%s' "$STALL_TIMEOUT"
  elif [ "$percent" -ge 25 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_CONSENSUS"
  elif [ "$percent" -ge 10 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_HANDSHAKE"
  else
    printf '%s' "$STALL_TIMEOUT"
  fi
}'''
new = '''stall_timeout_for_percent() {
  percent="$1"
  if [ -n "$STALL_TIMEOUT_OVERRIDE" ]; then
    printf '%s' "$STALL_TIMEOUT"
  elif [ "$percent" -ge 40 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_DESCRIPTORS"
  elif [ "$percent" -ge 25 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_CONSENSUS"
  elif [ "$percent" -ge 10 ] 2>/dev/null; then
    printf '%s' "$STALL_TIMEOUT_HANDSHAKE"
  else
    printf '%s' "$STALL_TIMEOUT"
  fi
}'''
s = must_replace(s, old, new, "late-stage timeout policy")

old = '''  elif [ "$transport" = "snowflake" ] && grep -q 'broker failure' "$file" 2>/dev/null; then
    printf 'BROKER_RENDEZVOUS_FAILURE'
  else
    printf '%s' "$fallback"
  fi'''
new = '''  elif [ "$transport" = "snowflake" ] && grep -q 'broker failure' "$file" 2>/dev/null; then
    printf 'BROKER_RENDEZVOUS_FAILURE'
  elif grep -Eq 'Bootstrapped (40|45|50|55|60|65|70|75)%' "$file" 2>/dev/null; then
    printf 'DIRECTORY_INFO_STALL'
  else
    printf '%s' "$fallback"
  fi'''
s = must_replace(s, old, new, "directory stall classifier")

old = "  if [ -f \"$TUNNEL_GEOIP6\" ]; then printf 'GeoIP IPv6: OK\\n'; else printf 'GeoIP IPv6: MISSING\\n'; fail=1; fi\n"
new = old + "  if [ -d \"$TUNNEL_TOR_CACHE_DIR\" ]; then printf 'Directory cache: OK (%s)\\n' \"$TUNNEL_TOR_CACHE_DIR\"; else printf 'Directory cache: WILL CREATE (%s)\\n' \"$TUNNEL_TOR_CACHE_DIR\"; fi\n"
s = must_replace(s, old, new, "doctor cache status")

cli.write_text(s)
Path("tunnel/VERSION").write_text("0.3.0-rc3\n")

for path in [Path("tests/test_devfix_tunnel.sh"), Path("tests/test_devfix_tunnel_chrome.sh")]:
    path.write_text(path.read_text().replace("0.3.0-rc2", "0.3.0-rc3"))

# The real packaged Tor parser must accept the exact separate-cache configuration.
tor_test = Path("tests/test_devfix_tunnel_tor_config.sh")
s = tor_test.read_text()
s = must_replace(s, '  data="$TMP/data-$transport"\n  torrc="$TMP/torrc-$transport"\n  mkdir -p "$data"', '  data="$TMP/data-$transport"\n  cache="$TMP/cache"\n  torrc="$TMP/torrc-$transport"\n  mkdir -p "$data" "$cache"', "tor parser cache dir")
s = must_replace(s, 'DataDirectory "$data"\nSocksPort 0\nClientOnly 1\nAvoidDiskWrites 1', 'DataDirectory "$data"\nCacheDirectory "$cache"\nSocksPort 0\nClientOnly 1\nAvoidDiskWrites 0', "tor parser cache config")
tor_test.write_text(s)

readme = Path("tunnel/README.md")
s = readme.read_text().replace("0.3.0-rc2", "0.3.0-rc3")
anchor = "`0.3.0-rc3` separates exit-only country policy from entry-bridge eligibility, exhausts the packaged catalog by default, and uses phase-aware stall limits.\n"
note = (
    "\nPhysical RC2 then proved that later obfs4 bridges could reach 50% and obtain a usable consensus, "
    "but each fallback used a fresh DataDirectory and Tor's default CacheDirectory followed it, so consensus/certificate/microdescriptor work was discarded. "
    "RC3 keeps fresh per-attempt DataDirectory/guard state while using a separate persistent directory cache shared sequentially across fallback attempts and sessions. "
    "It enables normal cache writes and gives the descriptor-loading phase a longer no-progress window.\n"
)
if anchor not in s:
    # The global version replacement changes the RC2 sentence to RC3 before this insertion.
    raise SystemExit("README RC3 anchor missing")
readme.write_text(s.replace(anchor, anchor + note, 1))

rem = Path("docs/tunnel/remediations")
rem.mkdir(parents=True, exist_ok=True)
(rem / "015_REAL_MAC_COLD_DIRECTORY_CACHE_EACH_FALLBACK.md").write_text(
    "# 015 — REAL_MAC_COLD_DIRECTORY_CACHE_EACH_FALLBACK\n\n"
    "Physical Monterey RC2 reached Tor bootstrap 45-50% on meek/obfs4, but every transport attempt used a fresh DataDirectory and failed attempts were deleted. "
    "Tor's default CacheDirectory follows DataDirectory, so cached consensus/certificates/microdescriptors were discarded with each fallback. "
    "RC3 separates CacheDirectory into a persistent user-owned directory while retaining fresh per-attempt DataDirectory state. `AvoidDiskWrites` is set to 0 so useful directory cache data can be persisted normally.\n"
)
(rem / "016_REAL_MAC_DESCRIPTOR_PHASE_TOO_AGGRESSIVE.md").write_text(
    "# 016 — REAL_MAC_DESCRIPTOR_PHASE_TOO_AGGRESSIVE\n\n"
    "RC2 terminated working obfs4 bridges at bootstrap 50% after 240 seconds without a percentage change. Tor documents phase 50 (loading relay descriptors) as typically the bulk of bootstrap, especially on slow links. "
    "RC3 uses a 900-second no-progress limit from phase >=40 and a 1200-second overall attempt ceiling, while early-stage failures remain bounded sooner.\n"
)
