#!/bin/sh
# Standalone C++ Invoke test. CONFIG is exported by validate-native-detector.py.
set -eu
BENCH="${1:?benchmark executable required}"
MODEL="${2:?original Google detector model required}"
RUNTIME="${3:?TFLite shared library required}"
CONFIG="${4:?original binarypb launch snapshot required}"
FRAME="${5:?stored RGB PPM frame required}"
OUT="${6:?output directory required}"
mkdir -p "$OUT"
for xnnpack in 0 1; do
    for threads in 1 2 4; do
        "$BENCH" "$MODEL" "$RUNTIME" "$CONFIG" "$FRAME" "$threads" "$xnnpack" 20 \
            > "$OUT/threads-$threads-xnnpack-$xnnpack.json" \
            2> "$OUT/threads-$threads-xnnpack-$xnnpack.log"
    done
done
