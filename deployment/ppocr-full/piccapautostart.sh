#!/bin/sh
sh /media/developer/gocr-runtime/tv-autostart.sh
luna-send -n 1 -f luna://org.webosbrew.piccap.service/status '{}' &
exit 0
