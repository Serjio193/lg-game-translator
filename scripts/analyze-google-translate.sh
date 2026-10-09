#!/usr/bin/env bash
set -euo pipefail

VER="10.38.67.991942559.4-release"
mkdir -p out/apk out/unpacked
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
APK=out/apk/google-translate.apk

is_apk() {
  [[ -s "$1" ]] || return 1
  python3 - "$1" <<'PY'
import sys,zipfile
p=sys.argv[1]
try:
    with zipfile.ZipFile(p) as z:
        names=set(z.namelist())
        ok=('AndroidManifest.xml' in names and 'classes.dex' in names)
    raise SystemExit(0 if ok else 1)
except Exception:
    raise SystemExit(1)
PY
}

try_url() {
  local url="$1"
  echo "Trying: $url"
  rm -f "$APK"
  if curl -fL --retry 2 --connect-timeout 20 -A "$UA" "$url" -o "$APK"; then
    if is_apk "$APK"; then
      echo "Valid APK downloaded from $url"
      return 0
    fi
  fi
  rm -f "$APK"
  return 1
}

echo "[1] Downloading latest Google Translate APK"
try_url "https://d.apkpure.com/b/APK/com.google.android.apps.translate?version=latest" || try_url "https://d.apkpure.net/b/APK/com.google.android.apps.translate?version=latest" || {
  PAGE="https://www.apkmirror.com/apk/google-inc/translate/google-translate-10-38-67-991942559-4-release-release/google-translate-10-38-67-991942559-4-release-2-android-apk-download/"
  echo "APKPure CDN failed; trying APKMirror HTML flow"
  curl -fsSL -A "$UA" "$PAGE" -o out/page.html
  DL_PATH=$(python3 - <<'PY'
import re
s=open('out/page.html',encoding='utf-8',errors='ignore').read()
m=re.search(r'href="([^"]*?/download/\?key=[^"]+)"', s) or re.search(r'href="([^"]*download\.php\?id=[^"]+)"', s)
print(m.group(1).replace('&amp;','&') if m else '')
PY
)
  [[ -n "$DL_PATH" ]] || { echo "No APKMirror intermediate link"; exit 2; }
  [[ "$DL_PATH" == http* ]] && DL_PAGE="$DL_PATH" || DL_PAGE="https://www.apkmirror.com$DL_PATH"
  curl -fsSL -A "$UA" -e "$PAGE" "$DL_PAGE" -o out/download.html
  FINAL=$(python3 - <<'PY'
import re
s=open('out/download.html',encoding='utf-8',errors='ignore').read()
for p in [r'href="([^"]*download\.php\?id=[^"]+)"',r'href="(https://download[^"]+)"',r'href="(https://downloadr[^"]+)"']:
    m=re.search(p,s)
    if m:
        print(m.group(1).replace('&amp;','&')); break
PY
)
  [[ -n "$FINAL" ]] || { echo "No APKMirror final link"; exit 3; }
  [[ "$FINAL" == http* ]] || FINAL="https://www.apkmirror.com$FINAL"
  try_url "$FINAL" || exit 4
}

echo "[2] Basic integrity"
file "$APK" | tee out/file.txt
sha256sum "$APK" | tee out/sha256.txt
stat -c '%s bytes' "$APK" | tee out/size.txt

echo "[3] Unpacking"
unzip -q "$APK" -d out/unpacked
find out/unpacked -type f | sort > out/file-list.txt
find out/unpacked -type f \( -iname '*.tflite' -o -iname '*.lite' -o -iname '*.task' -o -iname '*.bin' -o -iname '*.model' -o -iname '*.pb' -o -iname '*.onnx' \) -printf '%p\t%s bytes\n' | sort > out/model-files.txt
find out/unpacked -type f -name '*.so' -printf '%p\t%s bytes\n' | sort > out/native-libs.txt

echo "[4] Manifest/package metadata"
python3 - <<'PY' > out/apk-metadata.txt 2>&1
from androguard.core.apk import APK
a=APK('out/apk/google-translate.apk')
print('package=',a.get_package())
print('version_name=',a.get_androidversion_name())
print('version_code=',a.get_androidversion_code())
print('min_sdk=',a.get_min_sdk_version())
print('target_sdk=',a.get_target_sdk_version())
print('permissions:')
for p in sorted(a.get_permissions()): print(' ',p)
PY

echo "[5] Strings of interest"
{
  echo '=== APK strings ==='
  strings -a "$APK" | grep -iE 'lens|camera|ocr|text.?recogn|translate|inpaint|tflite|tensorflow|liteRT|region.?proposal|rpn|vision|segmentation|render|overlay' | sort -u | head -10000 || true
  echo
  echo '=== Native library matches ==='
  while IFS= read -r so; do
    echo "### $so"
    strings -a "$so" | grep -iE 'lens|camera|ocr|text.?recogn|translate|inpaint|tflite|tensorflow|liteRT|region.?proposal|rpn|vision|segmentation|render|overlay' | sort -u | head -3000 || true
  done < <(find out/unpacked -type f -name '*.so' | sort)
} > out/interesting-strings.txt

echo "[6] ELF dependencies"
{
  while IFS= read -r so; do
    echo "### $so"
    readelf -d "$so" 2>/dev/null | grep -E 'NEEDED|SONAME' || true
  done < <(find out/unpacked -type f -name '*.so' | sort)
} > out/elf-deps.txt

echo "[7] DEX class scan"
python3 - <<'PY' > out/dex-hits.txt 2>&1 || true
from androguard.core.apk import APK
from androguard.core.dex import DEX
import re
apk=APK('out/apk/google-translate.apk')
rx=re.compile(r'(lens|camera|ocr|text.?recogn|translate|inpaint|tflite|tensorflow|litert|region.?proposal|rpn|vision|segmentation|overlay)',re.I)
for d in apk.get_all_dex():
    dx=DEX(d)
    for c in dx.get_classes():
        n=c.get_name()
        if rx.search(n): print(n)
PY


echo "[8] WordLens class/method dump"
python3 - <<'PY' > out/wordlens-classdump.txt 2>&1 || true
from androguard.core.apk import APK
from androguard.core.dex import DEX
apk=APK('out/apk/google-translate.apk')
targets={
'Lcom/google/android/libraries/wordlens/NativeLangMan;',
'Lcom/google/android/libraries/wordlens/TranslateLibApi;',
'Lcom/google/android/libraries/wordlens/WordLensSystem;'
}
for dexbytes in apk.get_all_dex():
    dx=DEX(dexbytes)
    for c in dx.get_classes():
        if c.get_name() not in targets:
            continue
        print('\nCLASS', c.get_name())
        for m in c.get_methods():
            print('METHOD', m.get_name(), m.get_descriptor(), m.get_access_flags_string())
            code=m.get_code()
            if not code: continue
            for ins in code.get_bc().get_instructions():
                o=ins.get_output()
                if any(k in o.lower() for k in ('lens','camera','translate','native','gdd','googlequicksearchbox','intent','system.load','library')):
                    print(' ', ins.get_name(), o)

# Find strings relevant to dynamic Lens packages / Google app delegation.
needles=('GDD_LENS_','EVT_CAMERA_','WORDLENS','camera translation','googlequicksearchbox','com.google.android.googlequicksearchbox')
for dexbytes in apk.get_all_dex():
    dx=DEX(dexbytes)
    for s in dx.get_strings():
        val=s.get_value()
        if any(n.lower() in val.lower() for n in needles):
            print('STRING', repr(val))
PY

echo "[9] ELF exported JNI symbols"
{
  for so in out/unpacked/lib/arm64-v8a/*.so; do
    echo "### $so"
    readelf -Ws "$so" 2>/dev/null | grep -E 'Java_|JNI_OnLoad|Translate|WordLens|Lens|Camera|Text|OCR' | head -5000 || true
  done
} > out/elf-jni-symbols.txt

echo "[10] TFLite FlatBuffer magic scan"
python3 - <<'PY' > out/tflite-magic-scan.txt
from pathlib import Path
for p in Path('out/unpacked').rglob('*'):
    if not p.is_file(): continue
    try: b=p.read_bytes()
    except: continue
    hits=[]; pos=0
    while True:
        i=b.find(b'TFL3', pos)
        if i<0: break
        hits.append(i); pos=i+1
    if hits:
        print(p, len(hits), [hex(x) for x in hits[:50]])
PY

find out/unpacked -type f -printf '%s\t%p\n' | sort -nr | head -250 > out/largest-files.txt || true
echo "Done."
