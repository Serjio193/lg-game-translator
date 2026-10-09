#!/bin/sh
# Optional isolated ARM32 runtime comparison; never installs over system TFLite.
set -eu
SDK="${1:?absolute webOS SDK root required}"
WORK="${2:?absolute persistent Linux build directory required}"
case "$SDK" in /*) ;; *) echo "SDK must be absolute" >&2; exit 1;; esac
case "$WORK" in /*) ;; *) echo "WORK must be absolute" >&2; exit 1;; esac
mkdir -p "$WORK"
if [ ! -d "$WORK/source/.git" ]; then
    git clone --depth 1 --branch v2.17.0 \
        https://github.com/tensorflow/tensorflow.git "$WORK/source"
fi
EXPECTED=ad6d8cc177d0c868982e39e0823d0efbfb95f04c
ACTUAL="$(git -C "$WORK/source" rev-parse HEAD)"
[ "$ACTUAL" = "$EXPECTED" ] || { echo "unexpected TensorFlow source revision" >&2; exit 1; }
cmake -S "$WORK/source/tensorflow/lite/c" -B "$WORK/build" \
    -DCMAKE_TOOLCHAIN_FILE="$SDK/share/buildroot/toolchainfile.cmake" \
    -DCMAKE_BUILD_TYPE=Release -DTFLITE_ENABLE_XNNPACK=ON \
    -DTFLITE_ENABLE_RUY=ON -DTFLITE_ENABLE_GPU=OFF \
    -DCMAKE_C_FLAGS="-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=softfp" \
    -DCMAKE_CXX_FLAGS="-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=softfp"
cmake --build "$WORK/build" --target tensorflowlite_c -j4
printf '%s\n' "$WORK/build/libtensorflowlite_c.so"
