# Backend Contract

The backend implementation lives under `backend/app`. This package wires deployment and documents the public contract used by TRMNL.

Expected runtime contract:

- `GET /health` returns service health.
- `GET /api/current` returns compact cached JSON shaped like `fixtures/current-normal.json`.
- Backend reads AnkiConnect from `TRMNL_ANKI_ANKICONNECT_URL` only on the internal Docker network.
- If `ANKICONNECT_API_KEY` is set in compose, backend receives it as `TRMNL_ANKI_ANKICONNECT_API_KEY` and sends it on every AnkiConnect request.
- Backend writes JSON cache under `TRMNL_ANKI_CACHE_PATH`.
- Backend never exposes arbitrary AnkiConnect actions.

Settings use the `TRMNL_ANKI_` prefix from `backend/app/config.py`. Keep `backend.app.main:app` stable unless `Dockerfile` is updated too.
