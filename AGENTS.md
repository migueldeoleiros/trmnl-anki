# AGENTS.md

## Start Here
- Read `README.md`, `.opencode/specs/trmnl-anki.md`, `docker-compose.yml`, `.env.example`, and `backend/README.md` before changing architecture.
- The Anki runtime lives in `anki/`: KasmVNC launches real Anki Desktop and `anki/start-anki.sh` installs/configures AnkiConnect in the persistent profile.
- Treat `.opencode/specs/trmnl-anki.md` as the approved build plan unless the user explicitly supersedes it.

## Architecture Constraints
- Data source is AnkiConnect only; do not add AnkiWeb scraping, direct SQLite reads, or non-AnkiConnect APIs.
- AnkiConnect must stay internal-only on Docker networking; default compose binds it to `172.28.0.10:8765`, and public traffic should reach only the FastAPI cached endpoint.
- Backend must not mutate Anki data or proxy arbitrary AnkiConnect actions.
- TRMNL polls cached JSON from `GET /api/current`; that route must not trigger live Anki sync or slow AnkiConnect calls.
- Default deck/query is `deck:"Core 2000" (is:learn or is:review)` to include learning, relearning, young, and mature cards; keep deck names quoted in Anki search strings.

## Backend Notes
- FastAPI entrypoint is `backend.app.main:app`; Dockerfile depends on that import path.
- Settings use `pydantic-settings` with `TRMNL_ANKI_` env prefix from `backend/app/config.py`.
- `pyproject.toml` sets `pythonpath = backend`; run tests from repo root with `python -m pytest` after installing `backend/requirements-dev.txt` or `backend/requirements-dev.lock`.
- FastAPI docs are disabled by default via `TRMNL_ANKI_EXPOSE_API_DOCS=false`; do not re-enable in default compose.
- JSON cache is v1 persistence; preserve last-good cards on Anki failures or empty normalization results.
- Background sync retries with `TRMNL_ANKI_SYNC_RETRY_INTERVAL_SECONDS` after failures so startup races with AnkiConnect do not stay empty for an hour.
- AnkiWeb sync has a separate `TRMNL_ANKI_ANKICONNECT_SYNC_TIMEOUT_SECONDS`; if sync fails, backend should still try local card extraction and mark cache stale.

## TRMNL Plugin Notes
- `trmnl-plugin/template.html` expects the `/api/current` shape shown in `fixtures/current-normal.json`.
- `card.furigana_html` is intended to render as ruby markup; verify on TRMNL before changing the backend/template contract.
- Layout is inspired by `trmnl-japanese`, but that repo had no explicit license; do not copy its code/CSS verbatim.

## Docker / Ops Gotchas
- `docker compose --env-file .env.example config` is the normal lightweight compose verification; after bootstrap changes, also check `KASMVNC_PASSWORD=localtest-password docker compose --env-file .env.example -f docker-compose.yml -f docker-compose.bootstrap.yml config`.
- Backend binds to `127.0.0.1:${BACKEND_PORT:-8000}:8000`; reverse proxy should expose only the private TRMNL path mapped to `/api/current`.
- Real MVP still requires runtime proof against the headless Anki service: `version`, `deckNames`, `findCards`, `cardsInfo`, sync, and restart persistence.
- Keep `.env`, Anki profile data, `.anki2`, media, exported decks, and cached real cards out of git.

## Verification
- For backend-only changes: `python -m compileall -q backend && python -m pytest`.
- For fixtures: run `python -m json.tool fixtures/<file>.json` or parse all fixture JSON before committing.
- For packaging changes: run `docker compose --env-file .env.example config`.
- Before publish or pushing secrets-adjacent changes, scan for real URLs/tokens/AnkiWeb credentials; placeholders like `anki.example.com` and `<token>` are expected.
