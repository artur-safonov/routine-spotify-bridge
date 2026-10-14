FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
  io.hass.name="Routine Spotify Bridge" \
  io.hass.description="Spotify Web API bridge for an ESPHome display" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

COPY requirements.txt /tmp/requirements.txt
RUN apk add --no-cache python3 py3-pip \
    && python3 -m pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

COPY app /app
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
