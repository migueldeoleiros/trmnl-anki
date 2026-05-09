# TRMNL Hosted Private Plugin Settings Example

Use TRMNL's hosted Private Plugin in Polling mode.

- Strategy: `Polling`
- Poll URL: `https://anki.example.com/trmnl/<long-random-token>/random`
- Optional query-specific Poll URL: `https://anki.example.com/trmnl/<long-random-token>/random?deck=Core%202000&filter=is:review`
- Method: `GET`
- Headers: none by default, or a reverse-proxy auth header if your TRMNL plan supports it
- Body: empty
- Poll interval: choose in TRMNL; each poll receives a random cached card
- Markup: paste `trmnl-plugin/template.html`; it includes the CSS in a `<style>` block for TRMNL's online editor.

Do not point TRMNL at AnkiConnect. TRMNL should only poll the backend cached JSON endpoint; custom query URLs may return `not_ready` once while the backend fills the cache.
