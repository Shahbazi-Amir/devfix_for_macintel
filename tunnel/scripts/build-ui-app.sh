#!/bin/bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")/../.." && pwd)
OUT_DIR="${1:-$ROOT/build/tunnel-ui}"
APP_NAME="DevFix Tunnel"
APP="$OUT_DIR/$APP_NAME.app"
CONTENTS="$APP/Contents"
MACOS="$CONTENTS/MacOS"
SOURCE="$ROOT/tunnel/ui/DevFixTunnelMenuBar.swift"
ZIP="$OUT_DIR/DevFixTunnel-0.3.0-rc3-ui-preview-macos-x86_64.zip"

command -v xcrun >/dev/null 2>&1 || { echo "xcrun is required to build the macOS UI" >&2; exit 1; }
command -v codesign >/dev/null 2>&1 || { echo "codesign is required to build the macOS UI" >&2; exit 1; }
command -v ditto >/dev/null 2>&1 || { echo "ditto is required to package the macOS UI" >&2; exit 1; }

rm -rf "$APP" "$ZIP"
mkdir -p "$MACOS"

xcrun --sdk macosx swiftc \
  -O \
  -target x86_64-apple-macos12.0 \
  "$SOURCE" \
  -framework AppKit \
  -framework Foundation \
  -o "$MACOS/DevFixTunnelUI"

cat > "$CONTENTS/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleDisplayName</key>
  <string>DevFix Tunnel</string>
  <key>CFBundleExecutable</key>
  <string>DevFixTunnelUI</string>
  <key>CFBundleIdentifier</key>
  <string>com.devfix.tunnel.ui</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>DevFix Tunnel</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.3.0</string>
  <key>CFBundleVersion</key>
  <string>3</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>LSUIElement</key>
  <true/>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
PLIST

plutil -lint "$CONTENTS/Info.plist" >/dev/null
chmod 755 "$MACOS/DevFixTunnelUI"
codesign --force --sign - --timestamp=none "$APP"
codesign --verify --deep --strict "$APP"

ditto -c -k --sequesterRsrc --keepParent "$APP" "$ZIP"

printf '%s\n' "$APP"
printf '%s\n' "$ZIP"
