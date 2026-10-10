"""Package mobile settings/controller files, without replacing capture or watcher."""
from pathlib import Path
import io
import tarfile

ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    "runtime-control.js app-catalog.js app-icon.js AmbiSun-LICENSE.txt "
    "mobile-server.js mobile-auth.js mobile-store.js qr-url.js layer-settings.js "
    "translator-control.js translator-menu-route.js manual-menu-route.js orange-state.js "
    "tv-power.js luna-json-stream.js "
    "admission.js "
    "manual-style.js subtitle-layout.js glyph-cover.js mask-grow.js mask-osd-raster.js "
    "line-cover-mask.js mask-edge-blur.js control-icons.js backdrop.js fit-area.js "
    "mobile/index.html mobile/mobile.js mobile/mobile.css mobile/preview-variants.css "
    "mobile/provider-settings.js mobile/provider-settings.css"
).split()


def main():
    output = ROOT / "build/dist/mobile-osd-controller-0.1.8.tar.gz"
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for name in MODULES:
            archive.add(ROOT / "overlay" / name, arcname=name)
        for name in ("source_admission.py", "tv_server.py", "osd_publisher.py", "frame_client.py",
                     "frame_pipeline.py", "translation_client.py", "live_translation.py"):
            archive.add(ROOT / "gocr_worker" / name, arcname="relay/" + name)
        archive.add(ROOT / "deployment/mobile-osd/install-mobile.js", arcname="install-mobile.js")
        for source in (ROOT / "deployment/app-menu/install-controller.sh",
                       ROOT / "deployment/mobile-osd/install-mobile.sh"):
            body = source.read_bytes().replace(b"\r\n", b"\n")
            info = tarfile.TarInfo(source.name)
            info.size, info.mode = len(body), 0o755
            archive.addfile(info, io.BytesIO(body))
    print(output)


if __name__ == "__main__":
    main()
