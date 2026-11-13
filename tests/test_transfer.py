"""Tests for cross-platform API endpoints and universal transfers."""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from tidal_manager.server import app, client, spotify_client


class TestUniversalTransferAPI(unittest.TestCase):
    def setUp(self):
        self.api_client = TestClient(app)

    @patch.object(client, "is_logged_in", return_value=True)
    @patch.object(spotify_client, "is_authenticated", return_value=True)
    def test_universal_transfer_tidal_to_spotify(self, mock_sp_auth, mock_ti_auth):
        # Mock source TIDAL playlist details
        mock_ti_details = {
            "id": "ti_pl_1",
            "name": "Tidal Hits",
            "tracks": [
                {
                    "index": 0,
                    "id": "111",
                    "name": "Song A",
                    "artist": "Artist 1",
                    "isrc": "USRC11111111",
                },
                {
                    "index": 1,
                    "id": "222",
                    "name": "Song B",
                    "artist": "Artist 2",
                    "isrc": "USRC22222222",
                },
            ],
        }

        # Mock target Spotify playlist details
        mock_sp_details = {
            "id": "sp_pl_1",
            "name": "Spotify Destination",
            "tracks": [],
        }

        with patch.object(client, "get_playlist_details", return_value=mock_ti_details), \
             patch.object(spotify_client, "get_playlist_details", return_value=mock_sp_details), \
             patch.object(spotify_client, "search_track") as mock_search, \
             patch.object(spotify_client, "add_tracks", return_value=2) as mock_add:

            mock_search.side_effect = [
                {"id": "sp_tr_1", "uri": "spotify:track:sp_tr_1", "name": "Song A"},
                {"id": "sp_tr_2", "uri": "spotify:track:sp_tr_2", "name": "Song B"},
            ]

            payload = {
                "from_platform": "tidal",
                "to_platform": "spotify",
                "from_playlist_id": "ti_pl_1",
                "to_playlist_id": "sp_pl_1",
                "indices": [0, 1],
                "is_move": False,
            }

            resp = self.api_client.post("/api/transfer/universal", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["transferred_count"], 2)
            self.assertEqual(data["unmatched_count"], 0)
            self.assertTrue(mock_add.called)

    @patch.object(client, "is_logged_in", return_value=True)
    @patch.object(spotify_client, "is_authenticated", return_value=True)
    def test_universal_transfer_spotify_to_tidal(self, mock_sp_auth, mock_ti_auth):
        mock_sp_details = {
            "id": "sp_pl_1",
            "name": "Spotify Source",
            "tracks": [
                {
                    "index": 0,
                    "id": "sp_tr_1",
                    "name": "Song Spotify",
                    "artist": "Artist S",
                    "isrc": "USRC99999999",
                }
            ],
        }

        mock_ti_details = {
            "id": "ti_pl_1",
            "name": "Tidal Destination",
            "tracks": [],
        }

        with patch.object(spotify_client, "get_playlist_details", return_value=mock_sp_details), \
             patch.object(client, "get_playlist_details", return_value=mock_ti_details), \
             patch.object(client, "search_track") as mock_ti_search, \
             patch.object(client, "add_tracks", return_value=1) as mock_ti_add:

            mock_ti_search.return_value = {"id": "ti_tr_1", "name": "Song Spotify"}

            payload = {
                "from_platform": "spotify",
                "to_platform": "tidal",
                "from_playlist_id": "sp_pl_1",
                "to_playlist_id": "ti_pl_1",
                "indices": [0],
                "is_move": False,
            }

            resp = self.api_client.post("/api/transfer/universal", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["transferred_count"], 1)
            self.assertTrue(mock_ti_add.called)

    @patch.object(client, "is_logged_in", return_value=True)
    def test_universal_transfer_tidal_to_tidal_copy(self, mock_ti_auth):
        mock_ti_src = {
            "id": "ti_src",
            "name": "Tidal Source",
            "tracks": [{"index": 0, "id": "111", "name": "Song 1", "artist": "A1"}],
        }
        mock_ti_dst = {
            "id": "ti_dst",
            "name": "Tidal Dst",
            "tracks": [],
        }

        with patch.object(client, "get_playlist_details", side_effect=[mock_ti_src, mock_ti_dst]), \
             patch.object(client, "copy_tracks", return_value={"copied_count": 1}) as mock_copy:

            payload = {
                "from_platform": "tidal",
                "to_platform": "tidal",
                "from_playlist_id": "ti_src",
                "to_playlist_id": "ti_dst",
                "indices": [0],
                "is_move": False,
            }
            resp = self.api_client.post("/api/transfer/universal", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["transferred_count"], 1)
            mock_copy.assert_called_once_with(
                from_playlist_id="ti_src",
                to_playlist_id="ti_dst",
                indices=[0],
            )

    @patch.object(client, "is_logged_in", return_value=True)
    def test_universal_transfer_tidal_to_tidal_move(self, mock_ti_auth):
        mock_ti_src = {
            "id": "ti_src",
            "name": "Tidal Source",
            "tracks": [{"index": 0, "id": "111", "name": "Song 1", "artist": "A1"}],
        }
        mock_ti_dst = {
            "id": "ti_dst",
            "name": "Tidal Dst",
            "tracks": [],
        }

        with patch.object(client, "get_playlist_details", side_effect=[mock_ti_src, mock_ti_dst]), \
             patch.object(client, "move_tracks", return_value={"moved_count": 1}) as mock_move:

            payload = {
                "from_platform": "tidal",
                "to_platform": "tidal",
                "from_playlist_id": "ti_src",
                "to_playlist_id": "ti_dst",
                "indices": [0],
                "is_move": True,
            }
            resp = self.api_client.post("/api/transfer/universal", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["transferred_count"], 1)
            mock_move.assert_called_once_with(
                from_playlist_id="ti_src",
                to_playlist_id="ti_dst",
                indices=[0],
            )


if __name__ == "__main__":
    unittest.main()
