# TRMNL Hosted Private Plugin Settings Example

Use TRMNL's hosted Private Plugin in Polling mode.

- Strategy: `Polling`
- Poll URL: `https://anki.example.com/trmnl/<long-random-token>/current`
- Optional query-specific Poll URL: `https://anki.example.com/trmnl/<long-random-token>/current?deck=Core%202000&filter=is:review&cadence_minutes=30`
- Method: `GET`
- Headers: none by default, or a reverse-proxy auth header if your TRMNL plan supports it
- Body: empty
- Poll interval: `30 minutes` default; `15 minutes` is supported by this project if TRMNL allows it
- Markup: paste `trmnl-plugin/template.html`; it includes the CSS in a `<style>` block for TRMNL's online editor.

Do not point TRMNL at AnkiConnect. TRMNL should only poll the backend cached JSON endpoint; custom query URLs may return `not_ready` once while the backend fills the cache.
