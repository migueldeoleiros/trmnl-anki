# Backend Contract

The backend implementation lives under `backend/app`. This package wires deployment and documents the public contract used by TRMNL.

Expected runtime contract:

- `GET /health` returns service health.
- `GET /api/random` returns compact cached JSON shaped like `fixtures/random-normal.json`.
- `GET /api/random?query=...` uses a raw Anki search; `GET /api/random?deck=...&filter=...` composes `deck:"..." (<filter>)`.
- cold custom queries return `status: not_ready` while the background worker fills that cache entry.
- Backend reads AnkiConnect from `TRMNL_ANKI_ANKICONNECT_URL` only on the internal Docker network.
- If `ANKICONNECT_API_KEY` is set in compose, backend receives it as `TRMNL_ANKI_ANKICONNECT_API_KEY` and sends it on every AnkiConnect request.
- Backend writes a schema v2 per-query JSON cache under `TRMNL_ANKI_CACHE_PATH` and returns privacy-safe `query_key`/`query_label` metadata instead of echoing raw queries.
- Backend never exposes arbitrary AnkiConnect actions.

Settings use the `TRMNL_ANKI_` prefix from `backend/app/config.py`. Keep `backend.app.main:app` stable unless `Dockerfile` is updated too.
