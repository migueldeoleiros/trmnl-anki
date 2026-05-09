#!/usr/bin/env bash
set -euo pipefail

ANKI_BASE="${ANKI_BASE:-/config/Anki2}"
ANKI_PROFILE="${ANKI_PROFILE:-User 1}"
ANKICONNECT_ADDON_ID="${ANKICONNECT_ADDON_ID:-2055492159}"
ANKICONNECT_DIR="${ANKI_BASE}/addons21/${ANKICONNECT_ADDON_ID}"
ANKICONNECT_BIND_ADDRESS="${ANKICONNECT_BIND_ADDRESS:-172.28.0.10}"
ANKICONNECT_BIND_PORT="${ANKICONNECT_BIND_PORT:-8765}"
ANKICONNECT_REF="${ANKICONNECT_REF:-23.10.29.0}"
ANKICONNECT_REF_FILE="${ANKICONNECT_DIR}/.trmnl-anki-ref"

mkdir -p "${ANKI_BASE}/addons21"

installed_ref=""
if [ -f "${ANKICONNECT_REF_FILE}" ]; then
  installed_ref="$(cat "${ANKICONNECT_REF_FILE}")"
fi

if [ ! -f "${ANKICONNECT_DIR}/__init__.py" ] || [ "${installed_ref}" != "${ANKICONNECT_REF}" ]; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "${tmp_dir}"' EXIT
  new_dir="${tmp_dir}/addon"
  curl -fsSL "https://github.com/FooSoft/anki-connect/archive/refs/tags/${ANKICONNECT_REF}.tar.gz" \
    | tar -xz -C "${tmp_dir}" --strip-components=1
  test -f "${tmp_dir}/plugin/__init__.py"
  mkdir -p "${new_dir}"
  cp -a "${tmp_dir}/plugin/." "${new_dir}/"
  rm -rf "${ANKICONNECT_DIR}.previous"
  if [ -d "${ANKICONNECT_DIR}" ]; then
    mv "${ANKICONNECT_DIR}" "${ANKICONNECT_DIR}.previous"
  fi
  mv "${new_dir}" "${ANKICONNECT_DIR}"
  printf '%s' "${ANKICONNECT_REF}" > "${ANKICONNECT_REF_FILE}"
  rm -rf "${tmp_dir}"
  trap - EXIT
fi

jq -n \
  --arg bind "${ANKICONNECT_BIND_ADDRESS}" \
  --argjson port "${ANKICONNECT_BIND_PORT}" \
  --arg key "${ANKICONNECT_API_KEY:-}" \
  '{
    apiKey: (if $key == "" then null else $key end),
    apiLogPath: null,
    webBindAddress: $bind,
    webBindPort: $port,
    webCorsOriginList: ["http://localhost"],
    ignoreOriginList: []
  }' > "${ANKICONNECT_DIR}/config.json"

echo "Starting Anki profile '${ANKI_PROFILE}' with base '${ANKI_BASE}'"
exec anki -b "${ANKI_BASE}" -p "${ANKI_PROFILE}"
