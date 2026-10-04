#!/bin/sh
set -eu

destination=${1:-"$HOME/translator-test/nllb200"}
repository=https://huggingface.co/mijuanlo/nllb-200-distilled-600M-ct2-int8/resolve/main
mkdir -p "$destination"

for file in config.json shared_vocabulary.json sentencepiece.bpe.model model.bin; do
  if [ ! -s "$destination/$file" ]; then
    curl --fail --location --retry 3 \
      --output "$destination/$file" "$repository/$file"
  fi
done
