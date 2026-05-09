# TRMNL Anki Private Plugin

Personal TRMNL hosted Private Plugin for showing one cached Anki card at a time on a TRMNL OG display. The intended backend is Python/FastAPI, with Anki Desktop plus AnkiConnect running inside the same Docker/Portainer stack.

This repository contains a small FastAPI backend, Docker/Portainer packaging, a headless Anki/KasmVNC image, sanitized fixtures, docs, and the TRMNL template contract.

## Architecture

```text
AnkiDroid -> AnkiWeb -> headless Anki Desktop -> AnkiConnect :8765
         -> FastAPI backend JSON cache -> HTTPS reverse proxy
         -> TRMNL hosted Private Plugin Polling -> TRMNL OG
```

Key rules:

- AnkiConnect is the only data source.
- AnkiConnect stays internal to Docker and is never public.
- The public endpoint serves cached JSON only.
- noVNC/KasmVNC is for admin bootstrap only.
- Default deck/query: `deck:"Core 2000" (is:learn or is:review)` to include learning, relearning, young, and mature cards.
- Default sync interval: `3600` seconds.
- Default TRMNL card cadence: `30` minutes; `15` is supported if TRMNL polling allows it.

## Repository Layout

- `backend/` - FastAPI app, AnkiConnect client, JSON cache, rotation, and tests.
- `trmnl-plugin/` - original Liquid/CSS template and TRMNL settings example.
- `fixtures/` - sanitized current-card and AnkiConnect example payloads.
- `docs/` - setup, operations, privacy, reverse proxy, and bootstrap notes.
- `Dockerfile` - backend container packaging.
- `anki/` - KasmVNC-based Anki Desktop image that installs AnkiConnect into the persistent profile.
- `docker-compose.yml` - Portainer-ready stack with backend plus headless Anki service.
- `.env.example` - documented environment keys without secrets.

## Quick Start

1. Copy `.env.example` to `.env` and edit public URL, private path, deck, cadence, sync settings, and `BACKEND_PORT` if it conflicts with an existing service.
2. Set `KASMVNC_PASSWORD` before exposing the Anki admin UI.
3. Run local checks: `python -m compileall -q backend && python -m pytest`, then `docker compose --env-file .env.example config`.
   For the bootstrap overlay, pass a password while rendering config: `KASMVNC_PASSWORD=change-me docker compose --env-file .env.example -f docker-compose.yml -f docker-compose.bootstrap.yml config`.
4. Deploy `docker-compose.yml` in Portainer.
5. For first setup only, add `docker-compose.bootstrap.yml` to expose KasmVNC on localhost/admin-only access, open Anki, sign in to AnkiWeb, and sync the `Core 2000` deck.
6. Remove the bootstrap override, then reverse proxy only the backend cached endpoint over HTTPS.
7. Paste `trmnl-plugin/template.liquid` and `trmnl-plugin/styles.css` into a hosted TRMNL Private Plugin using Polling.

## Privacy

Card text may be personal study data. Treat the JSON endpoint as private even if it is read-only. Use a long unguessable path, HTTPS, rate limits, low-detail logs, and avoid full payload logging at the proxy.

Never commit `.env`, Anki profile data, `.anki2` files, media collections, cached real cards, AnkiWeb credentials, or exported decks.

## Current Status

Implemented now:

- FastAPI cached current-card endpoint from Worker A.
- KasmVNC-based Anki image that downloads Anki launcher and installs AnkiConnect on startup.
- Original TRMNL full-screen Liquid/CSS template with no QR code.
- Sanitized fixtures for normal, empty, stale, and long-text states.
- Docker/Portainer packaging.
- Docs for setup, operations, privacy, reverse proxy, and noVNC/bootstrap.
- Local runtime validation against headless Anki Desktop/AnkiConnect, including restart persistence.

Not implemented yet:

- Public reverse proxy/TRMNL hosted polling deployment.
