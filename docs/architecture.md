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

The current-card response should match `fixtures/current-normal.json` and include status metadata so the Liquid template can render empty, stale, and error states. The current backend exposes this at `/api/current`.

Card rotation should use deterministic wall-clock slots: `floor(now / cadence_minutes)`. That keeps the same card stable within a refresh slot and changes predictably at the next slot.
