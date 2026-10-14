# Changelog

## 0.1.1

- Add the MIT license and third-party notices.
- Remove unpublished GitHub URLs from app/repository metadata.
- Replace the shared default bridge token with a required installation-specific
  token; fail at startup when it is empty, too short or a known placeholder.
- Add a private token generator with matching app/display settings.
- Keep authentication scoped to the application and safely reject non-ASCII
  request tokens.
- Add Git/Docker ignores for credentials and runtime data.
- Share Python dependencies between local tests and the Docker build.
- Document current Spotify OAuth redirect URI requirements.
- Advertise only aarch64 and amd64, supported by the current base image.
