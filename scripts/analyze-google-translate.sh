#!/usr/bin/env bash
set -euo pipefail

VER="10.38.67.991942559.4-release"
PAGE="https://www.apkmirror.com/apk/google-inc/translate/google-translate-10-38-67-991942559-4-release-release/google-translate-10-38-67-991942559-4-release-2-android-apk-download/"
mkdir -p out/apk out/unpacked

UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"

echo "[1] Fetching APKMirror variant page"
curl -fsSL -A "$UA" "$PAGE" -o out/page.html

DL_PATH=$(python3 - <<'PY'
import re
s=open('out/page.html',encoding='utf-8',errors='ignore').read()
m=re.search(r'href="([^"]*?/download/\?key=[^"]+)"', s)
if not m:
    m=re.search(r'href="([^"]*download\.php\?id=[^"]+)"', s)
print(m.group(1).replace('&amp;','&') if m else '')
PY
)

if [[ -z "$DL_PATH" ]]; then
  echo "Could not locate APKMirror intermediate download link" >&2
  grep -oiE 'href="[^"]*(download|key)[^"]*"' out/page.html | head -100 > out/download-link-debug.txt || true
  exit 2
fi

if [[ "$DL_PATH" == http* ]]; then
  DL_PAGE="$DL_PATH"
else
  DL_PAGE="https://www.apkmirror.com$DL_PATH"
fi

echo "[2] Fetching intermediate page: $DL_PAGE"
curl -fsSL -A "$UA" -e "$PAGE" "$DL_PAGE" -o out/download.html

FINAL=$(python3 - <<'PY'
import re
s=open('out/download.html',encoding='utf-8',errors='ignore').read()
patterns=[
 r'href="([^"]*download\.php\?id=[^"]+)"',
 r'href="(https://download[^"]+)"',
 r'href="(https://downloadr[^"]+)"'
]
for p in patterns:
    m=re.search(p,s)
    if m:
        print(m.group(1).replace('&amp;','&'))
        break
PY
)

if [[ -z "$FINAL" ]]; then
  echo "Could not locate final APK URL" >&2
  grep -oiE 'href="[^"]*(download|\.apk)[^"]*"' out/download.html | head -100 > out/final-link-debug.txt || true
  exit 3
fi
if [[ "$FINAL" != http* ]]; then FINAL="https://www.apkmirror.com$FINAL"; fi

echo "[3] Downloading APK"
curl -fL --retry 3 -A "$UA" -e "$DL_PAGE" "$FINAL" -o out/apk/google-translate.apk

echo "[4] Basic integrity"
file out/apk/google-translate.apk | tee out/file.txt
sha256sum out/apk/google-translate.apk | tee out/sha256.txt
stat -c '%s bytes' out/apk/google-translate.apk | tee out/size.txt

echo "[5] Unpacking"
unzip -q out/apk/google-translate.apk -d out/unpacked

find out/unpacked -type f | sort > out/file-list.txt
find out/unpacked -type f \( -iname '*.tflite' -o -iname '*.lite' -o -iname '*.task' -o -iname '*.bin' -o -iname '*.model' -o -iname '*.pb' -o -iname '*.onnx' \) -printf '%p\t%s bytes\n' | sort > out/model-files.txt
find out/unpacked -type f -name '*.so' -printf '%p\t%s bytes\n' | sort > out/native-libs.txt

echo "[6] Strings of interest from APK and native libs"
{
  echo '=== APK strings ==='
  strings -a out/apk/google-translate.apk | grep -iE 'lens|camera|ocr|text.?recogn|translate|inpaint|tflite|tensorflow|liteRT|region.?proposal|rpn|vision|segmentation|render|overlay' | sort -u | head -10000
  echo
  echo '=== Native library matches ==='
  while IFS= read -r so; do
    echo "### $so"
    strings -a "$so" | grep -iE 'lens|camera|ocr|text.?recogn|translate|inpaint|tflite|tensorflow|liteRT|region.?proposal|rpn|vision|segmentation|render|overlay' | sort -u | head -3000 || true
  done < <(find out/unpacked -type f -name '*.so' | sort)
} > out/interesting-strings.txt

echo "[7] ELF dependencies"
{
  while IFS= read -r so; do
    echo "### $so"
    readelf -d "$so" 2>/dev/null | grep -E 'NEEDED|SONAME' || true
  done < <(find out/unpacked -type f -name '*.so' | sort)
} > out/elf-deps.txt

echo "[8] DEX class/string scan with androguard"
python3 - <<'PY' > out/dex-hits.txt 2>&1 || true
from androguard.core.apk import APK
import re
apk=APK('out/apk/google-translate.apk')
rx=re.compile(r'(lens|camera|ocr|text.?recogn|translate|inpaint|tflite|tensorflow|litert|region.?proposal|rpn|vision|segmentation|overlay)',re.I)
for d in apk.get_all_dex():
    from androguard.core.dex import DEX
    dx=DEX(d)
    for c in dx.get_classes():
        n=c.get_name()
        if rx.search(n):
            print(n)
PY

echo "[9] Largest files"
find out/unpacked -type f -printf '%s\t%p\n' | sort -nr | head -200 > out/largest-files.txt

echo "Done."
