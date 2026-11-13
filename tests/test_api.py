"""Integration and endpoint tests for FastAPI server."""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from tidal_manager.server import app, client
from tests.test_client import DummyPlaylist, DummyTrack


class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        self.api_client = TestClient(app)

    def test_auth_status_not_logged_in(self):
        with patch.object(client, "is_logged_in", return_value=False):
            res = self.api_client.get("/api/auth/status")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertFalse(data["logged_in"])

    def test_auth_status_logged_in(self):
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "get_user_info", return_value={"username": "audiophile", "country_code": "DE"}):
            res = self.api_client.get("/api/auth/status")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["logged_in"])
            self.assertEqual(data["user"]["username"], "audiophile")

    def test_unauthorized_access(self):
        with patch.object(client, "is_logged_in", return_value=False):
            res = self.api_client.get("/api/playlists")
            self.assertEqual(res.status_code, 401)

    def test_list_playlists(self):
        sample_playlists = [
            {"id": "p1", "name": "Chill", "num_tracks": 10, "duration": 1800, "duration_formatted": "30 min"}
        ]
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "list_playlists", return_value=sample_playlists):
            res = self.api_client.get("/api/playlists")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["name"], "Chill")

    def test_create_playlist(self):
        created = {"id": "new-1", "name": "Deep Focus", "num_tracks": 0, "duration": 0}
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "create_playlist", return_value=created):
            res = self.api_client.post("/api/playlists", json={"name": "Deep Focus", "description": "Work music"})
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["name"], "Deep Focus")

    def test_rename_playlist(self):
        renamed = {"id": "p1", "name": "Super Chill", "num_tracks": 10}
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "rename_playlist", return_value=renamed):
            res = self.api_client.put("/api/playlists/p1", json={"name": "Super Chill"})
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["name"], "Super Chill")

    def test_copy_tracks(self):
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "copy_tracks", return_value={"success": True, "copied_count": 2, "to_playlist": "Dest"}):
            res = self.api_client.post(
                "/api/playlists/copy",
                json={"from_id": "src", "to_id": "dst", "indices": [0, 1]},
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["copied_count"], 2)

    def test_move_tracks(self):
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "move_tracks", return_value={"success": True, "moved_count": 3, "to_playlist": "Dest"}):
            res = self.api_client.post(
                "/api/playlists/move",
                json={"from_id": "src", "to_id": "dst", "indices": [0, 1, 2]},
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["moved_count"], 3)

    def test_split_playlist_endpoint(self):
        split_result = {
            "needed_split": True,
            "success": True,
            "base_name": "Mega Playlist",
            "total_playlists": 2,
            "max_per_playlist": 99,
            "message": "Split into 2 playlists",
            "playlists": [
                {"part": 1, "id": "p1", "name": "Mega Playlist 1", "tracks_count": 99, "is_original": True},
                {"part": 2, "id": "p2", "name": "Mega Playlist 2", "tracks_count": 20, "is_original": False},
            ],
        }
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "split_playlist", return_value=split_result):
            res = self.api_client.post(
                "/api/playlists/p1/split",
                json={"max_tracks": 99, "rename_original": True},
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["needed_split"])
            self.assertEqual(data["total_playlists"], 2)

    def test_serve_frontend(self):
        res = self.api_client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("TIDAL", res.text)
        self.assertIn("Playlist Manager", res.text)


    def test_duplicates_endpoint(self):
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "find_duplicates", return_value={"duplicate_count": 1, "duplicate_indices": [2]}):
            res = self.api_client.get("/api/playlists/p1/duplicates")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["duplicate_count"], 1)

    def test_export_endpoint(self):
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "export_playlist", return_value=('{"test": 1}', "application/json", "test.json")):
            res = self.api_client.get("/api/playlists/p1/export?format=json")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.headers["content-type"], "application/json")

    def test_search_endpoint(self):
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "search_catalog", return_value=[{"id": "123", "name": "Found Track"}]):
            res = self.api_client.get("/api/search?q=test")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(res.json()), 1)


    def test_reorder_track_endpoint(self):
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "reorder_track", return_value=True):
            res = self.api_client.post(
                "/api/playlists/p1/reorder",
                json={"from_index": 0, "to_index": 3},
            )
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.json()["success"])

    def test_match_local_endpoint(self):
        from tidal_manager.local_matcher import LocalAudioFile

        mock_tracks = [
            {"index": 0, "id": "t1", "name": "Get Lucky", "artist": "Daft Punk", "isrc": "USAT21300307"},
            {"index": 1, "id": "t2", "name": "Starboy", "artist": "The Weeknd", "isrc": ""},
        ]
        mock_local = [
            LocalAudioFile(
                path="/music/Daft Punk - Get Lucky.mp3",
                filename="Daft Punk - Get Lucky.mp3",
                title="Get Lucky",
                artist="Daft Punk",
                album="Random Access Memories",
                isrc="USAT21300307",
            )
        ]

        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "get_playlist_details", return_value={"playlist": {"id": "p1"}, "tracks": mock_tracks}), \
             patch("tidal_manager.server.scan_local_directory", return_value=mock_local):
            # Test platform-specific route
            res = self.api_client.post(
                "/api/tidal/playlists/p1/match-local",
                json={"directory_path": "/mock/music"},
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["matched_count"], 1)
            self.assertEqual(data["matches"][0]["track_name"], "Get Lucky")

            # Test legacy route
            res_legacy = self.api_client.post(
                "/api/playlists/p1/match-local",
                json={"directory_path": "/mock/music"},
            )
            self.assertEqual(res_legacy.status_code, 200)
            self.assertEqual(res_legacy.json()["matched_count"], 1)

    def test_remove_local_endpoint(self):
        with patch.object(client, "is_logged_in", return_value=True), \
             patch.object(client, "remove_tracks_by_indices", return_value=2):
            res = self.api_client.post(
                "/api/tidal/playlists/p1/remove-local",
                json={"indices": [0, 3]},
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["removed_count"], 2)

            # Test legacy route
            res_legacy = self.api_client.post(
                "/api/playlists/p1/remove-local",
                json={"indices": [0, 3]},
            )
            self.assertEqual(res_legacy.status_code, 200)
            self.assertEqual(res_legacy.json()["removed_count"], 2)


if __name__ == "__main__":
    unittest.main()
