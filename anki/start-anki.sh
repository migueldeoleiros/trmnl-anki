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
ANKI_LAUNCHER_VENV_ROOT="${ANKI_LAUNCHER_VENV_ROOT:-/config/AnkiProgramFiles}"
ANKI_LAUNCHER_PYTHON_VERSION="${ANKI_LAUNCHER_PYTHON_VERSION:-3.13.5}"
ANKI_LAUNCHER_ANKI_VERSION="${ANKI_LAUNCHER_ANKI_VERSION:-25.09}"
ANKI_LAUNCHER_SYNC_COMPLETE="${ANKI_LAUNCHER_VENV_ROOT}/.sync_complete"
ANKI_LAUNCHER_SYNC_KEY="anki=${ANKI_LAUNCHER_ANKI_VERSION} python=${ANKI_LAUNCHER_PYTHON_VERSION}"

export ANKI_LAUNCHER_VENV_ROOT
export UV_CACHE_DIR="${UV_CACHE_DIR:-/config/uv-cache}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-/config/uv-python}"
export UV_HTTP_TIMEOUT="${UV_HTTP_TIMEOUT:-180}"
export UV_NATIVE_TLS="${UV_NATIVE_TLS:-1}"

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
  if [ -d "${ANKICONNECT_DIR}" ]; then
    rm -rf "${ANKICONNECT_DIR}"
  fi
  mv "${new_dir}" "${ANKICONNECT_DIR}"
  printf '%s' "${ANKICONNECT_REF}" > "${ANKICONNECT_REF_FILE}"
  rm -rf "${tmp_dir}"
  trap - EXIT
fi
rm -rf "${ANKICONNECT_DIR}.previous"

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

mkdir -p "${ANKI_LAUNCHER_VENV_ROOT}" "${UV_CACHE_DIR}" "${UV_PYTHON_INSTALL_DIR}"

cat > "${ANKI_LAUNCHER_VENV_ROOT}/pyproject.toml" <<EOF
[project]
name = "trmnl-anki-launcher"
version = "0.0.0"
requires-python = ">=${ANKI_LAUNCHER_PYTHON_VERSION}"
dependencies = [
  "anki-release==${ANKI_LAUNCHER_ANKI_VERSION}",
  "anki==${ANKI_LAUNCHER_ANKI_VERSION}",
  "aqt==${ANKI_LAUNCHER_ANKI_VERSION}",
]
EOF
printf '%s\n' "${ANKI_LAUNCHER_PYTHON_VERSION}" > "${ANKI_LAUNCHER_VENV_ROOT}/.python-version"

if [ "$(cat "${ANKI_LAUNCHER_SYNC_COMPLETE}" 2>/dev/null || true)" != "${ANKI_LAUNCHER_SYNC_KEY}" ]; then
  echo "Preparing Anki ${ANKI_LAUNCHER_ANKI_VERSION} launcher environment in '${ANKI_LAUNCHER_VENV_ROOT}'"
  /usr/local/share/anki/uv.amd64 sync \
    --project "${ANKI_LAUNCHER_VENV_ROOT}" \
    --upgrade \
    --no-config \
    --managed-python \
    --python "${ANKI_LAUNCHER_PYTHON_VERSION}"
  printf '%s\n' "${ANKI_LAUNCHER_SYNC_KEY}" > "${ANKI_LAUNCHER_SYNC_COMPLETE}"
fi

echo "Starting Anki profile '${ANKI_PROFILE}' with base '${ANKI_BASE}'"
export ANKI_LAUNCHER=/usr/local/share/anki/launcher.amd64
export ANKI_LAUNCHER_UV=/usr/local/share/anki/uv.amd64
export UV_PROJECT="${ANKI_LAUNCHER_VENV_ROOT}"
anki_cmd=(
  "${ANKI_LAUNCHER_VENV_ROOT}/.venv/bin/python"
  -c "import aqt, sys; sys.argv[0] = 'Anki'; aqt.run()"
  -b "${ANKI_BASE}"
  -p "${ANKI_PROFILE}"
  -l en
)
if [ "$(id -u)" = "0" ]; then
  exec s6-setuidgid abc "${anki_cmd[@]}"
fi
exec "${anki_cmd[@]}"
