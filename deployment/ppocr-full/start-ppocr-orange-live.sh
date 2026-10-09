#!/bin/sh
set -eu
cd /media/developer/gocr-runtime/ppocr-probe-transport
export PYTHONPATH=.
export PP_OCR_FULL_OSD=1
export PP_OCR_FRAME_COMPRESSION=lz4
export PP_OCR_LZ4_LIBRARY=/media/developer/gocr-runtime/liblz4-tv.so
exec python3 -B -m gocr_worker.tv_server --assets /media/developer/gocr-runtime/assets --mode ORANGE_FULL --frame-worker http://192.168.1.11:18775 --token-file /media/developer/gocr-runtime/transport.token --translator http://192.168.1.11:8765 --socket /tmp/gocr-frame.sock
