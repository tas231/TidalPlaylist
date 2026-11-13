"""Unit tests for local directory scanning and playlist matching."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from tidal_manager.local_matcher import (
    LocalAudioFile,
    extract_metadata_from_file,
    match_playlist_against_local,
    normalize_string,
    pick_directory_dialog,
    pick_directory_macos,
    scan_local_directory,
)
from tidal_manager.server import app


class TestLocalMatcher(unittest.TestCase):

    def test_normalize_string(self):
        self.assertEqual(normalize_string("Bohemian Rhapsody (2011 Remaster)"), "bohemian rhapsody")
        self.assertEqual(normalize_string("Get Lucky [feat. Pharrell Williams]"), "get lucky")
        self.assertEqual(normalize_string("Hotel California - Live"), "hotel california")
        self.assertEqual(normalize_string("Daft Punk feat. Nile Rodgers"), "daft punk")
        self.assertEqual(normalize_string("Café del Mar"), "cafe del mar")

    def test_match_by_isrc(self):
        playlist_tracks = [
            {"index": 0, "id": "1", "name": "Song A", "artist": "Artist A", "isrc": "USRC12345678"},
            {"index": 1, "id": "2", "name": "Song B", "artist": "Artist B", "isrc": "USRC99999999"},
        ]
        local_files = [
            LocalAudioFile(
                path="/music/song_a.flac",
                filename="song_a.flac",
                title="Song A",
                artist="Artist A",
                album="Album A",
                isrc="USRC12345678",
            )
        ]
        res = match_playlist_against_local(playlist_tracks, local_files)
        self.assertEqual(res["matched_count"], 1)
        self.assertEqual(res["matches"][0]["index"], 0)
        self.assertEqual(res["matches"][0]["match_type"], "isrc")

    def test_match_by_title_artist_normalization(self):
        playlist_tracks = [
            {"index": 0, "id": "1", "name": "Bohemian Rhapsody (2011 Remaster)", "artist": "Queen"},
            {"index": 1, "id": "2", "name": "Another One Bites The Dust", "artist": "Queen"},
        ]
        local_files = [
            LocalAudioFile(
                path="/music/queen/bohemian_rhapsody.mp3",
                filename="bohemian_rhapsody.mp3",
                title="Bohemian Rhapsody",
                artist="Queen",
                album="A Night at the Opera",
            )
        ]
        res = match_playlist_against_local(playlist_tracks, local_files)
        self.assertEqual(res["matched_count"], 1)
        self.assertEqual(res["matches"][0]["index"], 0)
        self.assertEqual(res["matches"][0]["match_type"], "title_artist")

    def test_filename_fallback_extraction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "Queen - Bohemian Rhapsody.mp3"
            file_path.write_text("dummy audio content")

            extracted = extract_metadata_from_file(file_path)
            self.assertEqual(extracted.artist, "Queen")
            self.assertEqual(extracted.title, "Bohemian Rhapsody")

    def test_scan_local_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "Artist A").mkdir()
            (p / "Artist A" / "01 - Track One.mp3").write_text("mp3")
            (p / "Artist A" / "02 - Track Two.flac").write_text("flac")
            (p / "notes.txt").write_text("text")  # non-audio

            scanned = scan_local_directory(p)
            self.assertEqual(len(scanned), 2)
            titles = [s.title for s in scanned]
            self.assertIn("Track One", titles)
            self.assertIn("Track Two", titles)

    @patch("subprocess.run")
    def test_pick_directory_macos_success(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "/Users/test/Music/Tidal/\n"
        mock_run.return_value = mock_proc

        result = pick_directory_macos("~/Music")
        self.assertEqual(result, "/Users/test/Music/Tidal")

    @patch("subprocess.run")
    def test_pick_directory_macos_canceled(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "User canceled (-128)"
        mock_run.return_value = mock_proc

        result = pick_directory_macos("~/Music")
        self.assertIsNone(result)

    @patch("tidal_manager.server.pick_directory_dialog", return_value="/Users/test/Music/Selected")
    def test_api_browse_folder_selected(self, mock_pick):
        client = TestClient(app)
        res = client.post("/api/utils/browse-folder", json={"initial_dir": "~/Music"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["path"], "/Users/test/Music/Selected")
        self.assertFalse(data["canceled"])

    @patch("tidal_manager.server.pick_directory_dialog", return_value=None)
    def test_api_browse_folder_canceled(self, mock_pick):
        client = TestClient(app)
        res = client.post("/api/utils/browse-folder", json={})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIsNone(data["path"])
        self.assertTrue(data["canceled"])


if __name__ == "__main__":
    unittest.main()
