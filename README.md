# TRMNL Anki

Show a random cached Anki card on a TRMNL display.

The stack runs Anki Desktop with AnkiConnect in Docker, syncs cards from AnkiWeb, keeps a small JSON cache, and serves one read-only endpoint for TRMNL polling.

```text
AnkiDroid -> AnkiWeb -> Anki Desktop -> AnkiConnect -> FastAPI cache -> TRMNL
```

## What It Runs

- FastAPI backend at `GET /api/random`
- Headless Anki Desktop in KasmVNC for setup and sync
- AnkiConnect bound only to the internal Docker network
- JSON cache persisted in a Docker volume
- TRMNL Liquid template in `trmnl-plugin/template.html`

`/api/random` returns cached data only. It does not proxy arbitrary AnkiConnect calls and does not touch live Anki during TRMNL requests.

## Quick Start

1. Copy `.env.example` to `.env` and edit the values you need.
2. Set `KASMVNC_PASSWORD` before using the bootstrap overlay.
3. Check the compose file:

   ```sh
   docker compose --env-file .env.example config
   ```

4. Start the stack with `docker-compose.yml`.
5. For first-time setup, temporarily add `docker-compose.bootstrap.yml`, open KasmVNC, sign in to AnkiWeb, and sync the deck.
6. Remove the bootstrap overlay after Anki is configured.
7. Reverse proxy a private HTTPS path to `http://backend:8000/api/random` and use that URL in TRMNL Polling mode.

Default card query:

```text
deck:"Core 2000" (is:learn or is:review)
```

## API

```text
GET /api/random
GET /api/random?query=deck:%22Core%202000%22%20is:review
GET /api/random?deck=Core%202000&filter=is:review
```

Responses match `fixtures/random-normal.json`. Cold custom queries return `status: not_ready` until the background refresh fills that cache entry.

## Configuration

Settings use the `TRMNL_ANKI_` prefix. Common values:

- `TRMNL_ANKI_CARD_QUERY` - default Anki search
- `TRMNL_ANKI_FALLBACK_QUERY` - fallback search when the default returns too few cards
- `TRMNL_ANKI_SYNC_INTERVAL_SECONDS` - AnkiWeb sync interval, default `3600`
- `TRMNL_ANKI_SYNC_RETRY_INTERVAL_SECONDS` - retry delay after failures
- `TRMNL_ANKI_MAX_CARDS` - maximum cards cached per query
- `TRMNL_ANKI_MAX_CACHED_QUERIES` - number of cached query variants to keep

See `.env.example` for the full set.

## Repository Layout

- `backend/` - FastAPI app, AnkiConnect client, cache, normalizer, tests
- `anki/` - KasmVNC Anki image and startup script
- `trmnl-plugin/` - TRMNL template and settings notes
- `fixtures/` - sample API responses and AnkiConnect payloads
- `docs/` - setup, reverse proxy, operations, and privacy notes
