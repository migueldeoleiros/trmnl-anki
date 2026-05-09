# Operations

## Sync

Default sync interval is `3600` seconds. Backend cache metadata records:

- `last_sync_at`
- `last_sync_status`
- `last_sync_error`
- `last_success_at`

Failed sync must not clear the existing card cache. TRMNL should continue showing stale cached cards with `stale: true`.

The backend settings are prefixed with `TRMNL_ANKI_`. Automatic refreshes are enabled by default, but they only populate cards after the Anki runtime is bootstrapped and AnkiConnect responds at the compose default `http://172.28.0.10:8765`.

## Anki Runtime

- `anki/Dockerfile` installs a pinned official Anki launcher release into a KasmVNC desktop image and verifies `ANKI_LAUNCHER_SHA256` during build.
- `anki/start-anki.sh` installs AnkiConnect into `/config/Anki2/addons21/2055492159` if missing and writes its config on each start. It removes stale `2055492159.previous` backup directories because Anki tries to import every directory under `addons21`.
- `ANKICONNECT_BIND_ADDRESS=172.28.0.10` keeps AnkiConnect bound to the static internal-network address instead of all container interfaces; do not change this to `0.0.0.0` unless you also isolate/firewall the service.
- `ANKICONNECT_API_KEY` is the compose-level source of truth; compose passes it to both AnkiConnect and the backend's `TRMNL_ANKI_ANKICONNECT_API_KEY` setting.
- Slow AnkiWeb sync gets a longer `TRMNL_ANKI_ANKICONNECT_SYNC_TIMEOUT_SECONDS`; if sync fails, backend still tries local card extraction and marks the cache stale.
- If AnkiConnect is not ready during backend startup, the background loop retries every `TRMNL_ANKI_SYNC_RETRY_INTERVAL_SECONDS` until a successful refresh, then returns to `TRMNL_ANKI_SYNC_INTERVAL_SECONDS`.

## Cache

v1 uses a JSON file cache. Keep cache data on a Docker volume and do not commit real cached cards.

## Troubleshooting

- Empty state: confirm Anki profile is synced and `Core 2000` exists.
- Stale state: confirm Anki Desktop is running, AnkiConnect is responding internally, and sync is not blocked by GUI prompts.
- TRMNL cannot load: confirm HTTPS reverse proxy route and polling URL.
- noVNC visible publicly: remove published port or protect it with admin-only auth immediately.
