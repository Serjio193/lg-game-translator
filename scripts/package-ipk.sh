#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
STAGE="$ROOT/build/ipk/com.serjio193.lggametranslator"
rm -rf "$STAGE"
mkdir -p "$STAGE"

cp "$ROOT/packaging/appinfo.json" "$STAGE/"
cp "$ROOT/packaging/index.html" "$STAGE/"
test -f "$ROOT/packaging/icon.png" || {
  echo "Required webOS app icon missing: packaging/icon.png" >&2
  exit 1
}
cp "$ROOT/packaging/icon.png" "$STAGE/"

if [ -x "$ROOT/build/webos/lg-game-capture-probe" ]; then
  mkdir -p "$STAGE/bin"
  cp "$ROOT/build/webos/lg-game-capture-probe" "$STAGE/bin/"
fi

if command -v ares-package >/dev/null 2>&1; then
  mkdir -p "$ROOT/build/dist"
  ares-package "$STAGE" -o "$ROOT/build/dist"
  echo "IPK written under build/dist/"
else
  echo "ares-package not found. Staged package at: $STAGE" >&2
  echo "Install LG webOS CLI, then run this script again." >&2
  exit 2
fi
