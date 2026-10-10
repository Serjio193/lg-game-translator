"""Assemble one OSD application with the existing menu assets embedded."""
from pathlib import Path
import runpy
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    modules = runpy.run_path(str(ROOT / 'scripts/package-mobile-osd.py'))['MODULES']
    staging = ROOT / 'build/unified-osd-0.2.0'
    staging.mkdir(parents=True, exist_ok=True)
    extras = ('appinfo.json', 'icon.png', 'index.html', 'overlay.css', 'overlay.js',
              'osd-shell.js', 'surface-probe.js', 'start-controller.sh', 'translation-watcher.js')
    for name in (*modules, *extras):
        target = staging / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'overlay' / name, target)
    embedded = staging / 'menu'
    embedded.mkdir(exist_ok=True)
    for name in ('index.html', 'menu.css', 'menu.js', 'manual-control.js',
                 'mobile-pairing.js', 'google-settings.js'):
        shutil.copyfile(ROOT / 'menu' / name, embedded / name)
    # The installer provisions the device-only menu capability after install.
    (embedded / 'menu-key.js').write_text('window.OSD_MENU_KEY="";\n', encoding='utf-8')
    subprocess.run(['powershell', '-NoProfile', '-File',
                    str(Path.home() / 'AppData/Roaming/npm/ares-package.ps1'),
                    str(staging), '-o', str(ROOT / 'build/dist')], check=True)


if __name__ == '__main__':
    main()
