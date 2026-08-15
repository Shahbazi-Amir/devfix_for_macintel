#!/bin/bash
set -u
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
DEVFIX="$ROOT/bin/devfix"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/devfix-tests.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT TERM

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'ok - %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'not ok - %s\n' "$1" >&2; }
assert_eq() {
  name="$1"; expected="$2"; actual="$3"
  if [ "$expected" = "$actual" ]; then pass "$name"; else fail "$name (expected=$expected actual=$actual)"; return 1; fi
}
assert_contains() {
  name="$1"; needle="$2"; hay="$3"
  if printf '%s' "$hay" | grep -Fq "$needle"; then pass "$name"; else fail "$name (missing $needle)"; return 1; fi
}

export HOME="$TMP/home"
export DEVFIX_STATE_DIR="$TMP/state"
export DEVFIX_LOG_DIR="$TMP/log"
mkdir -p "$HOME" "$TMP/bin" "$TMP/libexec/tor/pluggable_transports"

cat > "$TMP/fakecurl" <<'SH'
#!/bin/bash
case "${FAKE_CURL_MODE:-ok}" in
  ok) printf '200' ;;
  blocked) printf '000'; exit 28 ;;
  proxy-only)
    seen=0
    for a in "$@"; do [ "$a" != "--proxy" ] || seen=1; done
    if [ "$seen" -eq 1 ]; then printf '200'; else printf '000'; exit 28; fi
    ;;
esac
SH
chmod +x "$TMP/fakecurl"
export DEVFIX_CURL_BIN="$TMP/fakecurl"

cat > "$TMP/libexec/tor/tor" <<'SH'
#!/bin/bash
exec sleep 300
SH
cat > "$TMP/libexec/tor/pluggable_transports/lyrebird" <<'SH'
#!/bin/bash
exit 0
SH
chmod +x "$TMP/libexec/tor/tor" "$TMP/libexec/tor/pluggable_transports/lyrebird"
export DEVFIX_LIBEXEC_DIR="$TMP/libexec"
export DEVFIX_TOR_BIN="$TMP/libexec/tor/tor"
export DEVFIX_LYREBIRD_BIN="$TMP/libexec/tor/pluggable_transports/lyrebird"

out=$("$DEVFIX" --version)
assert_eq "version" "DevFix $(cat "$ROOT/VERSION")" "$out"

out=$("$DEVFIX" transport list)
assert_contains "snowflake listed" "snowflake" "$out"
assert_contains "snowflake available" "available" "$out"

out=$("$DEVFIX" proxy status)
assert_contains "proxy optional" "optional" "$out"
"$DEVFIX" proxy set socks5h://127.0.0.1:9999 >/dev/null
out=$("$DEVFIX" proxy status)
assert_contains "proxy saved" "127.0.0.1:9999" "$out"
"$DEVFIX" proxy clear >/dev/null

"$DEVFIX" config set-transport direct >/dev/null
FAKE_CURL_MODE=ok "$DEVFIX" connect direct >/dev/null
out=$("$DEVFIX" status)
assert_contains "direct connected" "Transport: direct" "$out"
"$DEVFIX" disconnect >/dev/null

export DEVFIX_TEST_MODE=1
"$DEVFIX" connect snowflake >/dev/null
out=$("$DEVFIX" status)
assert_contains "snowflake connected" "Transport: snowflake" "$out"
assert_contains "snowflake socks" "Local SOCKS: 127.0.0.1:" "$out"
"$DEVFIX" disconnect >/dev/null
if [ ! -f "$DEVFIX_STATE_DIR/run/state" ]; then pass "disconnect clears state"; else fail "disconnect clears state"; fi

# Auto mode falls back to Snowflake when direct is blocked.
FAKE_CURL_MODE=blocked "$DEVFIX" config set-transport auto >/dev/null
FAKE_CURL_MODE=blocked "$DEVFIX" connect auto >/dev/null
out=$("$DEVFIX" status)
assert_contains "auto fallback snowflake" "Transport: snowflake" "$out"
"$DEVFIX" disconnect >/dev/null

# Wrapper isolation: direct must not inherit a hostile proxy from parent.
cat > "$TMP/bin/brew" <<'SH'
#!/bin/bash
printf '%s|%s' "${http_proxy:-}" "${ALL_PROXY:-}" > "$BREW_CAPTURE"
exit "${BREW_EXIT:-0}"
SH
chmod +x "$TMP/bin/brew"
export PATH="$TMP/bin:$PATH"
export BREW_CAPTURE="$TMP/brew-env"
export http_proxy=http://bad.example:1
export ALL_PROXY=http://bad.example:1
FAKE_CURL_MODE=ok "$DEVFIX" connect direct >/dev/null
"$DEVFIX" brew update >/dev/null
captured=$(cat "$BREW_CAPTURE")
assert_eq "direct clears inherited proxy" "|" "$captured"
"$DEVFIX" disconnect >/dev/null
unset http_proxy ALL_PROXY

# Snowflake wrapper injects only the process-scoped SOCKS endpoint.
"$DEVFIX" connect snowflake >/dev/null
"$DEVFIX" brew update >/dev/null
captured=$(cat "$BREW_CAPTURE")
assert_contains "snowflake wrapper proxy" "socks5h://127.0.0.1:" "$captured"
"$DEVFIX" disconnect >/dev/null

# Error classification preserves tool exit status.
cat > "$TMP/bin/brew" <<'SH'
#!/bin/bash
echo 'Operation timed out while downloading' >&2
exit 7
SH
chmod +x "$TMP/bin/brew"
FAKE_CURL_MODE=ok "$DEVFIX" connect direct >/dev/null
set +e
errout=$("$DEVFIX" brew update 2>&1 >/dev/null)
rc=$?
set -e
assert_eq "wrapper preserves exit" "7" "$rc"
assert_contains "timeout classified" "TIMEOUT" "$errout"
"$DEVFIX" disconnect >/dev/null

# Repair removes stale state.
mkdir -p "$DEVFIX_STATE_DIR/run"
cat > "$DEVFIX_STATE_DIR/run/state" <<EOF_STATE
TRANSPORT=snowflake
PID=999999
SOCKS_PORT=19050
STARTED=x
EOF_STATE
"$DEVFIX" repair >/dev/null
if [ ! -f "$DEVFIX_STATE_DIR/run/state" ]; then pass "repair stale state"; else fail "repair stale state"; fi

# env output must be shell-quotable and preserve quote characters in optional proxy.
"$DEVFIX" proxy set "http://u'p@127.0.0.1:8080" >/dev/null
FAKE_CURL_MODE=ok "$DEVFIX" connect external-proxy >/dev/null
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
# shellcheck disable=SC1090
eval "$("$DEVFIX" env)"
assert_eq "env preserves shell quote" "http://u'p@127.0.0.1:8080" "${http_proxy:-}"
"$DEVFIX" disconnect >/dev/null

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
