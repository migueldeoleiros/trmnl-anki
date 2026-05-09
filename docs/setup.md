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
- `TRMNL_ANKI_CARD_QUERY=deck:"Core 2000" (is:learn or is:review)`
- `TRMNL_ANKI_FALLBACK_QUERY=deck:"Core 2000" (is:learn or is:review)`

## Portainer

Use `docker-compose.yml` as a stack template. The backend service is wired to `backend.app.main:app`. The `anki` service builds `anki/Dockerfile`, launches Anki Desktop through KasmVNC, and installs AnkiConnect into the persistent `/config/Anki2` profile. Keep the `internal` network internal so AnkiConnect is unavailable from the internet.

The first Anki startup still needs manual setup through KasmVNC/noVNC: sign in to AnkiWeb and choose the correct initial sync direction, usually download from AnkiWeb for a fresh server profile.

Use `docker-compose.bootstrap.yml` only during setup. It publishes KasmVNC to `127.0.0.1:${KASMVNC_PORT:-3000}` and fails during Compose interpolation if `KASMVNC_PASSWORD` is empty, so pass a password when rendering config or starting the overlay. Remove the override after profile/bootstrap work is done.

## TRMNL

Create a hosted Private Plugin in Polling mode and point it at the reverse-proxied backend current-card endpoint. See `trmnl-plugin/settings-example.md`.
