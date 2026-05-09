---
approval_state: complete
slug: trmnl-anki-flexible-api
created: 2026-05-10
updated: 2026-05-10
owner: build
---

# TRMNL Anki Flexible API

## Metadata
- Active spec path: .opencode/specs/trmnl-anki-flexible-api.md
- Approval state: complete
- Owner: build

## Objective
Evolve the proof-of-concept TRMNL Anki backend/template into a more flexible cached API. Return selected extra text data so TRMNL display can change without backend edits, especially sentence furigana. Generalize `GET /api/current` so users can request different Anki searches via URL query params while keeping AnkiConnect internal and keeping TRMNL polls cached-only.

## Non-Goals
- Do not add AnkiWeb scraping, direct SQLite reads, or non-AnkiConnect APIs.
- Do not mutate Anki data.
- Do not proxy arbitrary AnkiConnect actions.
- Do not make `GET /api/current` trigger live Anki sync or slow AnkiConnect calls.
- Do not add all raw AnkiConnect data to the public payload.
- Do not commit secrets, real card cache/profile/media/exported decks, or real field inspection text.

## Constraints
- AnkiConnect remains the only data source and must remain internal-only.
- `GET /api/current` must be cache-only; cold custom queries return `not_ready` and register background fill.
- Preserve last-good cards for a query on Anki failures or empty normalization results.
- Failure for one query must not affect other cache entries.
- Keep deck names quoted and escaped in composed Anki search strings.
- URL cadence values allowed only `15`, `30`, or `60`.
- Default cache limits: max query length `500`, max cached queries `25`, max cards/query `250`, refresh concurrency `1`.
- Metadata must be privacy-safe by default: return `query_key` and `query_label`, not raw query.
- Selected extras only: `sentence_furigana_html`, `sentence_reading`, and limited selected fields with strict sanitizer.
- HTML selected fields may allow only `ruby`, `rt`, `rp`, `rb`, and `br`; strip scripts, styles, event attrs, images, and links.
- Plain selected fields remain escaped/plain text.

## Relevant Files
- `backend/app/main.py` - FastAPI route surface for `GET /api/current` params, validation, and response metadata.
- `backend/app/service.py` - Background sync, per-query refresh orchestration, startup prewarm, and cached-only request handling.
- `backend/app/cache.py` - Cache v2 persistence, v1 migration, pending entries, atomic writes, eviction, and per-query last-good state.
- `backend/app/config.py` - Limits, default query, cadence, and environment configuration.
- `backend/app/normalize.py` - Card normalization extras, selected fields, sentence furigana/readings, and sanitizer integration.
- `backend/app/ankiconnect.py` - Read-only AnkiConnect calls for field inspection and per-query extraction.
- `backend/app/rotation.py` - Card selection behavior against per-query card sets.
- `backend/tests/test_rotation_cache_normalize.py` - Existing backend contract tests to extend for cache, params, normalization, and sanitizer behavior.
- `fixtures/current-normal.json` - Existing response fixture to update for added metadata and card extras.
- `fixtures/current-not-ready.json` - New not-ready fixture for cold query response.
- `trmnl-plugin/template.html` - TRMNL template should prefer `card.sentence_furigana_html` and fallback to `card.sentence`.
- `README.md` - User-facing API/query/cadence/cache behavior documentation.
- `backend/README.md` - Backend operation, configuration, and verification documentation.
- `.env.example` - New/updated configurable limits and defaults.
- `docker-compose.yml` - Compose verification target and default internal AnkiConnect/public backend constraints.
- `docs/` - Additional docs if API/cache behavior needs deeper explanation.
- `AGENTS.md` - Guidance updates only if implementation constraints change.

## Decisions
- URL shape uses query params on `GET /api/current`.
- Arbitrary Anki search strings are allowed through `query`.
- Payload exposes selected extras, not all raw card data.
- Cache is per-query.
- Sentence furigana field must be inspected from live fields first.
- Cold custom query returns `status: not_ready`, `card: null`, metadata, and registers a pending background fill.
- Cache v2 may remain one JSON file with entries keyed by `query_key`.
- Preserve and migrate current v1 cache into the default query entry.
- Atomic cache writes remain required.
- `query_key = hash(schema_version + normalized effective_query + selected field contract)`.
- `cadence_minutes` is not part of `query_key`; cadence is per-query metadata.
- Cadence conflicts use shortest allowed cadence; later longer cadences do not lengthen an existing query cadence.
- Eviction prefers entries with no cards, then oldest `last_accessed_at`; never evict default unless cache has only default.
- Metadata uses `query_key` and `query_label` by default; do not echo raw query.
- `query_label` values are `default` for no params, deck name for `deck=...`, and `custom` for raw `query=...`.
- Initially selected fields: `Vocabulary-Kanji`, `Vocabulary-Furigana`, `Vocabulary-Kana`, `Vocabulary-English`, `Expression`, `Reading`, discovered sentence furigana field, `Sentence-Kana`, `Sentence-English`.
- Parallel worker tracks after spec persistence: Worker A cache v2/migration/pending/eviction; Worker B API params/composition/response/cached-only tests; Worker C live field inspection/normalization extras/sanitizer; Worker D scheduler/prewarm/background refresh; Worker E template/fixtures/docs.
- Merge order: contract tests -> cache/API -> scheduler/normalizer -> template/docs -> full verification.

## Request Contract
- `GET /api/current`
- `GET /api/current?query=deck:%22Core%202000%22%20(is:learn%20or%20is:review)`
- `GET /api/current?deck=Core%202000&filter=is:review`
- Optional `cadence_minutes=15|30|60`.
- Mixing `query` with `deck` or `filter` returns 400.
- Empty custom query returns 400.
- Query over 500 chars returns 400.
- `query` wins alone and is raw Anki search.
- `deck` plus optional `filter` composes `deck:"escaped deck name"` or `deck:"escaped deck name" (<filter>)`.
- No params use default env query.

## Response Contract
- Existing fields remain: `schema_version`, `status`, `generated_at`, `last_sync_at`, `last_success_at`, `last_sync_status`, `last_sync_error`, `error`, `slot_id`, `cadence_minutes`, `stale`, `card`.
- Add `query_key`, `query_label`, `next_refresh_at`.
- Do not echo raw query by default.
- Cold miss returns `status: not_ready`, `card: null`, metadata, and registers idempotent pending entry with `first_seen_at`, `next_due_at=now`, `cadence_minutes`.
- Failed refresh or empty normalized result preserves last-good cards for that query and marks it stale/error.

## Tasks
- [x] T-101: Phase 0 inspect live Core 2000 fields via read-only AnkiConnect `findCards`, `cardsInfo`, maybe `notesInfo`; output only field names/counts/redacted shapes; identify sentence furigana alias or unavailable.
- [x] T-102: Phase 1 add contract tests for params, composition, query key stability, cadence validation, cached-only request path, and not_ready fixture.
- [x] T-103: Phase 2 implement cache v2, v1 migration, pending registration, limits, eviction, and per-query last-good preservation.
- [x] T-104: Phase 3 implement refresh scheduler: separate global AnkiWeb sync from per-query extraction; register/prewarm default query on startup; refresh due entries one at a time; dedupe repeated polls.
- [x] T-105: Phase 4 implement API params, validation, query composition, cache-only lookup/register, and frozen response metadata.
- [x] T-106: Phase 5 implement normalization extras and sanitizer tests.
- [x] T-107: Phase 6 update TRMNL template to prefer `card.sentence_furigana_html`, fallback to `card.sentence`; update fixtures/docs/env examples.
- [x] T-108: Verification: run `python -m compileall -q backend`, `python -m pytest`, `docker compose --env-file .env.example config`, optional live server smoke after deploy.

## Validation
- `python -m compileall -q backend`
- `python -m pytest`
- `docker compose --env-file .env.example config`
- Optional live server smoke after deploy for default query, custom raw query, deck/filter query, cold not_ready, and background fill.
- Field inspection evidence must include only field names/counts/redacted shapes, not real card text.

## Evidence Log
- 2026-05-10 T-101: User-approved plan captured in `.opencode/specs/trmnl-anki-flexible-api.md` -> approved for build handoff.
- 2026-05-10 T-101: Initial live field inspection saw no `Sentence-Furigana` or `Sentence-Reading`; later user clarified this Core 2000 card type stores the sentence in `Expression` and sentence reading in `Reading`, so normalization now treats `Expression` as the preferred sentence source and `Reading` as the preferred sentence reading source.
- 2026-05-10 T-102/T-103/T-104/T-105/T-106/T-107: Implementation -> schema v2 per-query cache, cached-only query params, scheduler due refresh before sync, normalization extras, template, docs, and fixtures complete.
- 2026-05-10 T-108: `python -m compileall -q backend` -> passed.
- 2026-05-10 T-108: `/tmp/opencode/trmnl-anki-venv/bin/python -m pytest` -> passed, 22 tests.
- 2026-05-10 T-108: `docker compose --env-file .env.example config` -> passed.
- 2026-05-10 T-108: Fixture JSON validation -> passed.

## Risks / Blockers
- Arbitrary query privacy: custom searches can expose matching Anki content if the endpoint leaks publicly.
- Cold first poll returns `not_ready` until the background tick fills the cache.
- True ruby sentence furigana is unavailable in current Core 2000 fields.
- Future decks may need configurable sentence field aliases.

## Handoff State
- Active task IDs: None
- Build Handoff: Implementation and verification complete; monitor residual risks before broader exposure.
