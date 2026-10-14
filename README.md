# Routine Spotify Bridge

A Home Assistant OS app that connects an ESPHome display to Spotify's Web API.
Browse tracks, albums and playlists, control playback, and select Spotify
Connect devices. Spotify credentials stay on the Home Assistant host; the
display receives compact JSON over a token-protected local API.

## Install

Add this repository to the Home Assistant app store:

```text
https://github.com/artur-safonov/routine-spotify-bridge
```

Install **Routine Spotify Bridge**, then follow the
[setup guide](routine_spotify_bridge/DOCS.md) to configure Spotify OAuth and
generate a unique bridge token. Alternatively, copy `routine_spotify_bridge/`
to `/addons` on your Home Assistant OS host and reload the local app list.

The Guition/ESPHome display firmware is a separate client and is not included.

## Status

Version 0.1.1 is an initial source release. Seven local unit tests passed with
Spotify requests mocked. This release's Docker image and installation on Home
Assistant have not yet been validated. Playback requires a Spotify account/API
application eligible to use the playback endpoints and an available Spotify
Connect device.

## Development

See the [app README](routine_spotify_bridge/README.md) for dependencies and tests.
Do not commit private token fragments, app options, Spotify refresh tokens or
display secrets.

## License

Project source and documentation are [MIT licensed](LICENSE).
Dependencies and container components retain their own licenses; see
[third-party notices](routine_spotify_bridge/THIRD_PARTY_NOTICES.md).
This project is not affiliated with Spotify.
