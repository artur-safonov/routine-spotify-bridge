# Routine Spotify Bridge

This Home Assistant OS app keeps Spotify credentials off the ESP32 and exposes
only a small, token-protected LAN API to the display. Search, library, playback
and device selection use Spotify's official Web API.

## Install on Home Assistant OS

1. Copy this directory to `/addons/routine_spotify_bridge` on the Home Assistant
   host (the Samba or SSH app can provide access to `/addons`).
2. In **Settings > Apps > App store**, reload the local apps list.
3. Open **Routine Spotify Bridge** and install it.

## Connect Spotify

1. Create or reuse a Spotify Developer application with **Web API** enabled.
2. Configure `public_base_url` to the address you will use for OAuth, and register
   that exact address plus `/callback` in Spotify's developer dashboard.
   Spotify requires HTTPS for hostnames; `http://homeassistant.local:8099/callback`
   is not an accepted new redirect URI. Use an HTTPS reverse proxy forwarding
   to this app. Alternatively, for a local setup session, forward the app's port
   to your computer and use an explicit loopback address such as
   `http://127.0.0.1:8099/callback`. The browser must run on that computer.
   See [Spotify's redirect URI requirements](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri).
3. On your computer, run `python tools/generate_token.py` from this directory.
   It creates a random 256-bit token and matching configuration fragments in
   `.private/`. Merge `addon-options.fragment.json` into the app options; also
   enter the Client ID, Client Secret and `public_base_url`. Do not replace the
   whole options file with the fragment: it contains only `bridge_token`.
4. Start the app and open its Web UI.
5. Select **Connect Spotify** and approve access.
6. Merge `.private/display-secrets.fragment.yaml` into the firmware `secrets.yaml`
   and compile/flash the display. It contains the same generated token under
   `spotify_bridge_token`. The firmware's LAN bridge URL can remain separate
   from the HTTPS/loopback address used for browser OAuth.

The ESPHome display uses port `8099` and sends the bridge token in the
`X-Bridge-Token` header. Spotify credentials and refresh tokens remain inside the
Home Assistant app data directory.

The default bridge token is empty, and the app refuses to start until a valid
one is configured. Accepted tokens have at least 32 URL-safe characters; the
generator produces 43 characters. Tokens are never embedded in the public
source, displayed on the setup page, or printed by the generator.

For an existing installation, keep a valid existing token to avoid interrupting
the display. If replacing a token, update the app and display together. These
local source changes do not migrate or restart an installed app automatically.

Keep `.private/`, Spotify refresh tokens, real app options and `secrets.yaml`
out of Git and Docker build contexts. The included ignore files exclude them.

Playback control requires a Spotify account/API application for which Spotify
permits the playback endpoints. At least one Spotify Connect device must be
visible before transfer or playback can start.
