#!/bin/sh
set -eu
STAGING=${1:?Usage: install-mobile.sh DIRECTORY_WITH_CONTROLLER_FILES}
/usr/bin/node "$STAGING/install-mobile.js" "$STAGING"
sh "$STAGING/install-controller.sh" "$STAGING"
