# Modified PicCap: one capture, HyperHDR plus OCR

These patches preserve the currently deployed development work from the separate
PicCap checkout. They include the OCR option/UI already present before the
2026-10-04 investigation, plus input diagnostics, robust TCP framing, packaging
permissions and boot activation fixes. Upstream licenses remain in the upstream
trees; this is not a replacement implementation of PicCap.

Exact bases are recorded in `bases.json`:

- `TBSniller/piccap`: `a243d0e0f4426f83e270553c4a5631964ee74358`.
- `webosbrew/hyperion-webos`: `00c932f092084b234b3f619b060a98fa134c12bd`.

## Reconstruct

In a separate clean checkout, with `$PATCHES` set to this directory:

```sh
git clone --recursive https://github.com/TBSniller/piccap.git piccap-ocr
cd piccap-ocr
git checkout a243d0e0f4426f83e270553c4a5631964ee74358
git submodule update --init --recursive
git -C hyperion-webos checkout 00c932f092084b234b3f619b060a98fa134c12bd
git apply --check "$PATCHES/piccap.patch"
git apply "$PATCHES/piccap.patch"
git -C hyperion-webos apply --check "$PATCHES/hyperion-webos.patch"
git -C hyperion-webos apply "$PATCHES/hyperion-webos.patch"
```

Both patches were applied to archived clean bases and their resulting modified
files compared with the development checkout (normalizing CRLF/LF): PASS.

## Build

Use the existing buildroot-nc4 toolchain and PicCap npm build commands described
in the patched README. Packaging additionally uses standard-library Python 3.
`npm run package` preserves executable mode 0755 for service binaries/scripts,
including when the webOS CLI packages on Windows.

The deployed native build used the SDK at
`/home/serji/.local/sdk/arm-webos-linux-gnueabi_sdk-buildroot` and its
`share/buildroot/toolchainfile.cmake`; build directory:
`/mnt/e/Github/piccap/hyperion-webos/build/ocr`.

```sh
cmake --build hyperion-webos/build/ocr -j4 --target hyperion-webos
gcc -Wall -Wextra -Werror -pthread -Ihyperion-webos/src \
  hyperion-webos/tests/socket_io_test.c hyperion-webos/src/socket_io.c \
  -Wl,--wrap=sendmsg -Wl,--wrap=read -o /tmp/piccap-socket-io-test
/tmp/piccap-socket-io-test
```

The TCP test forces partial writes/reads and EINTR, checks two complete 720p RGB
packets, EOF, and a closed peer without SIGPIPE. It passed on the Linux host.

## Operating profile

Set PicCap `width:1280`, `height:720`, `fps:60`, `nv12:false`, `nogui:true`,
`ocr:true`, `autostart:true`, `address:"127.0.0.1"`, `port:19400`.
Keep HyperHDR Forwarder disabled. OCR is an internal worker in PicCap, not a
consumer of HyperHDR Forwarder or a second capture process.

Tesseract and English data must already be available at `/usr/bin/tesseract` and
`/usr/share/tessdata/eng.traineddata`. If missing, OCR disables itself and capture
continues. The current OCR prototype has no tracker/cache/translation/overlay.

See `docs/ocr-dual-output.md` in lg-game-translator for measured behavior and
diagnostic sample paths.
