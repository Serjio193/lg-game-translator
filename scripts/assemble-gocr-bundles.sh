#!/bin/sh
set -eu

# Assemble two local GOCR benchmark bundles without committing proprietary model files.
# Usage:
#   ./scripts/assemble-gocr-bundles.sh /path/to/extracted/google/assets /path/to/output

ASSETS="${1:?path to extracted Google/Lens assets required}"
OUT="${2:-build/gocr-bundles}"

DET_MODEL="gocr_group_rpn_text_detection_model_2024_q4.tflite"
DET_CONFIG="gocr_group_rpn_text_detection_config_2024_q4.binarypb"
REC_MODEL="recognizer_latn_vi_cyrl_lm_retrained.tflite"
REC_LABELS="recognizer_latn_vi_cyrl_label_map.pb"

find_one() {
  name="$1"
  found="$(find "$ASSETS" -type f -name "$name" -print -quit)"
  [ -n "$found" ] || { echo "missing asset: $name" >&2; exit 1; }
  printf '%s\n' "$found"
}

DM="$(find_one "$DET_MODEL")"
DC="$(find_one "$DET_CONFIG")"
RM="$(find_one "$REC_MODEL")"
RL="$(find_one "$REC_LABELS")"

mkdir -p "$OUT/tv_full/models" "$OUT/tv_crop/tv/models" "$OUT/tv_crop/orange_pi/models"

cp config/gocr/gocr_tv_full.json "$OUT/tv_full/profile.json"
cp "$DM" "$OUT/tv_full/models/$DET_MODEL"
cp "$DC" "$OUT/tv_full/models/$DET_CONFIG"
cp "$RM" "$OUT/tv_full/models/$REC_MODEL"
cp "$RL" "$OUT/tv_full/models/$REC_LABELS"

cp config/gocr/gocr_tv_crop.json "$OUT/tv_crop/profile.json"
cp "$DM" "$OUT/tv_crop/tv/models/$DET_MODEL"
cp "$DC" "$OUT/tv_crop/tv/models/$DET_CONFIG"
cp "$RM" "$OUT/tv_crop/orange_pi/models/$REC_MODEL"
cp "$RL" "$OUT/tv_crop/orange_pi/models/$REC_LABELS"
for name in recognizer_cyrl_config.pb recognizer_cyrl_lm.compact_fst.gz \
    recognizer_cyrl_lm.syms recognizer_latn_vi_cyrl_prior.pb; do
    source="$(find_one "$name")"
    cp "$source" "$OUT/tv_full/models/$name"
    cp "$source" "$OUT/tv_crop/orange_pi/models/$name"
done

echo "assembled:"
echo "  $OUT/tv_full"
echo "  $OUT/tv_crop"
