#!/bin/sh
# Run on TV after unpacking the prepared controller bundle; does not alter PicCap.
set -eu
STAGING=${1:?Usage: install-controller.sh DIRECTORY_WITH_CONTROLLER_FILES}
APP=/media/developer/apps/usr/palm/applications/com.serjio193.lggametranslator.overlay
RELAY=/media/developer/gocr-runtime/ppocr-probe-transport/gocr_worker
test -d "$APP"
test -f "$APP/start-controller.sh"
for name in runtime-control.js app-catalog.js app-icon.js AmbiSun-LICENSE.txt; do
    test -f "$STAGING/$name"
done
BACKUP=/media/developer/gocr-runtime/backups/app-menu-$(date +%Y%m%d-%H%M%S)
if [ -d "$RELAY" ]; then
    for name in source_admission.py tv_server.py osd_publisher.py; do test -f "$STAGING/relay/$name"; done
fi
mkdir -p "$BACKUP"
for name in runtime-control.js app-catalog.js app-icon.js AmbiSun-LICENSE.txt; do
    if [ -f "$APP/$name" ]; then cp -p "$APP/$name" "$BACKUP/$name"; fi
    cp "$STAGING/$name" "$APP/$name"
done
PIDFILE=/tmp/game-translator-overlay.pid
if [ -d "$RELAY" ]; then
    mkdir -p "$BACKUP/relay"
    for name in source_admission.py tv_server.py osd_publisher.py; do
        if [ -f "$RELAY/$name" ]; then cp -p "$RELAY/$name" "$BACKUP/relay/$name"; fi
        cp "$STAGING/relay/$name" "$RELAY/$name"
    done
    SUPERVISOR=/tmp/ppocr-full-supervisor.pid
    if [ -f "$SUPERVISOR" ]; then
        supervisor_pid=$(cat "$SUPERVISOR")
        case "$supervisor_pid" in *[!0-9]*|'') exit 1;; esac
        if [ -r "/proc/$supervisor_pid/cmdline" ]; then
            case "$(tr '\000' ' ' < "/proc/$supervisor_pid/cmdline")" in
                *tv-relay-supervisor.sh*)
                    for child_pid in $(cat "/proc/$supervisor_pid/task/$supervisor_pid/children"); do
                        if [ -r "/proc/$child_pid/cmdline" ]; then
                            case "$(tr '\000' ' ' < "/proc/$child_pid/cmdline")" in
                                *gocr_worker.tv_server*ORANGE_FULL*) kill -TERM "$child_pid";;
                            esac
                        fi
                    done;;
            esac
        fi
    fi
fi
if [ -f "$PIDFILE" ]; then
    controller_pid=$(cat "$PIDFILE")
    case "$controller_pid" in *[!0-9]*|'') exit 1;; esac
    if [ -r "/proc/$controller_pid/cmdline" ]; then
        case "$(tr '\000' ' ' < "/proc/$controller_pid/cmdline")" in
            *lggametranslator.overlay/translation-watcher.js*) kill -TERM "$controller_pid";;
            *) echo 'PID belongs to another process; refusing restart' >&2; exit 1;;
        esac
        attempts=0
        while [ -r "/proc/$controller_pid/cmdline" ] && [ "$attempts" -lt 10 ]; do
            sleep 1
            attempts=$((attempts + 1))
        done
        if [ -r "/proc/$controller_pid/cmdline" ]; then echo 'Controller did not stop' >&2; exit 1; fi
    fi
fi
sh "$APP/start-controller.sh"
printf 'Controller started; backup: %s\n' "$BACKUP"
