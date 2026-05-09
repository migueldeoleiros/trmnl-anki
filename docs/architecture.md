# Architecture

The backend polls AnkiConnect over the internal Docker network, normalizes cards, writes a JSON cache, and exposes only cached read-only data to TRMNL.

The Anki container also joins an egress network so it can download/install AnkiConnect on first run and sync with AnkiWeb. AnkiConnect binds to the static internal address `172.28.0.10:8765`, so it remains unpublished and reachable only on the internal Docker network.

```text
AnkiDroid
  -> AnkiWeb
  -> headless Anki Desktop in Docker
  -> AnkiConnect http://172.28.0.10:8765
  -> FastAPI backend
  -> JSON file cache
  -> HTTPS reverse proxy
  -> TRMNL hosted Private Plugin Polling
```

The random-card response should match `fixtures/random-normal.json` and include status metadata so the Liquid template can render empty, stale, and error states. The backend exposes this at `/api/random`.

TRMNL owns poll cadence. Each `/api/random` call selects a random card from the matching cached query entry without triggering live AnkiConnect calls.
