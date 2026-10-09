#!/usr/bin/env bash
set -euo pipefail
OUT=fast-out
mkdir -p "$OUT/u"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
curl -fL -A "$UA" "https://d.apkpure.net/b/APK/com.google.android.googlequicksearchbox?version=latest" -o "$OUT/google.apk"
unzip -q "$OUT/google.apk" -d "$OUT/u"

find "$OUT/u" -type f -printf '%s\t%p\n' | sort -nr | head -1000 > "$OUT/largest.txt" || true
find "$OUT/u" -type f | grep -Ei 'lens|ocr|text|detect|recogn|vision|model|tflite|lite|inpaint|segment' > "$OUT/name-hits.txt" || true

for so in "$OUT/u"/lib/arm64-v8a/liblens*.so "$OUT/u"/lib/arm64-v8a/*vision*.so; do
  [[ -f "$so" ]] || continue
  echo "===== $so =====" >> "$OUT/lens-so-strings.txt"
  strings -a "$so" | grep -iE 'tflite|litert|model|detector|detect|recogn|ocr|text|offline|inpaint|segment|file.?group|gdd|tensor|input|output' | sort -u >> "$OUT/lens-so-strings.txt" || true
  echo >> "$OUT/lens-so-strings.txt"
  readelf -d "$so" >> "$OUT/lens-so-deps.txt" 2>/dev/null || true
done

python3 - <<'PY' > "$OUT/tfl3.txt"
from pathlib import Path
for p in Path('fast-out/u').rglob('*'):
    if not p.is_file(): continue
    try: b=p.read_bytes()
    except: continue
    pos=0; hits=[]
    while True:
        i=b.find(b'TFL3',pos)
        if i<0: break
        hits.append(i); pos=i+1
    if hits:
        print(p.stat().st_size, p, len(hits), ' '.join(hex(x) for x in hits[:100]))
PY

for d in "$OUT/u"/classes*.dex; do
  echo "===== $d =====" >> "$OUT/dex-strings.txt"
  strings -a "$d" | grep -iE 'GDD_LENS_|LENS_OFFLINE_TEXT|lens_ondevice|ondevice.*text|text.*detector|text.*recogn|offline.*text|inpaint|segmentation' | sort -u >> "$OUT/dex-strings.txt" || true
done

rm -f "$OUT/google.apk"
echo done
