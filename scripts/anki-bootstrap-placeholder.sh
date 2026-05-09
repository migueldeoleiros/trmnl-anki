#!/usr/bin/env sh
set -eu

cat <<'MSG'
This is a packaging placeholder for headless Anki Desktop.
It is not a runnable AnkiConnect service.

Replace this command with an image/script that installs and launches:
- Xvfb or KasmVNC/noVNC for admin-only GUI bootstrap
- Anki Desktop
- AnkiConnect add-on
- an hourly sync runner using ANKI_SYNC_INTERVAL_SECONDS

Keep AnkiConnect bound to the internal Docker network only.
MSG

sleep infinity
