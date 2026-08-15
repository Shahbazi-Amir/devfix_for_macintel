#!/bin/bash
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
VERSION=$(cat "$ROOT/VERSION")
OUT="${1:-$ROOT/dist}"
STAGE="$ROOT/build/DevFix-$VERSION"

rm -rf "$STAGE"
mkdir -p "$STAGE/bin" "$STAGE/man" "$STAGE/docs" "$OUT"
cp "$ROOT/bin/devfix" "$STAGE/bin/devfix"
cp "$ROOT/install.sh" "$ROOT/uninstall.sh" "$ROOT/README.md" "$ROOT/CHANGELOG.md" "$STAGE/"
cp "$ROOT/man/devfix.1" "$STAGE/man/"
cp "$ROOT/docs/architecture.md" "$ROOT/docs/troubleshooting.md" "$STAGE/docs/"

(
  cd "$(dirname "$STAGE")"
  tar -czf "$OUT/DevFix-$VERSION.tar.gz" "$(basename "$STAGE")"
)

if command -v shasum >/dev/null 2>&1; then
  (cd "$OUT" && shasum -a 256 "DevFix-$VERSION.tar.gz" > SHA256SUMS)
elif command -v sha256sum >/dev/null 2>&1; then
  (cd "$OUT" && sha256sum "DevFix-$VERSION.tar.gz" > SHA256SUMS)
fi

echo "Built $OUT/DevFix-$VERSION.tar.gz"
