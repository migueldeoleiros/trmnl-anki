---
approval_state: approved
slug: trmnl-anki
created: 2026-05-09
updated: 2026-05-09
owner: build
---

# TRMNL Anki Private Plugin

## Metadata
- Active spec path: .opencode/specs/trmnl-anki.md
- Approval state: approved
- Owner: build

## Objective
Build an open-source personal TRMNL hosted Private Plugin and Python/FastAPI backend that shows a different Anki card every 15 or 30 minutes on TRMNL OG 2-bit. Use AnkiConnect as the only data source. The user studies mostly on AnkiDroid and syncs to AnkiWeb. The server runs headless Anki Desktop plus AnkiConnect in the same server/Portainer stack as the backend, syncs from AnkiWeb hourly by default, caches normalized cards, and exposes a reverse-proxied HTTPS JSON endpoint polled by the TRMNL hosted Private Plugin.

The frontend should be inspired by the `trmnl-japanese` Japanese word-of-day layout, without QR code. Do not copy code or CSS verbatim because no explicit license was found.

## Non-Goals
- Do not use data sources other than AnkiConnect.
- Do not mutate Anki data from the backend.
- Do not proxy arbitrary AnkiConnect actions through the public or backend API.
- Do not expose AnkiConnect directly to the public internet.
- Do not expose noVNC publicly without admin-only protection.
- Do not commit secrets, cached real cards, Anki profile data, or AnkiWeb credentials.
- Do not copy code or CSS verbatim from `trmnl-japanese`.

## Constraints
- Use Python FastAPI for the backend.
- Use Docker/Portainer for deployment.
- Run headless Anki Desktop under Xvfb with noVNC for setup and maintenance.
- Keep AnkiConnect internal-only on the Docker network.
- Protect noVNC as admin-only.
- Use TRMNL hosted Private Plugin Polling.
- Public endpoint serves cached data only.
- Default Anki sync interval is `3600` seconds and must be configurable.
- Default TRMNL rotation cadence is `30` minutes and must be configurable; `15` minutes must be possible.
- Use JSON file cache for v1.
- Use default Anki query `rated:7 deck:"Core 2000"`.
- Fall back to `deck:"Core 2000"` if there are not enough cards.
- Deck name is `Core 2000`; quote it in Anki query syntax.
- Field mapping: headword uses `Vocabulary-Kanji -> Expression -> Vocabulary-Kana`.
- Field mapping: furigana/reading uses `Vocabulary-Furigana -> Reading -> Vocabulary-Kana`.
- Field mapping: meaning uses `Vocabulary-English`.
- Field mapping: sentence uses `Sentence-Kana`.
- Field mapping: sentence translation uses `Sentence-English`.
- Furigana should render above kanji using `ruby`/`rt` if possible.

## Relevant Files
- `backend/` - FastAPI app, AnkiConnect client, sync job, cache, current-card API, health/debug endpoints.
- `trmnl-plugin/` - Hosted Private Plugin Liquid/CSS template and fixture-driven layout assets.
- `docker-compose.yml` - Portainer-compatible stack for backend, headless Anki Desktop, Xvfb/noVNC, internal networking, volumes.
- `.env.example` - Documented configuration keys without secrets.
- `fixtures/` - Sanitized sample AnkiConnect responses and current-card JSON for backend and template development.
- `docs/` - Setup, operations, security, sync, TRMNL plugin configuration, troubleshooting.
- `README.md` - Open-source project overview, quick start, architecture, and publishing notes.
- `.opencode/specs/trmnl-anki.md` - Approved execution spec and handoff state.

## Decisions
- Python FastAPI is locked for the backend to keep the service small, testable, and easy to deploy.
- Docker/Portainer is locked for deployment because the server stack will be managed there.
- Headless Anki Desktop plus AnkiConnect is required because AnkiConnect is the only approved data source.
- Anki runs under Xvfb with noVNC for first-time profile setup and later maintenance.
- AnkiConnect listens only on the internal Docker network to avoid exposing mutating APIs.
- noVNC is admin-only and protected because GUI prompts and setup may expose sensitive account state.
- The backend reads from AnkiConnect and never mutates Anki data.
- The backend never proxies arbitrary AnkiConnect actions; it exposes only purpose-built cached/read-only endpoints.
- TRMNL hosted Private Plugin uses Polling against a reverse-proxied HTTPS JSON endpoint.
- The public endpoint returns cached data only to reduce Anki exposure and survive backend/Anki failures.
- The default Anki sync interval is 3600 seconds, configurable by environment.
- The default TRMNL card rotation is 30 minutes, configurable, with 15 minutes supported if TRMNL limits allow.
- v1 uses a JSON file cache to avoid introducing a database before the runtime shape is proven.
- Card selection uses deterministic wall-clock slots: `floor(now / cadence_minutes)`.
- The frontend is visually inspired by `trmnl-japanese` but original in code and CSS because the reference repo has no explicit license.

## Architecture
AnkiDroid -> AnkiWeb -> hourly configurable sync -> headless Anki Desktop container -> AnkiConnect `:8765` internal Docker network -> FastAPI backend -> cached current-card endpoint -> reverse proxy HTTPS -> TRMNL hosted Private Plugin polling -> TRMNL OG.

## Tasks
- [ ] T-001: Runtime proof - build minimal Portainer stack with Anki service and backend skeleton.
- [ ] T-002: Runtime proof - bootstrap Anki via noVNC and install/confirm AnkiConnect.
- [ ] T-003: Runtime proof - verify AnkiConnect `version`, `deckNames`, `findCards`, and `cardsInfo` from backend/container context.
- [ ] T-004: Runtime proof - confirm `Core 2000` deck exists.
- [ ] T-005: Runtime proof - prove restart preserves Anki profile and add-on state.
- [ ] T-006: Runtime proof - prove AnkiConnect is not public.
- [ ] T-007: Sync proof - implement configurable sync job trigger.
- [ ] T-008: Sync proof - record `last_sync_at`, `last_sync_status`, `last_sync_error`, and `last_success_at`.
- [ ] T-009: Sync proof - prove AnkiDroid review -> AnkiWeb sync -> server Anki sync -> backend sees reviewed card.
- [ ] T-010: Sync proof - prove failed sync does not clear cache.
- [ ] T-011: Data extraction - use `findCards` and `cardsInfo`, optionally `cardsToNotes`/`notesInfo` if needed.
- [ ] T-012: Data extraction - inspect 10 sample notes from `Core 2000`.
- [ ] T-013: Data extraction - lock observed furigana format and renderer contract.
- [ ] T-014: Data extraction - skip unusable cards and count included/skipped cards.
- [ ] T-015: Cache/rotation - implement JSON cache for normalized cards and status metadata.
- [ ] T-016: Cache/rotation - implement deterministic wall-clock slot `floor(now / cadence_minutes)`.
- [ ] T-017: Cache/rotation - prove same slot returns same card and next slot returns a different card when possible.
- [ ] T-018: Cache/rotation - prove restart preserves cache.
- [ ] T-019: Cache/rotation - serve stale fallback when Anki is unavailable.
- [ ] T-020: Public FastAPI endpoint - implement `/health`.
- [ ] T-021: Public FastAPI endpoint - implement `/api/current` returning compact JSON with `schema_version`, `status`, `generated_at`, `last_sync_at`, `slot_id`, `cadence_minutes`, `stale`, and card fields including `furigana_html`.
- [ ] T-022: Public FastAPI endpoint - optionally implement protected internal debug endpoint.
- [ ] T-023: Public FastAPI endpoint - document HTTPS reverse proxy, long unguessable path recommendation, rate limit, and avoiding full payload logs.
- [ ] T-024: TRMNL template - create hosted Private Plugin Polling template with original Liquid/CSS inspired by `trmnl-japanese`.
- [ ] T-025: TRMNL template - omit QR code.
- [ ] T-026: TRMNL template - design full-screen first layout with large furigana/headword, meaning, sentence, translation, and tiny stale/last-sync marker.
- [ ] T-027: TRMNL template - handle empty, stale, and error states.
- [ ] T-028: Docker/open-source packaging - create repo layout `backend/`, `trmnl-plugin/`, `docker-compose.yml`, `.env.example`, `fixtures/`, `docs/`, `README.md`.
- [ ] T-029: Docker/open-source packaging - ensure no secrets, cached real cards, or profile data are committed.
- [ ] T-030: Docker/open-source packaging - run secret scan before publish.

## Validation
- Go/no-go: headless Anki restarts and preserves profile/add-on state.
- Go/no-go: unattended Anki sync succeeds without GUI prompts.
- Go/no-go: AnkiDroid-to-TRMNL end-to-end path works after AnkiDroid sync and server sync.
- Go/no-go: failed sync or offline Anki leaves stale cached data available.
- Go/no-go: TRMNL OG 2-bit layout remains readable.
- Go/no-go: long headword, long sentence, and long translation remain usable.
- Go/no-go: empty cache returns a clear empty/error state without crashing backend or template.
- Go/no-go: reverse-proxied HTTPS endpoint is reachable from TRMNL and AnkiConnect is not reachable publicly.
- Go/no-go: repository contains no secrets, cached real cards, Anki profile data, or AnkiWeb credentials.

## Evidence Log
- 2026-05-09 SPEC: User approved direction captured in `.opencode/specs/trmnl-anki.md` -> ready for build handoff.

## Risks / Blockers
- Headless Anki is brittle and heavy, but required because AnkiConnect is the only approved data source.
- AnkiConnect sync may be fire-and-forget or stall on GUI prompts.
- AnkiDroid sync lag may delay reviewed cards reaching AnkiWeb and then server Anki.
- AnkiConnect mutating API must remain internal-only.
- Public endpoint may leak non-critical card content unless protected with obfuscated path, rate limiting, and careful logging.
- Deck query syntax must quote `Core 2000`.
- Furigana field format is unknown until sample notes are inspected.
- TRMNL refresh limits may force 30-minute cadence.
- Reference `trmnl-japanese` repo lacks explicit license, so inspiration only; no copied code/CSS.

## Handoff State
- Active task IDs: T-001, T-002, T-003, T-004, T-005, T-006
- Build Handoff: Switch to build agent after this spec write is complete. Start with runtime proof before product implementation. Worker A owns headless Anki/Portainer runtime spike: T-001 through T-006. Worker B owns FastAPI skeleton, cache, AnkiConnect client, sync state, and current-card API: T-007 through T-023, with backend extraction dependent on T-003 and T-012. Worker C owns TRMNL template and fixtures: T-024 through T-027, can start from sanitized fixture in parallel. Worker D owns docs and repo hygiene after contracts stabilize: T-028 through T-030. Dependencies: runtime proof and field sample must complete before final furigana renderer; TRMNL capability spike can run with fixture in parallel; backend extraction depends on AnkiConnect proof.
