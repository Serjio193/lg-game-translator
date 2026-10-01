#!/bin/sh
# LG Game Translator — non-destructive capture environment probe.
# Run as root on the TV and paste/save the output for analysis.

set -u

echo "=== lg-game-translator capture probe ==="
date 2>/dev/null || true
echo

echo "[system]"
uname -a 2>/dev/null || true
printf "arch: "; uname -m 2>/dev/null || true
if [ -r /etc/os-release ]; then cat /etc/os-release; fi
echo

echo "[candidate capture libraries]"
for root in /usr/lib /lib /usr/lib32 /usr/lib64 /mnt/otncabi/usr/lib; do
  [ -d "$root" ] || continue
  find "$root" -maxdepth 2 -type f \( \
    -name '*vtcapture*' -o \
    -name '*dile*vt*' -o \
    -name '*halgal*' \
  \) 2>/dev/null
done | sort -u
echo

echo "[loaded capture-related libraries]"
if [ -r /proc/self/maps ]; then
  grep -Ei 'vtcapture|dile.*vt|halgal' /proc/*/maps 2>/dev/null | head -n 100 || true
fi
echo

echo "[capture-related processes]"
ps 2>/dev/null | grep -Ei 'piccap|hyperion|hue|capture' | grep -v grep || true
echo

echo "[memory]"
grep -E 'MemTotal|MemFree|MemAvailable' /proc/meminfo 2>/dev/null || true
echo

echo "Probe finished. This script only discovers the environment; it does not start capture."
