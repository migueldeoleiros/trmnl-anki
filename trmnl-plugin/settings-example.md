# TRMNL Hosted Private Plugin Settings Example

Use TRMNL's hosted Private Plugin in Polling mode.

- Strategy: `Polling`
- Poll URL: `https://anki.example.com/trmnl/<long-random-token>/current`
- Method: `GET`
- Headers: none by default, or a reverse-proxy auth header if your TRMNL plan supports it
- Body: empty
- Poll interval: `30 minutes` default; `15 minutes` is supported by this project if TRMNL allows it
- Markup: paste `trmnl-plugin/template.liquid`
- CSS: paste `trmnl-plugin/styles.css`

Do not point TRMNL at AnkiConnect. TRMNL should only poll the backend cached JSON endpoint.
