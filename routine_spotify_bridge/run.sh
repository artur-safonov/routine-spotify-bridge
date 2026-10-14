#!/usr/bin/with-contenv bashio
set -euo pipefail

export SPOTIFY_CLIENT_ID="$(bashio::config 'client_id')"
export SPOTIFY_CLIENT_SECRET="$(bashio::config 'client_secret')"
export PUBLIC_BASE_URL="$(bashio::config 'public_base_url')"
export BRIDGE_TOKEN="$(bashio::config 'bridge_token')"
export SPOTIFY_MARKET="$(bashio::config 'market')"

exec python3 /app/main.py
