# Reverse Proxy

The reverse proxy should terminate TLS and forward only the cached current-card route to the backend.

Example route shape:

```text
https://anki.example.com/trmnl/<long-random-token>/current -> http://backend:8000/api/current
```

Operational recommendations:

- Use a long random token in the path.
- Add basic rate limiting.
- Log request metadata, not response bodies.
- Do not route `/debug`, `/docs`, AnkiConnect `:8765`, or noVNC/KasmVNC publicly.
- If possible, restrict admin bootstrap routes to VPN or local network.

Nginx/Caddy/Traefik configs are intentionally not fixed here because Portainer host environments vary.
