#!/bin/sh
APP=/media/developer/apps/usr/palm/applications/com.serjio193.lggametranslator.overlay
PIDFILE=/tmp/game-translator-overlay.pid
if [ ! -f "$APP/translation-watcher.js" ]; then exit 0; fi
if [ -f "$PIDFILE" ]; then
    task_pid=$(cat "$PIDFILE")
    case "$task_pid" in *[!0-9]*|'') exit 1;; esac
    if [ -r "/proc/$task_pid/cmdline" ]; then
        case "$(tr '\000' ' ' < "/proc/$task_pid/cmdline")" in
            *lggametranslator.overlay/translation-watcher.js*) exit 0;;
        esac
    fi
fi
nohup /usr/bin/node "$APP/translation-watcher.js" > /tmp/game-translator-overlay.log 2>&1 < /dev/null &
echo $! > "$PIDFILE"
