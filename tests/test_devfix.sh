#!/bin/bash
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
DEVFIX="$ROOT/bin/devfix"
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/devfix-test.XXXXXX")
export HOME="$TMP_ROOT/home"
export XDG_CONFIG_HOME="$TMP_ROOT/config"
mkdir -p "$HOME" "$XDG_CONFIG_HOME"

PASS=0
FAIL=0

cleanup() { rm -rf "$TMP_ROOT"; }
trap cleanup EXIT INT TERM

pass() { PASS=$((PASS + 1)); printf 'ok - %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'not ok - %s\n' "$1" >&2; }

assert_eq() {
  name="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then pass "$name"; else fail "$name (expected '$expected', got '$actual')"; fi
}

assert_contains() {
  name="$1" haystack="$2" needle="$3"
  case "$haystack" in *"$needle"*) pass "$name" ;; *) fail "$name (missing '$needle')" ;; esac
}

assert_not_contains() {
  name="$1" haystack="$2" needle="$3"
  case "$haystack" in *"$needle"*) fail "$name (unexpected '$needle')" ;; *) pass "$name" ;; esac
}

assert_success() {
  name="$1"; shift
  if "$@" >/dev/null 2>&1; then pass "$name"; else fail "$name"; fi
}

assert_failure() {
  name="$1"; shift
  if "$@" >/dev/null 2>&1; then fail "$name"; else pass "$name"; fi
}

version=$($DEVFIX version)
assert_eq "version" "1.0.0" "$version"

status=$($DEVFIX proxy status)
assert_contains "initial proxy disabled" "$status" "Proxy: disabled"
assert_contains "initial proxy unset" "$status" "URL: not configured"

assert_success "set socks proxy" "$DEVFIX" proxy set "socks5h://user:secret@127.0.0.1:7890"
status=$($DEVFIX proxy status)
assert_contains "proxy enabled after set" "$status" "Proxy: enabled"
assert_contains "credentials redacted" "$status" "socks5h://***@127.0.0.1:7890"
assert_not_contains "password never shown in status" "$status" "secret"

assert_success "set proxy containing quote" "$DEVFIX" proxy set "http://u:p'q@127.0.0.1:8080"
quoted_env=$($DEVFIX env)
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY no_proxy NO_PROXY 2>/dev/null || true
http_proxy=""
eval "$quoted_env"
assert_eq "env preserves shell quote" "http://u:p'q@127.0.0.1:8080" "$http_proxy"
assert_success "restore socks proxy" "$DEVFIX" proxy set "socks5h://user:secret@127.0.0.1:7890"

assert_failure "reject proxy without port" "$DEVFIX" proxy set "socks5h://127.0.0.1"
assert_failure "reject unsupported proxy scheme" "$DEVFIX" proxy set "ftp://127.0.0.1:21"

assert_success "proxy off" "$DEVFIX" off
status=$($DEVFIX proxy status)
assert_contains "disabled status" "$status" "Proxy: disabled"

assert_success "proxy on" "$DEVFIX" on
# shellcheck disable=SC2016
runtime_proxy=$($DEVFIX run sh -c 'printf "%s" "$http_proxy"')
assert_eq "managed command gets proxy" "socks5h://user:secret@127.0.0.1:7890" "$runtime_proxy"

env_out=$($DEVFIX env)
assert_contains "env includes http_proxy" "$env_out" "export http_proxy="
assert_contains "env includes all_proxy" "$env_out" "export all_proxy="
unset_out=$($DEVFIX env --unset)
assert_contains "unset env output" "$unset_out" "unset http_proxy"

assert_success "set api mirror" "$DEVFIX" mirror set-api "https://mirror.example/api"
assert_success "set artifact mirror" "$DEVFIX" mirror set-artifact "https://mirror.example/homebrew"
# shellcheck disable=SC2016
api_value=$($DEVFIX run sh -c 'printf "%s" "$HOMEBREW_API_DOMAIN"')
# shellcheck disable=SC2016
artifact_value=$($DEVFIX run sh -c 'printf "%s" "$HOMEBREW_ARTIFACT_DOMAIN"')
assert_eq "api mirror passed to command" "https://mirror.example/api" "$api_value"
assert_eq "artifact mirror passed to command" "https://mirror.example/homebrew" "$artifact_value"
assert_success "clear mirrors" "$DEVFIX" mirror clear

assert_success "offline doctor" "$DEVFIX" doctor --offline
assert_failure "unknown command fails" "$DEVFIX" definitely-not-a-command

config_path=$($DEVFIX config path)
if [ -f "$config_path" ]; then pass "config file created"; else fail "config file created"; fi

config_contents=$(cat "$config_path")
assert_contains "config contains proxy" "$config_contents" "PROXY_URL=socks5h://user:secret@127.0.0.1:7890"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
