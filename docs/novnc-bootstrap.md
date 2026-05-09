# noVNC Bootstrap

The Anki service should run Anki Desktop under Xvfb with noVNC or KasmVNC for first-time setup and maintenance.

Bootstrap flow:

1. Set a non-empty `KASMVNC_PASSWORD`.
2. Temporarily use `docker-compose.bootstrap.yml` to expose noVNC/KasmVNC only to localhost, an admin network, VPN, or localhost tunnel.
3. Launch Anki Desktop.
4. Sign in to AnkiWeb if needed.
5. Confirm AnkiConnect is installed under `/config/Anki2/addons21/2055492159`; `anki/start-anki.sh` installs it automatically if absent.
6. Sync the profile and confirm the `Core 2000` deck exists.
7. From backend/container context, verify AnkiConnect `version`, `deckNames`, `findCards`, and `cardsInfo`.
8. Restart the stack and confirm profile/add-on state persists.
9. Remove `docker-compose.bootstrap.yml` from the running stack so KasmVNC is no longer published.

The current `docker-compose.yml` builds `anki/Dockerfile`. KasmVNC ports are only exposed inside Docker by default; publish port `3000` temporarily and only behind admin-only access for bootstrap.
