# Privacy And Security

## Public Surface

Expose only the backend cached JSON endpoint. Do not expose AnkiConnect, noVNC/KasmVNC, Anki profile files, or debug endpoints publicly.

Recommended controls:

- HTTPS only.
- Long random endpoint path, for example `/trmnl/<token>/current`.
- Rate limit the endpoint.
- Avoid logging full JSON payloads.
- Disable public indexing and directory listings.
- Put noVNC/KasmVNC behind admin-only authentication or bind it to localhost/VPN.

## Secrets

Do not commit `.env`, AnkiWeb credentials, Anki profile data, cached real cards, exported decks, or media collections. Fixture files in this repository are sanitized examples only.

## AnkiConnect

AnkiConnect can mutate Anki data. Keep it on the internal Docker network and let the backend call only approved read/sync actions. The backend must not proxy arbitrary AnkiConnect requests.

If you set `ANKICONNECT_API_KEY`, compose passes the same value to the Anki service and backend. Do not expose or commit that value.
