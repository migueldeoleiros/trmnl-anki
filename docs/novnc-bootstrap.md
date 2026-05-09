# noVNC Bootstrap

The Anki service should run Anki Desktop under Xvfb with noVNC or KasmVNC for first-time setup and maintenance.

Bootstrap flow:

1. Temporarily expose noVNC/KasmVNC only to an admin network, VPN, or localhost tunnel.
2. Launch Anki Desktop.
3. Sign in to AnkiWeb if needed.
4. Install and confirm AnkiConnect.
5. Sync the profile and confirm the `Core 2000` deck exists.
6. From backend/container context, verify AnkiConnect `version`, `deckNames`, `findCards`, and `cardsInfo`.
7. Restart the stack and confirm profile/add-on state persists.
8. Remove public noVNC/KasmVNC exposure.

The current `docker-compose.yml` includes a placeholder Anki service. Replace it with a maintained Anki Desktop image or bootstrap script before runtime validation.
