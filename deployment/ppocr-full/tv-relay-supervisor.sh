#!/bin/sh
# Existing transport worker only; no model instances on TV.
trap 'test -z "$child_pid" || kill "$child_pid"; exit 0' TERM INT
while :; do
    sh /media/developer/gocr-runtime/start-ppocr-orange-live.sh &
    child_pid=$!
    wait "$child_pid"
    child_pid=
    sleep 3
done
