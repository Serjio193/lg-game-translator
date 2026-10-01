# Building for rooted LG webOS

The native probe requires the unofficial webOS native toolchain (buildroot-nc4), the same toolchain family used by hyperion-webos.

## Native binary

Set the toolchain path:

```sh
export TOOLCHAIN_FILE=/opt/arm-webos-linux-gnueabi_sdk-buildroot/share/buildroot/toolchainfile.cmake
./scripts/build-webos.sh
```

Output:

```
build/webos/lg-game-capture-probe
```

The current v0.1 binary only tests whether candidate LG capture libraries can be loaded. It deliberately does not call undocumented capture functions until the G5 environment is confirmed.

## IPK staging/package

LG's `ares-package` CLI can package the launcher:

```sh
./scripts/package-ipk.sh
```

The native executable is included automatically when it has already been cross-compiled.

## Why there is no prebuilt IPK yet

A valid ARM webOS binary requires the webOS native cross-toolchain. The project should not publish a host-compiled binary disguised as a TV build. Once CI has the toolchain, releases can produce installable artifacts automatically.
