import importlib.util
import secrets
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from aiohttp.test_utils import TestClient, TestServer


MODULE_PATH = Path(__file__).parents[1] / "app" / "main.py"
SPEC = importlib.util.spec_from_file_location("routine_spotify_bridge", MODULE_PATH)
bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bridge)


class BridgeHelpersTest(unittest.TestCase):
    def test_missing_or_placeholder_token_prevents_startup(self):
        for token in ("", "change-me-before-flashing", "changeme-" * 8, "a" * 43, "short", "é" * 43):
            with self.subTest(token=token):
                with self.assertRaises(ValueError):
                    bridge.create_app(token)

    def test_compact_track(self):
        result = bridge.compact_item(
            {
                "id": "track-1",
                "uri": "spotify:track:track-1",
                "type": "track",
                "name": "Test song",
                "artists": [{"name": "Test artist"}],
                "album": {"images": [{"url": "https://example.invalid/cover.jpg"}]},
                "duration_ms": 123000,
            }
        )
        self.assertEqual(result["title"], "Test song")
        self.assertEqual(result["subtitle"], "Test artist")
        self.assertEqual(result["duration_ms"], 123000)


class BridgeHttpTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.token = secrets.token_urlsafe(32)
        self.client = TestClient(
            TestServer(bridge.create_app(self.token)), timeout=bridge.ClientTimeout(total=5)
        )
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()

    async def test_health_is_public(self):
        response = await self.client.get("/api/health")
        self.assertEqual(response.status, 200)
        self.assertTrue((await response.json())["ok"])

    async def test_spotify_api_is_token_protected(self):
        with patch.object(bridge, "spotify_request", new_callable=AsyncMock) as spotify:
            for token in (None, "wrong-token", "é" * 43):
                headers = {} if token is None else {"X-Bridge-Token": token}
                response = await self.client.get("/api/devices", headers=headers)
                self.assertEqual(response.status, 401)
            spotify.assert_not_awaited()

    async def test_configured_token_allows_request(self):
        with patch.object(bridge, "spotify_request", new_callable=AsyncMock) as spotify:
            spotify.return_value = {"devices": []}
            response = await self.client.get("/api/devices", headers={"X-Bridge-Token": self.token})
            self.assertEqual(response.status, 200)
            self.assertEqual(await response.json(), {"items": []})
            spotify.assert_awaited_once_with("GET", "/me/player/devices")

    async def test_another_installations_token_is_rejected(self):
        other = TestClient(
            TestServer(bridge.create_app(secrets.token_urlsafe(32))),
            timeout=bridge.ClientTimeout(total=5),
        )
        await other.start_server()
        try:
            with patch.object(bridge, "spotify_request", new_callable=AsyncMock) as spotify:
                response = await other.get("/api/devices", headers={"X-Bridge-Token": self.token})
                self.assertEqual(response.status, 401)
                spotify.assert_not_awaited()
        finally:
            await other.close()


if __name__ == "__main__":
    unittest.main()
