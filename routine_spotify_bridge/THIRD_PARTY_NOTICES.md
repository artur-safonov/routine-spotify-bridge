# Third-party components

Routine Spotify Bridge's own source code and documentation are licensed under
the MIT License in `LICENSE`. This license does not relicense dependencies,
container images, Spotify services, or the separate display firmware.

- **aiohttp** — Apache-2.0; installed as a dependency, not vendored here.
  Source and license: <https://github.com/aio-libs/aiohttp>.
- **Home Assistant base image** — obtained from
  `ghcr.io/home-assistant/base`. Its components retain their own licenses.
  Source and notices: <https://github.com/home-assistant/docker-base>.
- **Python and Alpine packages** — installed in the container and retain their
  respective licenses; dependency copyright notices must be retained when
  distributing a built image.

Spotify names are used to identify the service integrated by this project.
Spotify's Web API is subject to Spotify's developer terms; this project's MIT
license grants no rights to Spotify content, branding, accounts, or services.

The Guition/ESPHome display is a separate client and is not included in this
package. Preserve its upstream license when distributing its firmware.
