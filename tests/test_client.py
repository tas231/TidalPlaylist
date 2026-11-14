"""Unit tests for TidalClient and playlist splitting logic."""

import json
import unittest
from unittest.mock import MagicMock, patch

from tidal_manager.client import TidalClient, TidalManagerError


class DummyTrack:
    def __init__(self, track_id: int, name: str, artist: str = "Artist", duration: int = 180):
        self.id = track_id
        self.name = name
        self.artist = MagicMock(name=artist)
        self.artist.name = artist
        self.album = MagicMock()
        self.album.name = "Album"
        self.album.image.return_value = "https://example.com/cover.jpg"
        self.duration = duration
        self.explicit = False
        self.audio_quality = "LOSSLESS"


class DummyPlaylist:
    def __init__(self, pl_id: str, name: str, tracks: list, description: str = ""):
        self.id = pl_id
        self.name = name
        self.description = description
        self._tracks = list(tracks)
        self.num_tracks = len(tracks)
        self.duration = sum(t.duration for t in tracks)
        self.public = False
        self.last_updated = "2026-01-01"
        self.created = "2026-01-01"

    def tracks_paginated(self):
        return list(self._tracks)

    def tracks(self, limit=None, offset=0):
        return list(self._tracks)

    def image(self, dimensions=320):
        return "https://example.com/playlist.jpg"

    def edit(self, title=None, description=None):
        if title:
            self.name = title
        if description is not None:
            self.description = description
        return True

    def delete(self):
        return True

    def add(self, media_ids, allow_duplicates=False):
        for mid in media_ids:
            self._tracks.append(DummyTrack(int(mid), f"Track {mid}"))
        self.num_tracks = len(self._tracks)
        return [int(m) for m in media_ids]

    def remove_by_indices(self, indices):
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self._tracks):
                del self._tracks[idx]
        self.num_tracks = len(self._tracks)
        return True

    def remove_by_index(self, idx):
        return self.remove_by_indices([idx])


class TestTidalClient(unittest.TestCase):
    def setUp(self):
        self.client = TidalClient()
        self.client.session = MagicMock()
        self.client.is_logged_in = MagicMock(return_value=True)

    def test_split_playlist_not_needed(self):
        tracks = [DummyTrack(i, f"Track {i}") for i in range(50)]
        dummy_pl = DummyPlaylist("pl-123", "Short Mix", tracks)
        self.client.get_playlist_obj = MagicMock(return_value=dummy_pl)

        res = self.client.split_playlist("pl-123", max_tracks=99)
        self.assertFalse(res["needed_split"])
        self.assertEqual(res["total_tracks"], 50)
        self.assertEqual(len(res["playlists"]), 1)

    def test_split_playlist_needed_250_tracks(self):
        # 250 tracks should split into 3 playlists: 99, 99, 52
        tracks = [DummyTrack(i, f"Track {i}") for i in range(250)]
        dummy_pl = DummyPlaylist("pl-orig", "Road Trip", tracks)

        created_playlists = {}

        def mock_get_playlist_obj(pl_id):
            if pl_id == "pl-orig":
                return dummy_pl
            return created_playlists[pl_id]

        def mock_create_playlist(title, description=""):
            new_id = f"pl-{title.replace(' ', '-').lower()}"
            new_pl = DummyPlaylist(new_id, title, [], description)
            created_playlists[new_id] = new_pl
            return self.client._format_playlist(new_pl)

        self.client.get_playlist_obj = mock_get_playlist_obj
        self.client.create_playlist = mock_create_playlist

        res = self.client.split_playlist("pl-orig", max_tracks=99, rename_original=True)

        self.assertTrue(res["needed_split"])
        self.assertTrue(res["success"])
        self.assertEqual(res["total_playlists"], 3)
        self.assertEqual(res["base_name"], "Road Trip")

        # Check part 1 (original)
        self.assertEqual(dummy_pl.name, "Road Trip 1")
        self.assertEqual(len(dummy_pl._tracks), 99)

        # Check part 2
        p2 = created_playlists["pl-road-trip-2"]
        self.assertEqual(p2.name, "Road Trip 2")
        self.assertEqual(len(p2._tracks), 99)

        # Check part 3
        p3 = created_playlists["pl-road-trip-3"]
        self.assertEqual(p3.name, "Road Trip 3")
        self.assertEqual(len(p3._tracks), 52)

        # Sum of all tracks must equal 250
        total_remaining = len(dummy_pl._tracks) + len(p2._tracks) + len(p3._tracks)
        self.assertEqual(total_remaining, 250)

    def test_copy_tracks(self):
        tracks_src = [DummyTrack(1, "Track 1"), DummyTrack(2, "Track 2"), DummyTrack(3, "Track 3")]
        src_pl = DummyPlaylist("src", "Source", tracks_src)
        dst_pl = DummyPlaylist("dst", "Dest", [])

        self.client.get_playlist_obj = MagicMock(side_effect=lambda x: src_pl if x == "src" else dst_pl)

        res = self.client.copy_tracks("src", "dst", indices=[0, 2])
        self.assertTrue(res["success"])
        self.assertEqual(res["copied_count"], 2)
        # Verify dest playlist has 2 tracks
        self.assertEqual(len(dst_pl._tracks), 2)
        # Verify source still has all 3 tracks
        self.assertEqual(len(src_pl._tracks), 3)

    def test_move_tracks(self):
        tracks_src = [DummyTrack(1, "Track 1"), DummyTrack(2, "Track 2"), DummyTrack(3, "Track 3")]
        src_pl = DummyPlaylist("src", "Source", tracks_src)
        dst_pl = DummyPlaylist("dst", "Dest", [])

        self.client.get_playlist_obj = MagicMock(side_effect=lambda x: src_pl if x == "src" else dst_pl)

        res = self.client.move_tracks("src", "dst", indices=[1])
        self.assertTrue(res["success"])
        self.assertEqual(res["moved_count"], 1)
        # Dest has 1 track
        self.assertEqual(len(dst_pl._tracks), 1)
        self.assertEqual(dst_pl._tracks[0].id, 2)
        # Source has 2 tracks left (Track 1 and Track 3)
        self.assertEqual(len(src_pl._tracks), 2)
        self.assertEqual([t.id for t in src_pl._tracks], [1, 3])


    def test_split_boundary_99_tracks(self):
        # 99 tracks -> no split needed
        tracks = [DummyTrack(i, f"Track {i}") for i in range(99)]
        dummy_pl = DummyPlaylist("pl-99", "Exact 99", tracks)
        self.client.get_playlist_obj = MagicMock(return_value=dummy_pl)

        res = self.client.split_playlist("pl-99", max_tracks=99)
        self.assertFalse(res["needed_split"])
        self.assertEqual(res["total_tracks"], 99)

    def test_split_boundary_100_tracks(self):
        # 100 tracks -> splits into 2: 99 and 1
        tracks = [DummyTrack(i, f"Track {i}") for i in range(100)]
        dummy_pl = DummyPlaylist("pl-100", "Century Mix 1", tracks)

        created = {}
        def mock_create(title, description=""):
            new_id = f"id-{title}"
            p = DummyPlaylist(new_id, title, [], description)
            created[new_id] = p
            return self.client._format_playlist(p)

        self.client.get_playlist_obj = lambda pl_id: dummy_pl if pl_id == "pl-100" else created[pl_id]
        self.client.create_playlist = mock_create

        res = self.client.split_playlist("pl-100", max_tracks=99, rename_original=True)
        self.assertTrue(res["needed_split"])
        self.assertEqual(res["total_playlists"], 2)
        self.assertEqual(res["base_name"], "Century Mix")
        self.assertEqual(dummy_pl.name, "Century Mix 1")
        self.assertEqual(len(dummy_pl._tracks), 99)
        p2 = created["id-Century Mix 2"]
        self.assertEqual(len(p2._tracks), 1)

    def test_rename_playlist(self):
        dummy_pl = DummyPlaylist("pl-1", "Old Name", [])
        self.client.get_playlist_obj = MagicMock(return_value=dummy_pl)

        res = self.client.rename_playlist("pl-1", "New Name", "New Description")
        self.assertEqual(dummy_pl.name, "New Name")
        self.assertEqual(dummy_pl.description, "New Description")
        self.assertEqual(res["name"], "New Name")


    def test_find_and_clean_duplicates(self):
        # 4 tracks, where track 0 and 2 are duplicate IDs, and track 1 and 3 are normalized duplicates
        t0 = DummyTrack(10, "Blinding Lights", "The Weeknd")
        t1 = DummyTrack(20, "Starboy", "The Weeknd")
        t2 = DummyTrack(10, "Blinding Lights", "The Weeknd") # Exact ID dup
        t3 = DummyTrack(30, "Starboy (Radio Edit)", "The Weeknd") # Fuzzy name dup

        dummy_pl = DummyPlaylist("pl-dup", "My Playlist", [t0, t1, t2, t3])
        self.client.get_playlist_obj = MagicMock(return_value=dummy_pl)

        dup_info = self.client.find_duplicates("pl-dup")
        self.assertEqual(dup_info["duplicate_count"], 2)
        self.assertIn(2, dup_info["duplicate_indices"])
        self.assertIn(3, dup_info["duplicate_indices"])

        clean_res = self.client.clean_duplicates("pl-dup")
        self.assertTrue(clean_res["success"])
        self.assertEqual(clean_res["removed_count"], 2)
        # 2 tracks should remain: indices 0 and 1
        self.assertEqual(len(dummy_pl._tracks), 2)
        self.assertEqual(dummy_pl._tracks[0].id, 10)
        self.assertEqual(dummy_pl._tracks[1].id, 20)

    def test_clean_duplicates_selective(self):
        t0 = DummyTrack(10, "Blinding Lights", "The Weeknd")
        t1 = DummyTrack(20, "Starboy", "The Weeknd")
        t2 = DummyTrack(10, "Blinding Lights", "The Weeknd")
        t3 = DummyTrack(30, "Starboy (Radio Edit)", "The Weeknd")

        dummy_pl = DummyPlaylist("pl-dup2", "My Playlist", [t0, t1, t2, t3])
        self.client.get_playlist_obj = MagicMock(return_value=dummy_pl)

        # Remove ONLY track 2 (exact ID dup), keeping track 3 (radio edit)
        clean_res = self.client.clean_duplicates("pl-dup2", indices=[2])
        self.assertTrue(clean_res["success"])
        self.assertEqual(clean_res["removed_count"], 1)
        self.assertEqual(len(dummy_pl._tracks), 3)
        remaining_ids = [t.id for t in dummy_pl._tracks]
        self.assertEqual(remaining_ids, [10, 20, 30])

    def test_clean_duplicates_remove_original(self):
        t0 = DummyTrack(10, "Blinding Lights", "The Weeknd")
        t1 = DummyTrack(20, "Starboy", "The Weeknd")
        t2 = DummyTrack(10, "Blinding Lights", "The Weeknd")
        t3 = DummyTrack(30, "Starboy (Radio Edit)", "The Weeknd")

        dummy_pl = DummyPlaylist("pl-dup3", "My Playlist", [t0, t1, t2, t3])
        self.client.get_playlist_obj = MagicMock(return_value=dummy_pl)

        # Remove the ORIGINAL track 0 and 1, keeping duplicates 2 and 3
        clean_res = self.client.clean_duplicates("pl-dup3", indices=[0, 1])
        self.assertTrue(clean_res["success"])
        self.assertEqual(clean_res["removed_count"], 2)
        self.assertEqual(len(dummy_pl._tracks), 2)
        remaining_ids = [t.id for t in dummy_pl._tracks]
        self.assertEqual(remaining_ids, [10, 30])

    def test_export_and_import_json(self):
        t0 = DummyTrack(101, "Song A", "Artist A", 200)
        t1 = DummyTrack(102, "Song B", "Artist B", 180)
        dummy_pl = DummyPlaylist("pl-exp", "Export Test", [t0, t1], "Description")
        self.client.get_playlist_obj = MagicMock(return_value=dummy_pl)

        # Export JSON
        content, mime, filename = self.client.export_playlist("pl-exp", "json")
        self.assertEqual(mime, "application/json")
        self.assertIn("Export Test", content)
        self.assertIn("Song A", content)

        # Import JSON
        created_pl = DummyPlaylist("pl-imp", "Imported", [])
        self.client.create_playlist = MagicMock(return_value={"id": "pl-imp", "name": "Imported"})
        self.client.add_tracks = MagicMock(return_value=[101, 102])

        # Import JSON into existing target playlist
        target_pl = DummyPlaylist("pl-target", "Existing Target", [])
        self.client.get_playlist_obj = MagicMock(return_value=target_pl)
        self.client.add_tracks = MagicMock(return_value=[101, 102])

        imp_append_res = self.client.import_playlist("Ignored", content, "json", target_playlist_id="pl-target")
        self.assertTrue(imp_append_res["success"])
        self.assertEqual(imp_append_res["mode"], "appended")
        self.assertEqual(imp_append_res["playlist_id"], "pl-target")

    def test_import_csv_title_artist_search(self):
        """Test importing CSV with only Title and Artist columns matching via catalog search."""
        csv_data = "Title,Artist\nBlinding Lights,The Weeknd\nStarboy,The Weeknd\n"
        self.client.create_playlist = MagicMock(return_value={"id": "pl-new", "name": "Imported Playlist"})
        self.client.add_tracks = MagicMock(return_value=["10", "20"])

        def mock_search(isrc=None, title=None, artist=None):
            if "Blinding" in (title or ""):
                return {"id": "10", "name": "Blinding Lights", "artist": "The Weeknd"}
            if "Starboy" in (title or ""):
                return {"id": "20", "name": "Starboy", "artist": "The Weeknd"}
            return None

        self.client.search_track = MagicMock(side_effect=mock_search)

        res = self.client.import_playlist("My Title Artist Import", csv_data, "csv")
        self.assertTrue(res["success"])
        self.assertEqual(res["imported_tracks_count"], 2)
        self.assertEqual(res["unmatched_count"], 0)
        self.assertEqual(res["playlist_id"], "pl-new")

    def test_import_csv_german_headers_semicolon(self):
        """Test importing German Excel CSV with semicolon and optional fields (Album, Dauer)."""
        csv_data = "Titel;Interpret;Album;Dauer\nBohemian Rhapsody;Queen;A Night at the Opera;5:55\n"
        self.client.create_playlist = MagicMock(return_value={"id": "pl-ger", "name": "German Import"})
        self.client.add_tracks = MagicMock(return_value=["999"])
        self.client.search_track = MagicMock(return_value={"id": "999", "name": "Bohemian Rhapsody", "artist": "Queen"})

        res = self.client.import_playlist("German Import", csv_data, "auto")
        self.assertTrue(res["success"])
        self.assertEqual(res["imported_tracks_count"], 1)
        self.assertEqual(res["playlist_id"], "pl-ger")

    def test_import_csv_headerless_two_columns(self):
        """Test importing headerless 2-column CSV (Title, Artist)."""
        csv_data = "Hotel California,Eagles\n"
        self.client.create_playlist = MagicMock(return_value={"id": "pl-hless", "name": "Headerless"})
        self.client.add_tracks = MagicMock(return_value=["777"])
        self.client.search_track = MagicMock(return_value={"id": "777", "name": "Hotel California", "artist": "Eagles"})

        res = self.client.import_playlist("Headerless", csv_data, "csv")
        self.assertTrue(res["success"])
        self.assertEqual(res["imported_tracks_count"], 1)

    def test_import_json_title_artist(self):
        """Test importing JSON with title and artist objects."""
        json_data = json.dumps([
            {"titel": "Song One", "künstler": "Artist One"},
            {"title": "Song Two", "artist": "Artist Two"}
        ])
        self.client.create_playlist = MagicMock(return_value={"id": "pl-json", "name": "JSON Import"})
        self.client.add_tracks = MagicMock(return_value=["1", "2"])
        self.client.search_track = MagicMock(side_effect=lambda **kw: {"id": "1", "name": kw.get("title")})

        res = self.client.import_playlist("JSON Import", json_data, "json")
        self.assertTrue(res["success"])
        self.assertEqual(res["imported_tracks_count"], 2)

    def test_import_m3u_extinf(self):
        """Test importing M3U with #EXTINF Artist - Title."""
        m3u_data = "#EXTM3U\n#EXTINF:210,Daft Punk - Get Lucky\n/music/daft.mp3\n"
        self.client.create_playlist = MagicMock(return_value={"id": "pl-m3u", "name": "M3U Import"})
        self.client.add_tracks = MagicMock(return_value=["456"])
        self.client.search_track = MagicMock(return_value={"id": "456", "name": "Get Lucky", "artist": "Daft Punk"})

        res = self.client.import_playlist("M3U Import", m3u_data, "m3u")
        self.assertTrue(res["success"])
        self.assertEqual(res["imported_tracks_count"], 1)

    def test_import_no_tracks_raises(self):
        """Test error raised when no tracks match or file is empty."""
        from tidal_manager.client import TidalManagerError
        with self.assertRaises(TidalManagerError):
            self.client.import_playlist("Empty", "", "csv")

    def test_merge_playlists(self):
        t1 = DummyTrack(1, "Track 1")
        t2 = DummyTrack(2, "Track 2")
        t3 = DummyTrack(2, "Track 2") # dup
        t4 = DummyTrack(3, "Track 3")

        pl1 = DummyPlaylist("p1", "Part 1", [t1, t2])
        pl2 = DummyPlaylist("p2", "Part 2", [t3, t4])

        self.client.get_playlist_obj = lambda pid: pl1 if pid == "p1" else pl2
        self.client.create_playlist = MagicMock(return_value={"id": "merged", "name": "Merged"})
        self.client.add_tracks = MagicMock(return_value=[1, 2, 3])

        res = self.client.merge_playlists(["p1", "p2"], "Merged", deduplicate=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["total_tracks"], 3) # 1, 2, 3

    def test_shuffle_playlist(self):
        tracks = [DummyTrack(i, f"Track {i}") for i in range(10)]
        dummy_pl = DummyPlaylist("pl-shuf", "Shuffle Me", tracks)
        dummy_pl.clear = MagicMock(side_effect=lambda: setattr(dummy_pl, "_tracks", []))
        self.client.get_playlist_obj = MagicMock(return_value=dummy_pl)
        self.client.add_tracks = MagicMock()

        res = self.client.shuffle_playlist("pl-shuf")
        self.assertTrue(res["success"])
        self.assertEqual(res["shuffled_count"], 10)
        self.assertTrue(dummy_pl.clear.called)
        self.assertTrue(self.client.add_tracks.called)


    def test_reorder_track(self):
        t0 = DummyTrack(1, "Track 1")
        t1 = DummyTrack(2, "Track 2")
        t2 = DummyTrack(3, "Track 3")
        dummy_pl = DummyPlaylist("p1", "Test", [t0, t1, t2])
        dummy_pl.move_by_index = MagicMock(return_value=True)
        self.client.get_playlist_obj = MagicMock(return_value=dummy_pl)

        res = self.client.reorder_track("p1", 0, 2)
        self.assertTrue(res)
        self.assertTrue(dummy_pl.move_by_index.called)


if __name__ == "__main__":
    unittest.main()
