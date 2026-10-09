#!/bin/sh
# Isolated exact-arithmetic candidates. Never replaces the TV system runtime.
set -eu
SDK="${1:?absolute webOS SDK root required}"
SOURCE="${2:?existing pinned TensorFlow source required}"
BUILD="${3:?separate absolute build directory required}"
VARIANT="${4:?baseline, neon or neon_eigen required}"
for DIR in "$SDK" "$SOURCE" "$BUILD"; do
    case "$DIR" in /*) ;; *) echo "paths must be absolute" >&2; exit 1;; esac
done
[ "$(git -C "$SOURCE" rev-parse HEAD)" = ad6d8cc177d0c868982e39e0823d0efbfb95f04c ]
git -C "$SOURCE" diff --quiet
git -C "$SOURCE" diff --cached --quiet
RUY=ON
case "$VARIANT" in
    baseline) CPU="-march=armv7-a -mfpu=vfpv3-d16 -mfloat-abi=softfp" ;;
    neon) CPU="-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=softfp" ;;
    neon_eigen) CPU="-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=softfp"; RUY=OFF ;;
    *) echo "unknown variant" >&2; exit 1 ;;
esac
EXACT="-fno-fast-math -fno-unsafe-math-optimizations -fno-associative-math -fno-reciprocal-math -fno-finite-math-only -ffp-contract=off -DEIGEN_FAST_MATH=0"
cmake -S "$SOURCE/tensorflow/lite/c" -B "$BUILD" \
    -DCMAKE_TOOLCHAIN_FILE="$SDK/share/buildroot/toolchainfile.cmake" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DTFLITE_ENABLE_XNNPACK=OFF -DTFLITE_ENABLE_RUY="$RUY" \
    -DTFLITE_ENABLE_GPU=OFF -DTFLITE_ENABLE_NNAPI=OFF \
    -DCMAKE_C_FLAGS="$CPU $EXACT" -DCMAKE_CXX_FLAGS="$CPU $EXACT" \
    -DCMAKE_C_FLAGS_RELEASE="-O2 -DNDEBUG" \
    -DCMAKE_CXX_FLAGS_RELEASE="-O2 -DNDEBUG"
cmake --build "$BUILD" --target tensorflowlite_c -j4
printf '%s\n' "$BUILD/libtensorflowlite_c.so"
