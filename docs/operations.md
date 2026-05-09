# Operations

## Sync

Default sync interval is `3600` seconds. Backend cache metadata records:

- `last_sync_at`
- `last_sync_status`
- `last_sync_error`
- `last_success_at`

Failed sync must not clear the existing card cache. TRMNL should continue showing stale cached cards with `stale: true`.

The backend settings are prefixed with `TRMNL_ANKI_`. Enable automatic refreshes with `TRMNL_ANKI_BACKGROUND_SYNC_ENABLED=true` after the Anki runtime is proven stable.

## Cache

v1 uses a JSON file cache. Keep cache data on a Docker volume and do not commit real cached cards.

## Troubleshooting

- Empty state: confirm Anki profile is synced and `Core 2000` exists.
- Stale state: confirm Anki Desktop is running, AnkiConnect is responding internally, and sync is not blocked by GUI prompts.
- TRMNL cannot load: confirm HTTPS reverse proxy route and polling URL.
- noVNC visible publicly: remove published port or protect it with admin-only auth immediately.
