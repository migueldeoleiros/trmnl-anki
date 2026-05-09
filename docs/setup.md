# Setup

## Prerequisites

- Docker or Portainer stack support.
- A reverse proxy with HTTPS.
- An Anki profile that can sync the `Core 2000` deck from AnkiWeb.
- TRMNL hosted Private Plugin access.

## Environment

Copy `.env.example` to `.env` and fill deployment-specific values. Keep `.env` out of git.

Important defaults:

- `TRMNL_ANKI_SYNC_INTERVAL_SECONDS=3600`
- `TRMNL_ANKI_CADENCE_MINUTES=30`
- `TRMNL_ANKI_CARD_QUERY=rated:7 deck:"Core 2000"`
- `TRMNL_ANKI_FALLBACK_QUERY=deck:"Core 2000"`

## Portainer

Use `docker-compose.yml` as a stack template. The backend service is wired to `backend.app.main:app`. The `anki` service is a documented placeholder until the real Anki Desktop runtime is added. Keep the `internal` network internal so AnkiConnect is unavailable from the internet.

## TRMNL

Create a hosted Private Plugin in Polling mode and point it at the reverse-proxied backend current-card endpoint. See `trmnl-plugin/settings-example.md`.
