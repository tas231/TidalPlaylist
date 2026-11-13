"""Unit tests for SpotifyClient wrapper."""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tidal_manager.spotify_client import SpotifyAuthError, SpotifyClient, SpotifyError


class TestSpotifyClient(unittest.TestCase):
    def setUp(self):
        self.test_session_path = Path("tests/test_spotify_session.json")
        if self.test_session_path.exists():
            self.test_session_path.unlink()
        self.client = SpotifyClient(session_file=self.test_session_path)

    def tearDown(self):
        if self.test_session_path.exists():
            self.test_session_path.unlink()

    def test_config_and_session_save(self):
        self.assertFalse(self.client.is_configured())
        self.client.set_config("test_client_id", "test_client_secret")
        self.assertTrue(self.client.is_configured())
        self.assertEqual(self.client.client_id, "test_client_id")
        self.assertEqual(self.client.client_secret, "test_client_secret")

        # Reload from file
        reloaded = SpotifyClient(session_file=self.test_session_path)
        self.assertTrue(reloaded.is_configured())
        self.assertEqual(reloaded.client_id, "test_client_id")

    def test_get_auth_url(self):
        self.client.set_config("cid_123", "sec_456")
        url = self.client.get_auth_url()
        self.assertIn("accounts.spotify.com/authorize", url)
        self.assertIn("client_id=cid_123", url)
        self.assertIn("response_type=code", url)

    @patch("requests.post")
    def test_exchange_code(self, mock_post):
        self.client.set_config("cid_123", "sec_456")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "acc_tok_999",
            "refresh_token": "ref_tok_888",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_resp

        data = self.client.exchange_code("sample_auth_code")
        self.assertEqual(data["access_token"], "acc_tok_999")
        self.assertEqual(self.client.access_token, "acc_tok_999")
        self.assertEqual(self.client.refresh_token, "ref_tok_888")
        self.assertTrue(self.client.is_authenticated())

    @patch.object(SpotifyClient, "_request")
    def test_get_current_user(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "id": "spot_user_1",
            "display_name": "Test Spotifyer",
            "email": "test@spotify.com",
            "country": "DE",
            "images": [{"url": "https://img.spotify.com/avatar.jpg"}],
        }
        mock_req.return_value = mock_resp

        user = self.client.get_current_user()
        self.assertEqual(user["id"], "spot_user_1")
        self.assertEqual(user["username"], "Test Spotifyer")
        self.assertEqual(user["country_code"], "DE")

    @patch.object(SpotifyClient, "_request")
    def test_list_playlists(self, mock_req):
        self.client._user_cache = {"id": "spot_user_1"}
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [
                {
                    "id": "sp_pl_1",
                    "name": "My Spotify Jams",
                    "description": "Chill music",
                    "tracks": {"total": 42},
                    "owner": {"id": "spot_user_1", "display_name": "Test Spotifyer"},
                    "images": [{"url": "https://cover.jpg"}],
                    "public": True,
                }
            ],
            "total": 1,
        }
        mock_req.return_value = mock_resp

        playlists = self.client.list_playlists()
        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0]["name"], "My Spotify Jams")
        self.assertEqual(playlists[0]["num_tracks"], 42)
        self.assertTrue(playlists[0]["is_user_playlist"])

    @patch.object(SpotifyClient, "_request")
    def test_search_track_by_isrc(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "tracks": {
                "items": [
                    {
                        "id": "tr_1",
                        "name": "Nightcall",
                        "artists": [{"name": "Kavinsky"}],
                        "album": {"name": "Nightcall", "images": []},
                        "duration_ms": 258000,
                        "explicit": False,
                        "external_ids": {"isrc": "FRS710900410"},
                        "uri": "spotify:track:tr_1",
                    }
                ]
            }
        }
        mock_req.return_value = mock_resp

        res = self.client.search_track(isrc="FRS710900410", title="Nightcall", artist="Kavinsky")
        self.assertIsNotNone(res)
        self.assertEqual(res["id"], "tr_1")
        self.assertEqual(res["match_type"], "isrc")
        self.assertEqual(res["name"], "Nightcall")


if __name__ == "__main__":
    unittest.main()
