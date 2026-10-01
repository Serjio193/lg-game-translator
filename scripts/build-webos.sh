#!/bin/sh
set -eu

: "${TOOLCHAIN_FILE:?Set TOOLCHAIN_FILE to buildroot-nc4 toolchainfile.cmake}"

cmake -S . -B build/webos \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE"
cmake --build build/webos --parallel

echo "Built: build/webos/lg-game-capture-probe"
