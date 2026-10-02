# HyperHDR Forwarder → PC frame receiver test

This is a diagnostic receiver for the first controlled HyperHDR NetworkForwarder experiment.

## Goal

Reuse the frames already captured by PicCap/hyperion-webos without starting a second screen capture.

Expected path:

```
PicCap / hyperion-webos
  -> HyperHDR FlatBuffers input on TV
  -> HyperHDR processing / LEDs
  -> NetworkForwarder
  -> PC receiver on TCP 32949
  -> browser preview on http://127.0.0.1:8000/
```

## PC setup

On Windows run:

```bat
scripts\start-hyperhdr-receiver.bat
```

The script creates a local venv, installs `flatbuffers` and `Pillow`, starts the receiver, and opens the browser UI.

Allow inbound TCP 32949 in Windows Firewall on the Private profile.

Example PowerShell as Administrator:

```powershell
New-NetFirewallRule -DisplayName "HyperHDR Frame Receiver" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 32949 -Profile Private
```

Find the PC LAN IPv4 address with:

```
ipconfig
```

## HyperHDR setup on TV

In Network Forwarder add a FlatBuffers destination:

```
<PC_LAN_IP>:32949
```

Do **not** use `127.0.0.1`: on the TV that points back to the TV.

## Browser UI

Open:

```
http://127.0.0.1:8000/
```

The page reports:

- connection state;
- received width/height;
- RGB24 format;
- total received FPS;
- MiB/s;
- raw bytes per frame;
- age of the last frame;
- live JPEG preview.

JPEG preview is throttled (default 10 FPS). The reported receive FPS counts every accepted frame.

## ON/OFF experiment

1. Start receiver.
2. Enable HyperHDR Network Forwarder.
3. With HyperHDR lighting **ON**, record receive FPS and MiB/s for 30-60 seconds.
4. Use the normal HyperHDR lighting **OFF** control without changing PicCap.
5. Observe whether:
   - TCP stays connected;
   - frame count continues increasing;
   - receive FPS remains non-zero;
   - browser image keeps changing.
6. Turn lighting **ON** again and confirm recovery.

This tells us whether the normal HyperHDR ON/OFF state also disables the Forwarder/frame pipeline.

## Protocol assumptions to validate

The receiver follows current HyperHDR FlatBuffers schema:

- 4-byte big-endian payload length;
- `Request` union;
- `Register` request;
- forwarded `RawImage` as RGB24;
- `Reply.registered` and `Reply.video` acknowledgements.

Do not treat these assumptions as production-validated until the real TV test passes.
