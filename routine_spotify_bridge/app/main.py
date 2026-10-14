import asyncio
import base64
import json
import logging
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientSession, ClientTimeout, web


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("routine_spotify_bridge")

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://homeassistant.local:8099").rstrip("/")
BRIDGE_TOKEN = os.environ.get("BRIDGE_TOKEN", "")
BRIDGE_TOKEN_KEY = web.AppKey("bridge_token", bytes)
MARKET = os.environ.get("SPOTIFY_MARKET", "UA")
TOKEN_PATH = Path("/data/spotify_token.json")
REDIRECT_URI = f"{PUBLIC_BASE_URL}/callback"
SCOPES = " ".join(
    [
        "user-read-playback-state",
        "user-modify-playback-state",
        "user-read-currently-playing",
        "user-read-recently-played",
        "user-library-read",
        "playlist-read-private",
        "playlist-read-collaborative",
    ]
)

SPOTIFY_API = "https://api.spotify.com/v1"
SPOTIFY_ACCOUNTS = "https://accounts.spotify.com"
HTTP_TIMEOUT = ClientTimeout(total=18)
oauth_state = ""
token_lock = asyncio.Lock()


def load_token() -> dict[str, Any]:
    if not TOKEN_PATH.exists():
        return {}
    try:
        return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        LOG.exception("Unable to read saved Spotify token")
        return {}


def save_token(token: dict[str, Any]) -> None:
    token["expires_at"] = int(time.time()) + int(token.get("expires_in", 3600)) - 60
    TOKEN_PATH.write_text(json.dumps(token, indent=2), encoding="utf-8")


async def exchange_token(payload: dict[str, str]) -> dict[str, Any]:
    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    async with ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.post(f"{SPOTIFY_ACCOUNTS}/api/token", data=payload, headers=headers) as response:
            body = await response.json(content_type=None)
            if response.status >= 400:
                raise web.HTTPBadGateway(text=json.dumps(body), content_type="application/json")
            return body


async def access_token() -> str:
    async with token_lock:
        token = load_token()
        if not token:
            raise web.HTTPUnauthorized(text='{"error":"spotify_not_authorized"}', content_type="application/json")
        if int(token.get("expires_at", 0)) > int(time.time()):
            return str(token["access_token"])
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise web.HTTPUnauthorized(text='{"error":"spotify_refresh_token_missing"}', content_type="application/json")
        refreshed = await exchange_token({"grant_type": "refresh_token", "refresh_token": refresh_token})
        refreshed["refresh_token"] = refreshed.get("refresh_token", refresh_token)
        save_token(refreshed)
        return str(refreshed["access_token"])


@web.middleware
async def api_auth(request: web.Request, handler):
    if request.path.startswith("/api/") and request.path != "/api/health":
        supplied = request.headers.get("X-Bridge-Token", "")
        if not secrets.compare_digest(supplied.encode("utf-8"), request.app[BRIDGE_TOKEN_KEY]):
            raise web.HTTPUnauthorized(text='{"error":"invalid_bridge_token"}', content_type="application/json")
    return await handler(request)


async def spotify_request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    token = await access_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.request(
            method,
            f"{SPOTIFY_API}{path}",
            params=params,
            json=payload,
            headers=headers,
        ) as response:
            text = await response.text()
            if response.status == 204:
                return {"ok": True}
            if response.status >= 400:
                LOG.warning("Spotify %s %s returned %s: %s", method, path, response.status, text)
                raise web.HTTPBadGateway(
                    text=json.dumps({"error": "spotify_api_error", "status": response.status, "detail": text}),
                    content_type="application/json",
                )
            return json.loads(text) if text else {"ok": True}


def image_url(item: dict[str, Any]) -> str:
    images = item.get("images") or item.get("album", {}).get("images") or []
    return images[0].get("url", "") if images else ""


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    item_type = item.get("type", "")
    artists = item.get("artists") or item.get("album", {}).get("artists") or []
    subtitle = ", ".join(artist.get("name", "") for artist in artists if artist.get("name"))
    if not subtitle:
        subtitle = item.get("owner", {}).get("display_name") or item.get("description", "")
    return {
        "id": item.get("id", ""),
        "uri": item.get("uri", ""),
        "type": item_type,
        "title": item.get("name", ""),
        "subtitle": subtitle,
        "image": image_url(item),
        "duration_ms": item.get("duration_ms", 0),
    }


def unwrap_items(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    container = data.get(key, {})
    items = container.get("items", []) if isinstance(container, dict) else []
    normalized = []
    for entry in items:
        item = entry.get("track", entry) if isinstance(entry, dict) else {}
        if item:
            normalized.append(compact_item(item))
    return normalized


async def index(_: web.Request) -> web.Response:
    authorized = bool(load_token())
    status = "Connected" if authorized else "Not connected"
    return web.Response(
        text=f"""<!doctype html><html><head><meta name=viewport content='width=device-width'>
<style>body{{font:16px system-ui;background:#121212;color:#fff;max-width:680px;margin:48px auto;padding:20px}}a{{display:inline-block;background:#1ed760;color:#000;padding:14px 22px;border-radius:999px;text-decoration:none;font-weight:700}}code{{color:#1ed760}}</style></head>
<body><h1>Routine Spotify Bridge</h1><p>Status: <strong>{status}</strong></p>
<p>Redirect URI configured in Spotify must be <code>{REDIRECT_URI}</code>.</p>
<a href='/auth/login'>Connect Spotify</a></body></html>""",
        content_type="text/html",
    )


async def auth_login(_: web.Request) -> web.Response:
    global oauth_state
    if not CLIENT_ID or not CLIENT_SECRET:
        raise web.HTTPServiceUnavailable(text="Set client_id and client_secret in the app options first")
    oauth_state = secrets.token_urlsafe(24)
    query = urlencode(
        {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "state": oauth_state,
            "show_dialog": "true",
        }
    )
    raise web.HTTPFound(f"{SPOTIFY_ACCOUNTS}/authorize?{query}")


async def auth_callback(request: web.Request) -> web.Response:
    if request.query.get("state") != oauth_state or not request.query.get("code"):
        raise web.HTTPBadRequest(text="Invalid OAuth callback")
    token = await exchange_token(
        {
            "grant_type": "authorization_code",
            "code": request.query["code"],
            "redirect_uri": REDIRECT_URI,
        }
    )
    save_token(token)
    raise web.HTTPFound("/")


async def health(_: web.Request) -> web.Response:
    return web.json_response({"ok": True, "authorized": bool(load_token())})


async def player(_: web.Request) -> web.Response:
    data = await spotify_request("GET", "/me/player")
    if data.get("ok"):
        return web.json_response({"playing": False, "item": None})
    item = data.get("item") or {}
    return web.json_response(
        {
            "playing": bool(data.get("is_playing")),
            "progress_ms": data.get("progress_ms", 0),
            "shuffle": data.get("shuffle_state", False),
            "repeat": data.get("repeat_state", "off"),
            "device": data.get("device", {}),
            "item": compact_item(item) if item else None,
        }
    )


async def devices(_: web.Request) -> web.Response:
    data = await spotify_request("GET", "/me/player/devices")
    result = [
        {
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "type": item.get("type", ""),
            "active": item.get("is_active", False),
            "volume": item.get("volume_percent"),
        }
        for item in data.get("devices", [])
    ]
    return web.json_response({"items": result})


async def search(request: web.Request) -> web.Response:
    query = request.query.get("q", "").strip()
    if not query:
        return web.json_response({"items": []})
    kinds = request.query.get("types", "track,album,playlist,artist")
    data = await spotify_request(
        "GET",
        "/search",
        params={"q": query, "type": kinds, "limit": 8, "market": MARKET},
    )
    result: list[dict[str, Any]] = []
    for key in ("tracks", "albums", "playlists", "artists"):
        result.extend(unwrap_items(data, key))
    return web.json_response({"items": result[:24]})


async def library(_: web.Request) -> web.Response:
    playlists, tracks, recent = await asyncio.gather(
        spotify_request("GET", "/me/playlists", params={"limit": 10}),
        spotify_request("GET", "/me/tracks", params={"limit": 10, "market": MARKET}),
        spotify_request("GET", "/me/player/recently-played", params={"limit": 10}),
    )
    return web.json_response(
        {
            "playlists": [compact_item(x) for x in playlists.get("items", [])],
            "liked": [compact_item(x.get("track", {})) for x in tracks.get("items", []) if x.get("track")],
            "recent": [compact_item(x.get("track", {})) for x in recent.get("items", []) if x.get("track")],
        }
    )


async def json_body(request: web.Request) -> dict[str, Any]:
    try:
        return await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest):
        return {}


async def play(request: web.Request) -> web.Response:
    body = await json_body(request)
    uri = str(body.get("uri", ""))
    device_id = body.get("device_id")
    payload: dict[str, Any] = {}
    if uri.startswith(("spotify:track:", "spotify:episode:")):
        payload["uris"] = [uri]
    elif uri:
        payload["context_uri"] = uri
    params = {"device_id": device_id} if device_id else None
    return web.json_response(await spotify_request("PUT", "/me/player/play", params=params, payload=payload))


async def transfer(request: web.Request) -> web.Response:
    body = await json_body(request)
    device_id = str(body.get("device_id", ""))
    if not device_id:
        raise web.HTTPBadRequest(text='{"error":"device_id_required"}', content_type="application/json")
    return web.json_response(
        await spotify_request("PUT", "/me/player", payload={"device_ids": [device_id], "play": bool(body.get("play", False))})
    )


async def simple_player_action(request: web.Request) -> web.Response:
    action = request.match_info["action"]
    mapping = {"pause": ("PUT", "/me/player/pause"), "next": ("POST", "/me/player/next"), "previous": ("POST", "/me/player/previous")}
    if action not in mapping:
        raise web.HTTPNotFound()
    method, path = mapping[action]
    return web.json_response(await spotify_request(method, path))


async def controls(request: web.Request) -> web.Response:
    action = request.match_info["action"]
    body = await json_body(request)
    if action == "volume":
        return web.json_response(await spotify_request("PUT", "/me/player/volume", params={"volume_percent": int(body.get("value", 50))}))
    if action == "seek":
        return web.json_response(await spotify_request("PUT", "/me/player/seek", params={"position_ms": int(body.get("value", 0))}))
    if action == "shuffle":
        return web.json_response(await spotify_request("PUT", "/me/player/shuffle", params={"state": str(bool(body.get("value"))).lower()}))
    if action == "repeat":
        return web.json_response(await spotify_request("PUT", "/me/player/repeat", params={"state": body.get("value", "off")}))
    if action == "queue":
        return web.json_response(await spotify_request("POST", "/me/player/queue", params={"uri": body.get("uri", "")}))
    raise web.HTTPNotFound()


def validate_bridge_token(token: str) -> bytes:
    """Fail before serving requests when the installation has no usable secret."""
    if (
        not re.fullmatch(r"[A-Za-z0-9_-]{32,}", token)
        or len(set(token)) < 2
        or token.lower().startswith(("change-me", "changeme", "replace-me", "your-token"))
    ):
        raise ValueError(
            "Set bridge_token to a unique random token of at least 32 URL-safe "
            "characters. Generate one with tools/generate_token.py and put the "
            "same value in the display's spotify_bridge_token secret."
        )
    return token.encode("ascii")


def create_app(bridge_token: str | None = None) -> web.Application:
    token = validate_bridge_token(BRIDGE_TOKEN if bridge_token is None else bridge_token)
    app = web.Application(middlewares=[api_auth])
    app[BRIDGE_TOKEN_KEY] = token
    app.add_routes(
        [
            web.get("/", index),
            web.get("/auth/login", auth_login),
            web.get("/callback", auth_callback),
            web.get("/api/health", health),
            web.get("/api/player", player),
            web.get("/api/devices", devices),
            web.get("/api/search", search),
            web.get("/api/library", library),
            web.post("/api/play", play),
            web.post("/api/transfer", transfer),
            web.post("/api/player/{action:pause|next|previous}", simple_player_action),
            web.post("/api/control/{action:volume|seek|shuffle|repeat|queue}", controls),
        ]
    )
    return app


if __name__ == "__main__":
    try:
        application = create_app()
    except ValueError as error:
        LOG.error("%s", error)
        raise SystemExit(1) from None
    web.run_app(application, host="0.0.0.0", port=8099)
