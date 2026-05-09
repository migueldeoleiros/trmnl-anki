---
approval_state: approved
slug: trmnl-anki-deployment-readiness
created: 2026-05-09
updated: 2026-05-09
owner: build
---

# TRMNL Anki Deployment Readiness

## Metadata
- Active spec path: .opencode/specs/trmnl-anki-deployment-readiness.md
- Approval state: approved
- Owner: build

## Objective
Prepare the working local backend for a safe public GitHub push, then determine when the project is ready to move deployment to the server via Portainer stack. Tell the user it is ready for server deployment only after the ready-for-server gate is satisfied.

## Non-Goals
- Do not deploy to the server during this phase unless the user explicitly requests it after readiness is confirmed.
- Do not expose the backend or AnkiConnect publicly during this phase; public reverse proxy/TRMNL URL comes later.
- Do not add AnkiWeb scraping, direct SQLite reads, or non-AnkiConnect APIs.
- Do not mutate Anki data from the backend or add arbitrary AnkiConnect proxying.
- Do not use the bootstrap overlay for normal runtime.

## Constraints
- Data source is AnkiConnect only.
- AnkiConnect stays internal-only on Docker networking, with default compose binding to `172.28.0.10:8765`.
- Public traffic, when added later, must reach only the FastAPI cached endpoint, not AnkiConnect.
- `GET /api/current` must serve cached JSON and must not trigger live Anki sync or slow AnkiConnect calls.
- Backend must not mutate Anki data or proxy arbitrary AnkiConnect actions.
- Normal stack uses `docker-compose.yml` without `docker-compose.bootstrap.yml`.
- Bootstrap overlay is for admin setup/recovery only, including first Anki login/sync when needed, and must be removed afterward.
- Keep `.env`, credentials, AnkiWeb data, Anki profile data, `.anki2`, media, exported decks, cached real cards, and tokens out of git.
- GitHub repo is public: `https://github.com/migueldeoleiros/trmnl-anki.git`; pushing is approved only if no credentials or private data are pushed.
- Stage explicit reviewed paths only; stop on unexpected changes.
- Reverse proxy/TRMNL public URL is later; local-only access first.

## Relevant Files
- `README.md` - project setup and deployment docs that may need readiness notes.
- `.opencode/specs/trmnl-anki.md` - approved project build plan and architecture constraints.
- `.opencode/specs/trmnl-anki-deployment-readiness.md` - active execution spec for this next phase.
- `AGENTS.md` - repo-specific architecture, verification, and safety rules.
- `docker-compose.yml` - normal Portainer stack source and local runtime config.
- `docker-compose.bootstrap.yml` - admin setup/recovery overlay only.
- `.env.example` - committed safe environment template and compose config input.
- `.gitignore` - safety boundary for secrets, profiles, media, cache, and exported decks.
- `backend/README.md` - backend behavior and local validation notes.
- `backend/app/config.py` - `TRMNL_ANKI_` settings and default env behavior.
- `backend/app/main.py` - FastAPI app entrypoint and cached endpoint behavior.
- `fixtures/current-normal.json` - expected `/api/current` shape for TRMNL template compatibility.
- `trmnl-plugin/template.liquid` - TRMNL consumer of `/api/current` response contract.

## Decisions
- Proceed with an approved execution spec because the user approved the next phase from local backend to GitHub push and later Portainer deployment.
- Use public GitHub remote `https://github.com/migueldeoleiros/trmnl-anki.git`; set or correct the remote only if needed and only to this target.
- Push to `main` after reviewed staging, successful local checks, and secret/data safety checks.
- Keep server deployment as a handoff, not part of the push phase, until the ready-for-server gate passes.
- Portainer stack must use environment values entered in Portainer, not a committed `.env`.
- Optional real sync proof is user-triggered only because it touches real Anki sync state.

## Tasks
- [ ] T-001: Preflight git state: confirm branch, HEAD SHA, working tree status, and remote target; set remote to `https://github.com/migueldeoleiros/trmnl-anki.git` only if needed; review diffs for all dirty files before staging; stop on unexpected changes.
- [ ] T-002: Secret/data safety: scan working tree and recent/unpushed history for `.env`, credentials, AnkiWeb data, profile files, `.anki2`, media, exported decks, cached real cards, real URLs, and tokens; verify `.gitignore` coverage; stop on suspicious findings.
- [ ] T-003: Local readiness checks: run `python -m compileall -q backend`, `python -m pytest`, `docker compose --env-file .env.example config`, and `KASMVNC_PASSWORD=localtest-password docker compose --env-file .env.example -f docker-compose.yml -f docker-compose.bootstrap.yml config`.
- [ ] T-004: Local runtime proof: start the normal stack without bootstrap; verify `/health`, `/api/current`, a non-stale cached card, AnkiConnect not host-public, and restart persistence for cache, profile, and AnkiConnect add-on.
- [ ] T-005: Optional real sync proof: if and only if the user explicitly requests it, run AnkiDroid -> AnkiWeb -> server Anki sync -> backend cache validation, warning first that this touches real Anki sync state.
- [ ] T-006: Commit reviewed changes: stage explicit reviewed paths only and commit runtime, query, and deployment-readiness changes with no secrets or private data.
- [ ] T-007: Push verification: ensure `origin` is `https://github.com/migueldeoleiros/trmnl-anki.git`, push `main`, and verify the pushed SHA matches local HEAD.
- [ ] T-008: Ready-for-server gate: tell the user ready only when GitHub `main` has the expected commit SHA, local compose renders, local runtime survives restart, no secrets/profile/cache/media are committed, and server env checklist is clear.
- [ ] T-009: Portainer handoff notes: prepare server steps for stack creation from GitHub `main`, Portainer env values, bootstrap overlay use/removal, local-only exposure, and validation of `/health`, `/api/current`, and non-public AnkiConnect.

## Evidence Log
- 2026-05-09 T-001: User request -> approved next phase specified; no git inspection performed in plan phase.
- 2026-05-09 T-008: User request -> ready-for-server gate criteria captured.

## Risks / Blockers
- Public GitHub repo makes any committed secret, profile, media, exported deck, or cached real card high impact.
- Dirty working tree may contain user changes; build must review diffs and stop on unexpected changes.
- Recent or unpushed history may contain sensitive data even if the working tree is clean.
- Optional real sync proof can alter real Anki sync state and must not run without explicit user approval.
- Server networking can accidentally expose AnkiConnect if Portainer env/ports are changed from the intended local-only model.

## Handoff State
- Active task IDs: T-001, T-002, T-003, T-004, T-006, T-007, T-008, T-009
- Build Handoff: Switch to build after this spec write. Use worker boundaries: Worker A handles preflight, dirty diffs, secret/history scan, `.gitignore`, and git remote safety; Worker B handles local validation, normal runtime checks, non-public AnkiConnect proof, and restart persistence; Worker C handles docs/readiness cleanup if needed without changing architecture; Worker D handles explicit staging, commit, push SHA verification, and Portainer handoff notes. Do not mark implementation complete until all non-optional tasks pass. Do not run T-005 unless the user explicitly asks for real sync proof.
