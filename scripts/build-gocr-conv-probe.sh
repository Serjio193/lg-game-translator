#!/bin/sh
# Diagnostic forwarding library only; does not rebuild or replace TFLite.
set -eu
SDK="${1:?webOS SDK root required}"
TF_SOURCE="${2:?pinned TensorFlow 2.17 source required}"
OUTPUT="${3:?absolute output .so path required}"
for DIR in "$SDK" "$TF_SOURCE" "$OUTPUT"; do
    case "$DIR" in /*) ;; *) echo "absolute paths required" >&2; exit 1;; esac
done
[ "$(git -C "$TF_SOURCE" rev-parse HEAD)" = ad6d8cc177d0c868982e39e0823d0efbfb95f04c ]
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
"$SDK/bin/arm-linux-g++" -std=c++17 -O2 -Wall -Wextra -Werror \
    -shared -fPIC -fno-fast-math -ffp-contract=off -I"$TF_SOURCE" \
    "$SCRIPT_DIR/../native/gocr_detector_native/conv_dispatch_probe.cpp" \
    -ldl -pthread -o "$OUTPUT"
