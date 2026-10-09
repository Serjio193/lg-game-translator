#!/usr/bin/env bash
set -euo pipefail
OUT=out-google-app
APK="$OUT/google-app.apk"
mkdir -p "$OUT/reports" "$OUT/unpacked" "$OUT/jadx"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"

is_apk(){ python3 - "$1" <<'PY'
import sys,zipfile
try:
  z=zipfile.ZipFile(sys.argv[1]); n=set(z.namelist())
  raise SystemExit(0 if 'AndroidManifest.xml' in n and any(x.startswith('classes') and x.endswith('.dex') for x in n) else 1)
except Exception: raise SystemExit(1)
PY
}

is_bundle(){ python3 - "$1" <<'PY'
import sys,zipfile
try:
 z=zipfile.ZipFile(sys.argv[1]); names=z.namelist()
 raise SystemExit(0 if any(x.lower().endswith('.apk') for x in names) else 1)
except Exception: raise SystemExit(1)
PY
}

echo "[1] Download Google App package"
BUNDLE="$OUT/google-app-download.bin"
URL="https://d.apkpure.net/b/APK/com.google.android.googlequicksearchbox?version=latest"
rm -f "$BUNDLE"
curl -fL --retry 2 -A "$UA" -D "$OUT/reports/download-headers.txt" "$URL" -o "$BUNDLE"

file "$BUNDLE" | tee "$OUT/reports/file.txt"
sha256sum "$BUNDLE" | tee "$OUT/reports/sha256.txt"
stat -c '%s bytes' "$BUNDLE" | tee "$OUT/reports/size.txt"
xxd -l 64 "$BUNDLE" > "$OUT/reports/first64.txt" || true
python3 - "$BUNDLE" > "$OUT/reports/container-list.txt" 2>&1 <<'PY'
import sys,zipfile,os
p=sys.argv[1]
print('is_zip=',zipfile.is_zipfile(p))
if zipfile.is_zipfile(p):
    with zipfile.ZipFile(p) as z:
        for i,n in enumerate(z.namelist()[:5000]):
            info=z.getinfo(n)
            print(info.file_size, n)
PY

mkdir -p "$OUT/package"
if is_apk "$BUNDLE"; then
  cp "$BUNDLE" "$APK"
elif is_bundle "$BUNDLE"; then
  unzip -q "$BUNDLE" -d "$OUT/package"
  find "$OUT/package" -type f -iname '*.apk' -printf '%s\t%p\n' | sort -nr > "$OUT/reports/split-apks.txt"
  BASE=$(find "$OUT/package" -type f \( -iname 'base.apk' -o -iname '*base*.apk' \) | head -1 || true)
  if [[ -z "$BASE" ]]; then BASE=$(find "$OUT/package" -type f -iname '*.apk' -printf '%s\t%p\n' | sort -nr | head -1 | cut -f2-); fi
  cp "$BASE" "$APK"
else
  echo "Package is neither direct APK nor zip bundle with APK files" | tee "$OUT/reports/package-error.txt"
  exit 2
fi

python3 - <<'PY' > "$OUT/reports/apk-metadata.txt" 2>&1
from androguard.core.apk import APK
a=APK('out-google-app/google-app.apk')
print('package=',a.get_package())
print('version_name=',a.get_androidversion_name())
print('version_code=',a.get_androidversion_code())
print('min_sdk=',a.get_min_sdk_version())
print('target_sdk=',a.get_target_sdk_version())
PY

echo "[2] Unpack base + all feature splits"
mkdir -p "$OUT/unpacked/base"
unzip -q "$APK" -d "$OUT/unpacked/base"
if compgen -G "$OUT/package/*.apk" >/dev/null || find "$OUT/package" -type f -name '*.apk' | grep -q .; then
  i=0
  while IFS= read -r ap; do
    i=$((i+1)); d="$OUT/unpacked/split-$i"; mkdir -p "$d"; unzip -q "$ap" -d "$d" || true
  done < <(find "$OUT/package" -type f -name '*.apk' | sort)
fi
find "$OUT/unpacked" -type f | sort > "$OUT/reports/file-list.txt"
find "$OUT/unpacked" -type f \( -iname '*.tflite' -o -iname '*.lite' -o -iname '*.task' -o -iname '*.bin' -o -iname '*.model' -o -iname '*.pb' -o -iname '*.onnx' -o -iname '*.mlmodel*' \) -printf '%s\t%p\n' | sort -nr > "$OUT/reports/model-files.txt"
find "$OUT/unpacked" -type f -name '*.so' -printf '%s\t%p\n' | sort -nr > "$OUT/reports/native-libs.txt"

echo "[3] Exact Lens/GDD strings"
grep -aR -n -E 'GDD_LENS_(OFFLINE_TEXT|TEXT|INPAINTING|SEGMENTATION|TEXT_CLASSIFIER)|LENS_OFFLINE_TEXT|offline.?text|inpainting' "$OUT/unpacked" > "$OUT/reports/gdd-raw-grep.txt" 2>/dev/null || true
{
 for d in "$OUT"/unpacked/classes*.dex; do
   echo "### $d"
   strings -a "$d" | grep -iE 'GDD_LENS_|LENS_OFFLINE_TEXT|offline.?text|lens.?text|inpaint|segment' | sort -u || true
 done
} > "$OUT/reports/dex-gdd-strings.txt"
{
 find "$OUT/unpacked" -type f -name '*.so' -print0 | while IFS= read -r -d '' so; do
   hits=$(strings -a "$so" | grep -iE 'GDD_LENS_|LENS_OFFLINE_TEXT|offline.?text|lens.?text|inpaint|text.?detect|ocr|tflite' | head -500 || true)
   if [[ -n "$hits" ]]; then echo "### $so"; echo "$hits"; fi
 done
} > "$OUT/reports/native-lens-strings.txt"

echo "[4] TFLite FlatBuffer scan"
python3 - <<'PY' > "$OUT/reports/tflite-magic-scan.txt"
from pathlib import Path
for p in Path('out-google-app/unpacked').rglob('*'):
  if not p.is_file(): continue
  try: b=p.read_bytes()
  except: continue
  hits=[]; pos=0
  while True:
    i=b.find(b'TFL3',pos)
    if i<0: break
    hits.append(i); pos=i+1
  if hits: print(p, p.stat().st_size, len(hits), [hex(x) for x in hits[:100]])
PY

echo "[5] Install latest jadx"
JURL=$(curl -fsSL https://api.github.com/repos/skylot/jadx/releases/latest | jq -r '.assets[] | select(.name|test("^jadx-[0-9.]+\\.zip$")) | .browser_download_url' | head -1)
[[ -n "$JURL" && "$JURL" != null ]] || exit 3
curl -fL "$JURL" -o "$OUT/jadx.zip"
unzip -q "$OUT/jadx.zip" -d "$OUT/jadx-bin"

echo "[6] Decompile targeted sources"
JINPUTS=("$APK")
while IFS= read -r ap; do JINPUTS+=("$ap"); done < <(find "$OUT/package" -type f -name '*.apk' | sort)
"$OUT/jadx-bin/bin/jadx" --no-res --no-imports -d "$OUT/jadx" "${JINPUTS[@]}" >/dev/null 2>"$OUT/reports/jadx-errors.txt" || true
grep -R -n -E 'GDD_LENS_(OFFLINE_TEXT|TEXT|INPAINTING|SEGMENTATION|TEXT_CLASSIFIER)|LENS_OFFLINE_TEXT' "$OUT/jadx/sources" > "$OUT/reports/jadx-gdd-hits.txt" || true

python3 - <<'PY'
from pathlib import Path
hits=Path('out-google-app/reports/jadx-gdd-hits.txt')
out=Path('out-google-app/reports/jadx-gdd-context.txt')
lines=hits.read_text(errors='ignore').splitlines() if hits.exists() else []
files=[]
for l in lines:
  p=l.split(':',1)[0]
  if p not in files: files.append(p)
with out.open('w') as w:
  for f in files[:200]:
    p=Path(f)
    w.write('\n===== '+f+' =====\n')
    try:
      txt=p.read_text(errors='ignore').splitlines()
    except: continue
    nums=[]
    for l in lines:
      if l.startswith(f+':'):
        try: nums.append(int(l.split(':',2)[1]))
        except: pass
    keep=set()
    for n in nums:
      keep.update(range(max(1,n-30), min(len(txt),n+30)+1))
    for n in sorted(keep):
      w.write(f'{n:5d}: {txt[n-1]}\n')
PY

echo "[7] Search related implementation terms near Lens packages"
grep -R -n -iE 'filegroup|file.?group|mobstore|download.*lens|lens.*download|offline.*text|text.*detector|text.?recognizer|ocr|tflite|litert' "$OUT/jadx/sources/com/google/android/apps" "$OUT/jadx/sources/com/google/android/libraries" > "$OUT/reports/jadx-lens-related.txt" 2>/dev/null || true

echo "[8] Native dependencies for Lens-looking libs"
{
 while read -r size so; do
   if strings -a "$so" | grep -qiE 'lens|offline.?text|text.?detect|ocr|tflite|inpaint'; then
     echo "### $so ($size)"
     readelf -d "$so" 2>/dev/null | grep -E 'NEEDED|SONAME' || true
   fi
 done < "$OUT/reports/native-libs.txt"
} > "$OUT/reports/native-lens-deps.txt"

echo "[9] Largest potential model/data files"
find "$OUT/unpacked" -type f -printf '%s\t%p\n' | sort -nr | head -500 > "$OUT/reports/largest-files.txt" || true

echo "Done"
