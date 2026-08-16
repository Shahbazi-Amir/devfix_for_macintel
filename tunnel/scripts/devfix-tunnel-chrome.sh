#!/bin/bash
# Launch an isolated Chrome profile through DevFix Tunnel SOCKS without changing macOS System Proxy.
set -u

CLI_BIN="${DEVFIX_TUNNEL_CLI_BIN:-/usr/local/bin/devfix-tunnel}"
PROFILE_DIR="${DEVFIX_TUNNEL_CHROME_PROFILE:-$HOME/Library/Application Support/DevFixTunnel/ChromeProfile}"
URL="https://check.torproject.org/"
TRANSPORT="auto"
TRANSPORT_EXPLICIT=0
EXIT_POLICY="FOREIGN_ONLY"
EXIT_COUNTRY=""

err() { printf 'Error: %s\n' "$*" >&2; }
die() { err "$*"; exit 1; }

usage() {
  cat <<'EOF'
Usage:
  devfix-tunnel-chrome [options] [https://URL]

Options:
  --transport auto|snowflake|meek|obfs4
  --foreign-only              Exclude Iran/unknown exits (default)
  --allow-any-exit            Allow Tor's normal exit selection
  --exit-country CC           Prefer a two-letter Tor exit country
  --profile DIR               Use a different isolated Chrome profile
  -h, --help

The launcher uses SOCKS-only DevFix Tunnel mode. It does not enable macOS
System Proxy and does not modify the ordinary Chrome profile.
EOF
}

validate_transport() {
  case "$1" in auto|snowflake|meek|obfs4) return 0 ;; *) return 1 ;; esac
}

validate_country() {
  case "$1" in [A-Za-z][A-Za-z]) return 0 ;; *) return 1 ;; esac
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --transport)
      [ "$#" -ge 2 ] || die "--transport requires auto|snowflake|meek|obfs4"
      validate_transport "$2" || die "invalid transport: $2"
      TRANSPORT="$2"
      TRANSPORT_EXPLICIT=1
      shift 2
      ;;
    --foreign-only)
      EXIT_POLICY="FOREIGN_ONLY"
      shift
      ;;
    --allow-any-exit)
      EXIT_POLICY="ANY"
      shift
      ;;
    --exit-country)
      [ "$#" -ge 2 ] || die "--exit-country requires a 2-letter country code"
      validate_country "$2" || die "invalid country code: $2"
      EXIT_COUNTRY=$(printf '%s' "$2" | tr '[:upper:]' '[:lower:]')
      shift 2
      ;;
    --profile)
      [ "$#" -ge 2 ] || die "--profile requires a directory"
      PROFILE_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    http://*|https://*)
      URL="$1"
      shift
      ;;
    *)
      die "unknown option or invalid URL: $1"
      ;;
  esac
done

if [ "$EXIT_POLICY" = "FOREIGN_ONLY" ] && [ "$EXIT_COUNTRY" = "ir" ]; then
  die "foreign-only policy conflicts with --exit-country ir"
fi

[ -x "$CLI_BIN" ] || die "devfix-tunnel CLI not found: $CLI_BIN"

find_chrome() {
  if [ -n "${DEVFIX_TUNNEL_CHROME_BIN:-}" ]; then
    [ -x "$DEVFIX_TUNNEL_CHROME_BIN" ] || return 1
    printf '%s' "$DEVFIX_TUNNEL_CHROME_BIN"
    return 0
  fi

  for candidate in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "$HOME/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "$HOME/Applications/Chromium.app/Contents/MacOS/Chromium"
  do
    if [ -x "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

status_output() { "$CLI_BIN" status 2>/dev/null || true; }

status_field() {
  data="$1"
  prefix="$2"
  printf '%s\n' "$data" | sed -n "s/^${prefix}//p" | head -n 1
}

connected_route_compatible() {
  current="$1"
  health=$(status_field "$current" 'Health: ')
  [ "$health" = "OK" ] || {
    err "existing DevFix Tunnel session is not healthy; run 'devfix-tunnel status' and repair/disconnect it first"
    return 1
  }

  current_policy=$(status_field "$current" 'Exit policy: ')
  [ "$current_policy" = "$EXIT_POLICY" ] || {
    err "existing tunnel uses exit policy ${current_policy:-unknown}, requested $EXIT_POLICY; disconnect before changing policy"
    return 1
  }

  current_country=$(status_field "$current" 'Preferred exit country: ')
  if [ -n "$EXIT_COUNTRY" ] && [ "$current_country" != "$EXIT_COUNTRY" ]; then
    err "existing tunnel does not use requested exit country $EXIT_COUNTRY; disconnect before changing country"
    return 1
  fi

  if [ "$TRANSPORT_EXPLICIT" -eq 1 ]; then
    current_requested=$(printf '%s\n' "$current" | sed -nE 's/^Transport: .*\(candidate [^;]+; requested ([^)]+)\)$/\1/p' | head -n 1)
    [ "$current_requested" = "$TRANSPORT" ] || {
      err "existing tunnel uses requested transport ${current_requested:-unknown}, requested $TRANSPORT; disconnect before changing transport"
      return 1
    }
  fi

  return 0
}

ensure_socks_route() {
  current=$(status_output)
  state=$(status_field "$current" 'State: ')

  if [ "$state" = "CONNECTED" ]; then
    connected_route_compatible "$current" || return 1
  else
    printf '%s\n' "DevFix Tunnel is not connected; starting isolated SOCKS mode..." >&2
    connect_args=(socks --transport "$TRANSPORT")
    if [ "$EXIT_POLICY" = "ANY" ]; then
      connect_args+=(--allow-any-exit)
    else
      connect_args+=(--foreign-only)
    fi
    if [ -n "$EXIT_COUNTRY" ]; then
      connect_args+=(--exit-country "$EXIT_COUNTRY")
    fi

    "$CLI_BIN" connect "${connect_args[@]}" >&2 || return 1
    current=$(status_output)
    state=$(status_field "$current" 'State: ')
    health=$(status_field "$current" 'Health: ')
    [ "$state" = "CONNECTED" ] && [ "$health" = "OK" ] || {
      err "DevFix Tunnel did not report a healthy connected SOCKS route"
      return 1
    }
  fi

  port=$(printf '%s\n' "$current" | sed -nE 's#^SOCKS: socks5h://127\.0\.0\.1:([0-9]+)$#\1#p' | head -n 1)
  case "$port" in
    ''|*[!0-9]*) return 1 ;;
  esac

  # This function is used in command substitution. Its stdout contract is
  # intentionally the numeric SOCKS port only; diagnostics belong on stderr.
  printf '%s' "$port"
}

CHROME_BIN=$(find_chrome) || die "Google Chrome/Chromium was not found"
PORT=$(ensure_socks_route) || die "could not establish or reuse a compatible healthy DevFix Tunnel SOCKS route"

mkdir -p "$PROFILE_DIR" || die "cannot create isolated Chrome profile directory"
chmod 700 "$PROFILE_DIR" 2>/dev/null || true

PROXY="socks5://127.0.0.1:$PORT"
HOST_RULES="MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"
WEBRTC_POLICY="disable_non_proxied_udp"

printf 'Launching isolated tunneled Chrome profile.\n'
printf 'SOCKS: %s\n' "$PROXY"
printf 'Profile: %s\n' "$PROFILE_DIR"
printf 'Normal Chrome instances are not modified by this launcher.\n'

if [ "${DEVFIX_TUNNEL_CHROME_TEST_MODE:-0}" = "1" ]; then
  "$CHROME_BIN" \
    "--user-data-dir=$PROFILE_DIR" \
    "--proxy-server=$PROXY" \
    "--host-resolver-rules=$HOST_RULES" \
    "--force-webrtc-ip-handling-policy=$WEBRTC_POLICY" \
    --no-first-run \
    "$URL"
  exit $?
fi

/usr/bin/nohup "$CHROME_BIN" \
  "--user-data-dir=$PROFILE_DIR" \
  "--proxy-server=$PROXY" \
  "--host-resolver-rules=$HOST_RULES" \
  "--force-webrtc-ip-handling-policy=$WEBRTC_POLICY" \
  --no-first-run \
  "$URL" >/dev/null 2>&1 &

printf '%s\n' "Tunneled Chrome launched."
