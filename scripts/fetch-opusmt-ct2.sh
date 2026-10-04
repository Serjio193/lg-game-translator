#!/bin/sh
set -eu

destination=${1:-"$HOME/translator-test/opusmt"}
model_dir="$destination/opus-mt-en-ru-ctranslate2-int8"
archive="$destination/opus-mt-en-ru-ctranslate2-int8.zip"
url=https://huggingface.co/ordois/opus-mt-en-ru-ctranslate2-int8/resolve/main/opus-mt-en-ru-ctranslate2-int8.zip

mkdir -p "$destination"
if [ ! -s "$archive" ]; then
  curl --fail --location --retry 3 --output "$archive" "$url"
fi
unzip -q -o "$archive" -d "$destination"
cd "$model_dir"
printf '%s  %s\n' \
  '8f6496adfc930cbfecbe8281112197705c488fab47d34b4829b06d7f478909af' config.json \
  'f5ae1da30bcb61e877c549be8fb5a434193893eb97509ccd0b954465f9a8f80c' model.bin \
  'bf1812383ed402163a2ed1b553e175e7db96a54ed68b6c15566018fdf945ed99' shared_vocabulary.json \
  '16bebef1389a0b8ab452772c4e35b9e605e5713f8ac7baa71ca701394eaa086d' source.spm \
  '745998e51ba5b058e38b7ac7765c25c43ed5c1c39cc92b27163b9b2e323c9d7c' target.spm \
  | sha256sum --check
