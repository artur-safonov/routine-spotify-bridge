# Routine Spotify Bridge

A small local API for the Routine Controller display. It implements Spotify OAuth,
search, library browsing, playback control and Spotify Connect device selection.

This is a standalone Home Assistant OS app. Copy this directory to
`/addons/routine_spotify_bridge` and follow [the setup guide](DOCS.md).
The Guition display firmware is a separate client and is not included here.

## Authentication

Each installation needs its own bridge token. Generate matching private app and
display configuration fragments with:

```sh
python tools/generate_token.py
```

The files are written to the ignored `.private/` directory. Merge
`addon-options.fragment.json` into the app's options and
`display-secrets.fragment.yaml` into the display's `secrets.yaml`.
The generator refuses to overwrite existing token files. Keep them private.

The app refuses to start with an empty, short, or known placeholder token.
Protected API endpoints require the token in the `X-Bridge-Token` header;
`/api/health` and the OAuth setup pages remain accessible without it on the LAN.
Use a trusted network; the bridge's built-in listener uses HTTP, so do not expose
port 8099 directly to the internet.

## Development

Python 3.11 or newer:

```sh
python -m venv .venv
# Activate the virtual environment for your shell.
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Tests use a local HTTP server and mock Spotify requests; they do not change
playback or require Spotify credentials.

## License

Own source code and documentation: [MIT](LICENSE).
Dependencies and container components retain their respective licenses; see
[third-party notices](THIRD_PARTY_NOTICES.md). This project is not affiliated
with Spotify.
