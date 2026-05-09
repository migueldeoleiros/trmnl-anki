# Architecture

The backend polls AnkiConnect over the internal Docker network, normalizes cards, writes a JSON cache, and exposes only cached read-only data to TRMNL.

```text
AnkiDroid
  -> AnkiWeb
  -> headless Anki Desktop in Docker
  -> AnkiConnect http://anki:8765
  -> FastAPI backend
  -> JSON file cache
  -> HTTPS reverse proxy
  -> TRMNL hosted Private Plugin Polling
```

The current-card response should match `fixtures/current-normal.json` and include status metadata so the Liquid template can render empty, stale, and error states. The current backend exposes this at `/api/current`.

Card rotation should use deterministic wall-clock slots: `floor(now / cadence_minutes)`. That keeps the same card stable within a refresh slot and changes predictably at the next slot.
