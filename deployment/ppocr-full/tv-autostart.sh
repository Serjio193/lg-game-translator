#!/bin/sh
set -eu
ROOT=/media/developer/gocr-runtime
PIDFILE=/tmp/ppocr-full-supervisor.pid
if [ -f "$PIDFILE" ]; then
    task_pid=$(cat "$PIDFILE")
    case "$task_pid" in *[!0-9]*|'') exit 1;; esac
    if [ -r "/proc/$task_pid/cmdline" ]; then
        case "$(tr '\000' ' ' < "/proc/$task_pid/cmdline")" in
            *tv-relay-supervisor.sh*) exit 0;;
        esac
    fi
fi
# Installed PicCap supports TV_FULL as the full-frame socket selector.
# Actual execution location belongs to start-ppocr-orange-live.sh: ORANGE_FULL.
printf 'TV_FULL\n' > /media/developer/apps/usr/palm/applications/org.webosbrew.piccap/gocr-mode.conf
touch /media/developer/ppocr-full-osd.enabled
nohup sh "$ROOT/tv-relay-supervisor.sh" > "$ROOT/ppocr-orange-live.log" 2>&1 < /dev/null &
echo $! > "$PIDFILE"
