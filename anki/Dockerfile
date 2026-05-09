FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm

ARG ANKI_LAUNCHER_URL=https://apps.ankiweb.net/downloads/current/anki-launcher-linux.tar.zst
ARG ANKICONNECT_REF=23.10.29.0

ENV ANKI_BASE=/config/Anki2 \
    ANKI_PROFILE="User 1" \
    ANKICONNECT_BIND_ADDRESS=0.0.0.0 \
    ANKICONNECT_BIND_PORT=8765 \
    ANKICONNECT_REF=${ANKICONNECT_REF}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        jq \
        libnss3 \
        libxcb-cursor0 \
        libxcb-xinerama0 \
        tar \
        zstd \
        fonts-noto-cjk \
        fonts-noto-color-emoji \
        xterm \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "${ANKI_LAUNCHER_URL}" -o /tmp/anki-launcher.tar.zst \
    && mkdir -p /tmp/anki-launcher \
    && tar --zstd -xf /tmp/anki-launcher.tar.zst -C /tmp/anki-launcher --strip-components=1 \
    && /tmp/anki-launcher/install.sh \
    && rm -rf /tmp/anki-launcher /tmp/anki-launcher.tar.zst

COPY start-anki.sh /opt/trmnl-anki/start-anki.sh
COPY root/defaults/autostart /defaults/autostart
RUN chmod +x /opt/trmnl-anki/start-anki.sh /defaults/autostart

EXPOSE 3000 3001 8765
