# Embedded Game Translator menu

This directory supplies the menu assets inside the single OSD application,
`com.serjio193.lggametranslator.overlay`, titled «Перевод игры». It has no separate
appinfo/package. Build with `python scripts/package-unified-osd.py`, then the
controller archive via `python scripts/package-mobile-osd.py`.
Opening the icon displays a centered ON/OFF switch; settings are a secondary
panel. Back hides the menu while the transparent subtitle surface stays alive.
See `docs/unified-osd-app.md`. The API remains on Orange Pi at 192.168.1.11:8765.

Legacy API fields for HDMI checkbox selection, selected applications, translation provider and compatible
translation server URL are loaded from and saved to `/api/settings`. All HDMI
inputs default on; applications default off. Old saved settings migrate to an
empty applications list. Older clients omitting applications preserve saved choices.

## Installed application catalogue

overlay/app-catalog.js uses the same webOS listApps/local-icon approach as AmbiSun,
not its Windows process list. Attribution/license: overlay/AmbiSun-LICENSE.txt.
The existing root controller starts a read-only catalogue on 127.0.0.1:18779/apps.
Menu displays real visible installed apps, their names/icons and checkboxes.
HDMI and own settings/overlay/system panels are excluded. Missing icons get an
initial-letter fallback. Normal reads use a 60-second cache; explicit refresh
bypasses it and reloads installed apps. Failed loading preserves selections and HDMI editing.

Local icon files must stay under approved installed-app roots after realpath,
be bounded raster images and have PNG/JPEG/WebP signatures. Remote URLs and SVG
are not fetched. Catalogue endpoint neither writes settings nor launches apps;
source choices remain in the existing Orange API.

Selected full-frame relay snapshots enabled source/provider/address before a
frame and validates it again before publication. A late reply for a switched or
disabled source is rejected; OSD observations/placement reset for the new source.
Controller appends a session epoch to the existing control-state line; native
parser keeps its original first eight fields. Relay accepts legacy eight-field
state too. Reenabling the same source starts a fresh epoch, not an old admission.

## Install prepared changes

1. Update translator/translation_settings.py on the existing Orange API runtime
   and restart its user service; verify /api/health and /api/settings.
2. Install build/dist/com.serjio193.lggametranslator.settings_0.1.2_all.ipk using the
   existing developer IPK workflow (ares-install with the configured TV device).
3. Copy/unpack build/dist/app-menu-controller-0.1.2.tar.gz on TV and run its
   install-controller.sh with the unpacked controller directory. It backs up and
   updates the four controller modules/license and (when present) the three relay
   source-admission modules, restarts the existing watcher/relay, and leaves
   renderer/PicCap files unchanged.
4. Open settings, refresh apps, select one, save, reopen and verify persistence.
   Switch to that app and verify /tmp/game-translator-control.state enabled=1;
   unselected app must disable it. Native sources remain subject to PicCap's
   actual ability to capture their video; selection does not grant capture access.

The TV was unavailable while preparing this update. Package/host checks alone
do not prove live listApps permissions, local HTTP access, icons or remote focus.
Orange settings module is already updated and its service restarted/health checked;
existing HDMI choices preserved, applications default empty. TV installation and
physical menu verification remain pending because the user cannot enable TV now.
Host gates: 40 translator tests, 21 PP-OCR tests, three source-admission tests,
controller admission/catalogue/icon/UI tests,
JavaScript/shell syntax and IPK manifest inspection (test JS excluded) pass.

Russian idle controls retain existing settings values. The target sentence-based
five-minute rule is documented in docs/Логика системы.md and has not been
implemented by this menu change. Do not infer full-frame Russian sleep works
from the presence of its checkbox; the old native language path is separate.
PicCap capture and HyperHDR remain independent.
Saving is explicit. Failed loading disables editing; OK retries. Failed saving
reports the error and retains edits. Back/Escape/Return closes the menu.

Arrows navigate controls; OK toggles checkboxes. Select provider with left/right,
up/down leaves it. The server field accepts text/TV keyboard and up/down navigation.
Physical remote/input behavior needs user confirmation; deployed screenshot shows
loaded settings and initial checkbox focus. See docs/evidence/translation-menu-20261005.
