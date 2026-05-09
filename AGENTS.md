# AGENTS.md

## Start Here
- Read `README.md`, `.opencode/specs/trmnl-anki.md`, `docker-compose.yml`, `.env.example`, and `backend/README.md` before changing architecture.
- This repo intentionally has no real Anki runtime yet: `docker-compose.yml` starts `scripts/anki-bootstrap-placeholder.sh`, which sleeps forever and does not expose AnkiConnect.
- Treat `.opencode/specs/trmnl-anki.md` as the approved build plan unless the user explicitly supersedes it.

## Architecture Constraints
- Data source is AnkiConnect only; do not add AnkiWeb scraping, direct SQLite reads, or non-AnkiConnect APIs.
- AnkiConnect must stay internal-only on Docker networking; public traffic should reach only the FastAPI cached endpoint.
- Backend must not mutate Anki data or proxy arbitrary AnkiConnect actions.
- TRMNL polls cached JSON from `GET /api/current`; that route must not trigger live Anki sync or slow AnkiConnect calls.
- Default deck/query is `rated:7 deck:"Core 2000"`, fallback `deck:"Core 2000"`; keep deck names quoted in Anki search strings.

## Backend Notes
- FastAPI entrypoint is `backend.app.main:app`; Dockerfile depends on that import path.
- Settings use `pydantic-settings` with `TRMNL_ANKI_` env prefix from `backend/app/config.py`.
- `pytest.ini` sets `pythonpath = backend`; run tests from repo root with `python -m pytest` after installing `backend/requirements-dev.txt`.
- FastAPI docs are disabled by default via `TRMNL_ANKI_EXPOSE_API_DOCS=false`; do not re-enable in default compose.
- JSON cache is v1 persistence; preserve last-good cards on Anki failures or empty normalization results.

## TRMNL Plugin Notes
- `trmnl-plugin/template.liquid` expects the `/api/current` shape shown in `fixtures/current-normal.json`.
- `card.furigana_html` is intended to render as ruby markup; verify on TRMNL before changing the backend/template contract.
- Layout is inspired by `trmnl-japanese`, but that repo had no explicit license; do not copy its code/CSS verbatim.

## Docker / Ops Gotchas
- `docker compose --env-file .env.example config` is the current lightweight compose verification.
- Backend binds to `127.0.0.1:${BACKEND_PORT:-8000}:8000`; reverse proxy should expose only the private TRMNL path mapped to `/api/current`.
- Real MVP is blocked until a headless Anki Desktop + AnkiConnect service replaces the placeholder and proves `version`, `deckNames`, `findCards`, `cardsInfo`, sync, and restart persistence.
- Keep `.env`, Anki profile data, `.anki2`, media, exported decks, and cached real cards out of git.

## Verification
- For backend-only changes: `python -m compileall -q backend && python -m pytest`.
- For fixtures: run `python -m json.tool fixtures/<file>.json` or parse all fixture JSON before committing.
- For packaging changes: run `docker compose --env-file .env.example config`.
- Before publish or pushing secrets-adjacent changes, scan for real URLs/tokens/AnkiWeb credentials; placeholders like `anki.example.com` and `<token>` are expected.
