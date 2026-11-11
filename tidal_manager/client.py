"""Tidal API Client wrapper for session management, playlist operations, and batch splitting."""

from __future__ import annotations

import csv
import io
import json
import logging
import math
import os
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

import requests
import tidalapi
from tidalapi.playlist import UserPlaylist, Playlist

from tidal_manager.config import SESSION_FILE

logger = logging.getLogger(__name__)


class TidalManagerError(Exception):
    """Base exception for Tidal Playlist Manager errors."""
    pass


class TidalAuthError(TidalManagerError):
    """Authentication or session error."""
    pass


class TidalClient:
    """Manages the Tidal session and all playlist/track manipulation."""

    def __init__(self, session_file: Optional[Path] = None):
        self.session_file = session_file or SESSION_FILE
        self.session = tidalapi.Session()
        self._current_link_login: Optional[tidalapi.session.LinkLogin] = None
        self._login_start_time: float = 0.0

        # Try auto-loading existing session
        self.try_restore_session()

    # -------------------------------------------------------------------------
    # Authentication & Session Management
    # -------------------------------------------------------------------------

    def try_restore_session(self) -> bool:
        """Attempt to restore a previously saved session."""
        if not self.session_file.exists():
            return False

        try:
            loaded = self.session.load_session_from_file(self.session_file)
            if not loaded:
                return False

            if self.session.check_login():
                return True

            # If check_login failed, attempt token refresh
            if self.session.refresh_token:
                logger.info("Access token expired, attempting refresh...")
                if self.session.token_refresh(self.session.refresh_token):
                    self.save_session()
                    return self.session.check_login()

            return False
        except Exception as e:
            logger.warning("Failed to restore session from %s: %s", self.session_file, e)
            return False

    def is_logged_in(self) -> bool:
        """Check if currently authenticated with Tidal."""
        try:
            return bool(self.session.check_login())
        except Exception:
            return False

    def save_session(self) -> bool:
        """Save active session credentials to file."""
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            self.session.save_session_to_file(self.session_file)
            os.chmod(self.session_file, 0o600)
            return True
        except Exception as e:
            logger.error("Error saving session to %s: %s", self.session_file, e)
            return False

    def logout(self) -> bool:
        """Clear local session and file."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
        except Exception as e:
            logger.warning("Error deleting session file: %s", e)
        self.session = tidalapi.Session()
        self._current_link_login = None
        return True

    def start_oauth_login(self) -> Dict[str, Any]:
        """Start the OAuth2 Device Code login flow."""
        self._current_link_login = self.session.get_link_login()
        self._login_start_time = time.time()

        uri = self._current_link_login.verification_uri_complete
        if not uri.startswith("http"):
            full_url = f"https://{uri}"
        else:
            full_url = uri

        return {
            "device_code": self._current_link_login.device_code,
            "user_code": self._current_link_login.user_code,
            "verification_uri": self._current_link_login.verification_uri,
            "verification_url": full_url,
            "expires_in": int(self._current_link_login.expires_in),
            "interval": int(self._current_link_login.interval),
        }

    def poll_oauth_login(self) -> Dict[str, Any]:
        """Check if the pending OAuth device code authorization succeeded."""
        if not self._current_link_login:
            return {"status": "none", "logged_in": False, "message": "No active login in progress"}

        link = self._current_link_login
        elapsed = time.time() - self._login_start_time
        remaining = max(0, int(link.expires_in - elapsed))

        if remaining <= 0:
            self._current_link_login = None
            return {"status": "expired", "logged_in": False, "message": "Device login code expired"}

        try:
            url = self.session.config.api_oauth2_token
            params = {
                "client_id": self.session.config.client_id,
                "client_secret": self.session.config.client_secret,
                "device_code": link.device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "scope": "r_usr w_usr w_sub",
            }
            res = self.session.request_session.post(url, params)
            data = res.json()

            if res.ok:
                self.session.process_auth_token(data, is_pkce_token=False)
                self.save_session()
                self._current_link_login = None
                return {
                    "status": "success",
                    "logged_in": True,
                    "user": self.get_user_info(),
                    "message": "Login successful!",
                }

            error = data.get("error")
            if error == "authorization_pending":
                return {
                    "status": "pending",
                    "logged_in": False,
                    "remaining_seconds": remaining,
                    "message": "Waiting for user confirmation in browser...",
                }
            elif error == "expired_token":
                self._current_link_login = None
                return {
                    "status": "expired",
                    "logged_in": False,
                    "message": "Login code expired",
                }
            else:
                return {
                    "status": "waiting",
                    "logged_in": False,
                    "remaining_seconds": remaining,
                    "message": data.get("error_description", "Waiting for confirmation..."),
                }
        except Exception as e:
            logger.exception("Error checking login status")
            return {"status": "error", "logged_in": False, "message": str(e)}

    def get_user_info(self) -> Dict[str, Any]:
        """Retrieve details about the logged-in user."""
        if not self.is_logged_in():
            return {"logged_in": False}

        u = self.session.user
        user_id = getattr(u, "id", None)
        username = getattr(u, "username", None) or getattr(u, "email", None) or f"User {user_id}"
        country = getattr(self.session, "country_code", None)

        return {
            "logged_in": True,
            "id": user_id,
            "username": username,
            "first_name": getattr(u, "first_name", None),
            "last_name": getattr(u, "last_name", None),
            "country_code": country,
        }

    # -------------------------------------------------------------------------
    # Playlist Retrieval & Formatting
    # -------------------------------------------------------------------------

    def _format_playlist(self, pl: Union[Playlist, UserPlaylist]) -> Dict[str, Any]:
        """Convert a Tidal playlist object into a clean dictionary."""
        is_user = isinstance(pl, UserPlaylist) or (
            hasattr(pl, "creator")
            and pl.creator
            and hasattr(self.session.user, "id")
            and pl.creator.id == self.session.user.id
        )

        image_url = ""
        try:
            if hasattr(pl, "image") and callable(pl.image):
                image_url = pl.image(dimensions=320) or ""
        except Exception:
            pass

        duration_sec = getattr(pl, "duration", 0) or 0
        hours = duration_sec // 3600
        mins = (duration_sec % 3600) // 60
        if hours > 0:
            duration_str = f"{hours} hr {mins} min"
        else:
            duration_str = f"{mins} min"

        return {
            "id": pl.id,
            "name": pl.name,
            "description": getattr(pl, "description", "") or "",
            "num_tracks": getattr(pl, "num_tracks", 0) or 0,
            "duration": duration_sec,
            "duration_formatted": duration_str,
            "image": image_url,
            "is_user_playlist": is_user,
            "public": getattr(pl, "public", False),
            "last_updated": str(getattr(pl, "last_updated", "") or ""),
            "created": str(getattr(pl, "created", "") or ""),
        }

    def _format_track(self, idx: int, t: Any) -> Dict[str, Any]:
        """Format a single Track object into dictionary."""
        dur = getattr(t, "duration", 0) or 0
        m = dur // 60
        s = dur % 60

        artist_name = "Unknown Artist"
        if hasattr(t, "artist") and t.artist and hasattr(t.artist, "name"):
            artist_name = t.artist.name
        elif hasattr(t, "artists") and t.artists:
            artist_name = ", ".join(a.name for a in t.artists if hasattr(a, "name"))

        album_name = ""
        album_img = ""
        if hasattr(t, "album") and t.album:
            album_name = getattr(t.album, "name", "") or ""
            try:
                if hasattr(t.album, "image"):
                    album_img = t.album.image(dimensions=160) or ""
            except Exception:
                pass

        return {
            "index": idx,
            "id": str(t.id),
            "name": t.name,
            "artist": artist_name,
            "album": album_name,
            "album_image": album_img,
            "duration": dur,
            "duration_formatted": f"{m}:{s:02d}",
            "explicit": bool(getattr(t, "explicit", False)),
            "isrc": getattr(t, "isrc", "") or "",
            "audio_quality": getattr(t, "audio_quality", "LOSSLESS"),
        }

    def list_playlists(self) -> List[Dict[str, Any]]:
        """List all personal playlists for the current user."""
        if not self.is_logged_in():
            raise TidalAuthError("Not logged in to Tidal")

        raw_playlists = self.session.user.playlists()
        result = [self._format_playlist(p) for p in raw_playlists]
        result.sort(key=lambda x: (x["name"].lower() if x.get("name") else ""))
        return result

    def get_playlist_obj(self, playlist_id: str) -> UserPlaylist:
        """Load a playlist object by ID and ensure it is wrapped as UserPlaylist."""
        if not self.is_logged_in():
            raise TidalAuthError("Not logged in to Tidal")

        try:
            pl = self.session.playlist(playlist_id)
            if not isinstance(pl, UserPlaylist):
                pl = UserPlaylist(self.session, playlist_id)
            return pl
        except Exception as e:
            raise TidalManagerError(f"Could not load playlist '{playlist_id}': {e}") from e

    def get_playlist_details(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist metadata along with all tracks."""
        pl = self.get_playlist_obj(playlist_id)
        info = self._format_playlist(pl)

        raw_tracks = pl.tracks_paginated() if hasattr(pl, "tracks_paginated") else pl.tracks()
        tracks_formatted = [self._format_track(idx, t) for idx, t in enumerate(raw_tracks)]

        info["tracks"] = tracks_formatted
        info["num_tracks"] = len(tracks_formatted)
        return info

    def resolve_playlist(self, identifier: str) -> UserPlaylist:
        """Resolve a playlist by UUID or case-insensitive title."""
        playlists = self.session.user.playlists()
        for p in playlists:
            if p.id == identifier:
                return self.get_playlist_obj(p.id)

        matches = [p for p in playlists if p.name and p.name.strip().lower() == identifier.strip().lower()]
        if len(matches) == 1:
            return self.get_playlist_obj(matches[0].id)
        elif len(matches) > 1:
            raise TidalManagerError(f"Multiple playlists found with name '{identifier}'. Please specify the playlist ID.")

        partial = [p for p in playlists if p.name and identifier.strip().lower() in p.name.strip().lower()]
        if len(partial) == 1:
            return self.get_playlist_obj(partial[0].id)

        return self.get_playlist_obj(identifier)

    # -------------------------------------------------------------------------
    # Playlist Management (Create, Rename, Delete)
    # -------------------------------------------------------------------------

    def create_playlist(self, title: str, description: str = "") -> Dict[str, Any]:
        """Create a new playlist."""
        if not self.is_logged_in():
            raise TidalAuthError("Not logged in to Tidal")

        clean_title = (title or "").strip()
        if not clean_title:
            raise TidalManagerError("Playlist title cannot be empty")

        new_pl = self.session.user.create_playlist(title=clean_title, description=description or "")
        return self._format_playlist(new_pl)

    def rename_playlist(self, playlist_id: str, new_title: str, new_description: Optional[str] = None) -> Dict[str, Any]:
        """Rename an existing playlist and optionally update its description."""
        pl = self.get_playlist_obj(playlist_id)
        clean_title = (new_title or "").strip()
        if not clean_title:
            raise TidalManagerError("New title cannot be empty")

        desc = new_description if new_description is not None else (getattr(pl, "description", "") or "")
        success = pl.edit(title=clean_title, description=desc)
        if not success:
            raise TidalManagerError(f"Failed to rename playlist {playlist_id}")

        updated = self.get_playlist_obj(playlist_id)
        return self._format_playlist(updated)

    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete an existing user playlist."""
        pl = self.get_playlist_obj(playlist_id)
        success = pl.delete()
        if not success:
            raise TidalManagerError(f"Failed to delete playlist {playlist_id}")
        return True

    # -------------------------------------------------------------------------
    # Track Operations (Add, Remove, Copy, Move)
    # -------------------------------------------------------------------------

    def add_tracks(
        self,
        playlist_id: str,
        track_ids: Sequence[Union[str, int]],
        allow_duplicates: bool = False,
        chunk_size: int = 50,
    ) -> List[int]:
        """Add tracks to a playlist in safe chunks."""
        pl = self.get_playlist_obj(playlist_id)
        try:
            pl.tracks(limit=1)
        except Exception:
            pass

        added_all: List[int] = []
        str_ids = [str(tid) for tid in track_ids if tid]
        if not str_ids:
            return added_all

        for i in range(0, len(str_ids), chunk_size):
            chunk = str_ids[i : i + chunk_size]
            added = pl.add(chunk, allow_duplicates=allow_duplicates)
            if added:
                added_all.extend(added)

        return added_all

    def remove_tracks_by_indices(self, playlist_id: str, indices: Sequence[int]) -> bool:
        """Remove tracks at specified indices from a playlist."""
        pl = self.get_playlist_obj(playlist_id)
        sorted_indices = sorted(set(indices), reverse=True)
        if not sorted_indices:
            return True

        pl.tracks(limit=1)
        try:
            ok = pl.remove_by_indices(sorted_indices)
            if ok:
                return True
        except Exception as e:
            logger.warning("Bulk remove failed (%s), falling back to single-index deletion", e)

        for idx in sorted_indices:
            pl.tracks(limit=1)
            pl.remove_by_index(idx)

        return True

    def remove_tracks_by_ids(self, playlist_id: str, track_ids: Sequence[Union[str, int]]) -> bool:
        """Remove tracks with matching track IDs from a playlist."""
        pl = self.get_playlist_obj(playlist_id)
        str_ids = {str(tid) for tid in track_ids}
        if not str_ids:
            return True

        all_tracks = pl.tracks_paginated() if hasattr(pl, "tracks_paginated") else pl.tracks()
        matching_indices = [idx for idx, t in enumerate(all_tracks) if str(t.id) in str_ids]
        if not matching_indices:
            return True

        return self.remove_tracks_by_indices(playlist_id, matching_indices)

    def copy_tracks(
        self,
        from_playlist_id: str,
        to_playlist_id: str,
        indices: Optional[Sequence[int]] = None,
        track_ids: Optional[Sequence[Union[str, int]]] = None,
        allow_duplicates: bool = True,
    ) -> Dict[str, Any]:
        """Copy selected tracks from one playlist to another."""
        src_pl = self.get_playlist_obj(from_playlist_id)
        dst_pl = self.get_playlist_obj(to_playlist_id)

        all_src_tracks = src_pl.tracks_paginated() if hasattr(src_pl, "tracks_paginated") else src_pl.tracks()

        selected_ids: List[str] = []
        if indices is not None and len(indices) > 0:
            for idx in sorted(indices):
                if 0 <= idx < len(all_src_tracks):
                    selected_ids.append(str(all_src_tracks[idx].id))
        elif track_ids is not None and len(track_ids) > 0:
            selected_ids = [str(tid) for tid in track_ids]
        else:
            raise TidalManagerError("No tracks specified to copy")

        if not selected_ids:
            return {"copied_count": 0, "track_ids": []}

        added = self.add_tracks(to_playlist_id, selected_ids, allow_duplicates=allow_duplicates)
        return {
            "success": True,
            "copied_count": len(selected_ids),
            "track_ids": selected_ids,
            "from_playlist": src_pl.name,
            "to_playlist": dst_pl.name,
        }

    def move_tracks(
        self,
        from_playlist_id: str,
        to_playlist_id: str,
        indices: Optional[Sequence[int]] = None,
        track_ids: Optional[Sequence[Union[str, int]]] = None,
        allow_duplicates: bool = True,
    ) -> Dict[str, Any]:
        """Move tracks from source to target playlist (add to target, delete from source)."""
        src_pl = self.get_playlist_obj(from_playlist_id)
        dst_pl = self.get_playlist_obj(to_playlist_id)

        all_src_tracks = src_pl.tracks_paginated() if hasattr(src_pl, "tracks_paginated") else src_pl.tracks()

        target_indices: List[int] = []
        selected_ids: List[str] = []

        if indices is not None and len(indices) > 0:
            for idx in indices:
                if 0 <= idx < len(all_src_tracks):
                    target_indices.append(idx)
                    selected_ids.append(str(all_src_tracks[idx].id))
        elif track_ids is not None and len(track_ids) > 0:
            str_ids = [str(t) for t in track_ids]
            for idx, t in enumerate(all_src_tracks):
                if str(t.id) in str_ids:
                    target_indices.append(idx)
                    selected_ids.append(str(t.id))
        else:
            raise TidalManagerError("No tracks specified to move")

        if not selected_ids:
            return {"moved_count": 0, "track_ids": []}

        self.add_tracks(to_playlist_id, selected_ids, allow_duplicates=allow_duplicates)
        self.remove_tracks_by_indices(from_playlist_id, target_indices)

        return {
            "success": True,
            "moved_count": len(selected_ids),
            "track_ids": selected_ids,
            "from_playlist": src_pl.name,
            "to_playlist": dst_pl.name,
        }

    # -------------------------------------------------------------------------
    # Auto-Split Feature (Max 99 tracks per playlist)
    # -------------------------------------------------------------------------

    def split_playlist(
        self,
        playlist_id: str,
        max_tracks: int = 99,
        rename_original: bool = True,
    ) -> Dict[str, Any]:
        """Split a playlist into multiple playlists with suffix if it has > max_tracks."""
        if max_tracks < 1:
            raise TidalManagerError("max_tracks must be at least 1")

        pl = self.get_playlist_obj(playlist_id)
        original_name = pl.name.strip()
        original_desc = getattr(pl, "description", "") or ""

        all_tracks = pl.tracks_paginated() if hasattr(pl, "tracks_paginated") else pl.tracks()
        total_tracks = len(all_tracks)

        if total_tracks <= max_tracks:
            return {
                "needed_split": False,
                "message": f"Playlist '{original_name}' has {total_tracks} tracks (<= {max_tracks}), no split needed.",
                "total_tracks": total_tracks,
                "playlists": [{"id": pl.id, "name": original_name, "tracks_count": total_tracks}],
            }

        match = re.match(r"^(.*?)(?:\s*[-_]?\s*(\d+))?$", original_name)
        if match and match.group(2):
            base_name = match.group(1).strip()
        else:
            base_name = original_name

        total_parts = math.ceil(total_tracks / max_tracks)
        results = []

        part1_name = f"{base_name} 1" if rename_original else original_name
        if rename_original and original_name != part1_name:
            self.rename_playlist(playlist_id, part1_name, original_desc)

        results.append({
            "part": 1,
            "id": playlist_id,
            "name": part1_name,
            "tracks_count": min(max_tracks, total_tracks),
            "is_original": True,
        })

        indices_to_remove_from_original: List[int] = list(range(max_tracks, total_tracks))

        for part_num in range(2, total_parts + 1):
            start_idx = (part_num - 1) * max_tracks
            end_idx = min(part_num * max_tracks, total_tracks)
            chunk_tracks = all_tracks[start_idx:end_idx]
            chunk_ids = [str(t.id) for t in chunk_tracks]

            part_name = f"{base_name} {part_num}"
            part_desc = f"{original_desc} (Part {part_num})".strip()

            new_pl_info = self.create_playlist(title=part_name, description=part_desc)
            new_id = new_pl_info["id"]

            self.add_tracks(new_id, chunk_ids, allow_duplicates=True)

            results.append({
                "part": part_num,
                "id": new_id,
                "name": part_name,
                "tracks_count": len(chunk_ids),
                "is_original": False,
            })

        self.remove_tracks_by_indices(playlist_id, indices_to_remove_from_original)

        return {
            "needed_split": True,
            "success": True,
            "base_name": base_name,
            "original_tracks_count": total_tracks,
            "total_playlists": total_parts,
            "max_per_playlist": max_tracks,
            "playlists": results,
            "message": f"Successfully split '{original_name}' into {total_parts} playlists with max {max_tracks} tracks each.",
        }

    # -------------------------------------------------------------------------
    # 1. Duplicate Finder & Cleaner
    # -------------------------------------------------------------------------

    def _normalize_string(self, text: str) -> str:
        """Normalize song title or artist for fuzzy duplicate comparison."""
        if not text:
            return ""
        s = text.lower().strip()
        # Remove text in parentheses/brackets like (Remastered 2021) or [Live]
        s = re.sub(r"[\(\[].*?[\)\]]", "", s)
        s = re.sub(r"[^\w\s]", "", s)
        return " ".join(s.split())

    def find_duplicates(self, playlist_id: str) -> Dict[str, Any]:
        """Find duplicate tracks within a playlist by ID and Normalized Name + Artist."""
        details = self.get_playlist_details(playlist_id)
        tracks = details.get("tracks", [])

        seen_ids: Dict[str, int] = {}
        seen_normalized: Dict[str, int] = {}
        duplicate_indices: Set[int] = set()
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for t in tracks:
            idx = t["index"]
            tid = t["id"]
            norm_key = f"{self._normalize_string(t['name'])} - {self._normalize_string(t['artist'])}"

            is_dup = False
            group_key = norm_key

            if tid in seen_ids:
                is_dup = True
                duplicate_indices.add(idx)
            else:
                seen_ids[tid] = idx

            if norm_key and norm_key in seen_normalized:
                is_dup = True
                duplicate_indices.add(idx)
            elif norm_key:
                seen_normalized[norm_key] = idx

            if is_dup:
                if group_key not in groups:
                    first_idx = seen_normalized.get(group_key, seen_ids.get(tid))
                    first_track = next((x for x in tracks if x["index"] == first_idx), None)
                    groups[group_key] = [first_track] if first_track else []
                groups[group_key].append(t)

        formatted_groups = [
            {"key": k, "tracks": v, "count": len(v)}
            for k, v in groups.items()
        ]

        return {
            "playlist_id": playlist_id,
            "playlist_name": details.get("name"),
            "total_tracks": len(tracks),
            "duplicate_count": len(duplicate_indices),
            "duplicate_indices": sorted(duplicate_indices),
            "groups": formatted_groups,
        }

    def clean_duplicates(self, playlist_id: str) -> Dict[str, Any]:
        """Remove duplicate tracks from a playlist, keeping the first occurrence."""
        dup_info = self.find_duplicates(playlist_id)
        dup_indices = dup_info["duplicate_indices"]

        if not dup_indices:
            return {
                "success": True,
                "removed_count": 0,
                "message": "No duplicates found.",
            }

        self.remove_tracks_by_indices(playlist_id, dup_indices)
        return {
            "success": True,
            "removed_count": len(dup_indices),
            "message": f"Successfully removed {len(dup_indices)} duplicate track(s).",
        }

    # -------------------------------------------------------------------------
    # 2. Backup & Export / Import
    # -------------------------------------------------------------------------

    def export_playlist(self, playlist_id: str, format_type: str = "json") -> Tuple[str, str, str]:
        """
        Export a playlist.
        Returns (content_string, mime_type, filename).
        """
        details = self.get_playlist_details(playlist_id)
        name = details.get("name", "playlist").replace("/", "_").replace("\\", "_")
        tracks = details.get("tracks", [])

        if format_type.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Index", "Title", "Artist", "Album", "Duration_Seconds", "Duration", "Tidal_ID", "ISRC"])
            for t in tracks:
                writer.writerow([
                    t["index"] + 1,
                    t["name"],
                    t["artist"],
                    t["album"],
                    t["duration"],
                    t["duration_formatted"],
                    t["id"],
                    t.get("isrc", ""),
                ])
            return output.getvalue(), "text/csv", f"{name}.csv"

        elif format_type.lower() == "m3u":
            output = io.StringIO()
            output.write("#EXTM3U\n")
            for t in tracks:
                output.write(f"#EXTINF:{t['duration']},{t['artist']} - {t['name']}\n")
                output.write(f"#TIDAL-ID:{t['id']}\n")
                output.write(f"https://listen.tidal.com/track/{t['id']}\n")
            return output.getvalue(), "audio/x-mpegurl", f"{name}.m3u8"

        else:
            export_data = {
                "app": "TIDAL Playlist Manager",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "playlist": {
                    "id": details.get("id"),
                    "name": details.get("name"),
                    "description": details.get("description"),
                    "num_tracks": len(tracks),
                    "duration": details.get("duration"),
                    "duration_formatted": details.get("duration_formatted"),
                },
                "tracks": tracks,
            }
            return json.dumps(export_data, indent=2), "application/json", f"{name}.json"

    def import_playlist(
        self,
        title: Optional[str],
        file_content: str,
        format_type: str = "auto",
        description: str = "Imported via TIDAL Playlist Manager",
        target_playlist_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Import tracks from JSON, CSV, or M3U, creating a new playlist or appending to an existing one."""
        raw = file_content.strip()
        track_ids: List[str] = []
        parsed_title = title or "Imported Playlist"

        if format_type == "auto":
            if raw.startswith("{") or raw.startswith("["):
                format_type = "json"
            elif raw.startswith("#EXTM3U"):
                format_type = "m3u"
            else:
                format_type = "csv"

        if format_type == "json":
            data = json.loads(raw)
            if isinstance(data, dict):
                parsed_title = title or data.get("playlist", {}).get("name") or data.get("title") or parsed_title
                tracks = data.get("tracks", [])
                for t in tracks:
                    if isinstance(t, dict) and t.get("id"):
                        track_ids.append(str(t["id"]))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("id"):
                        track_ids.append(str(item["id"]))

        elif format_type == "m3u":
            lines = raw.splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith("#TIDAL-ID:"):
                    tid = line.replace("#TIDAL-ID:", "").strip()
                    if tid:
                        track_ids.append(tid)
                elif "listen.tidal.com/track/" in line:
                    match = re.search(r"track/(\d+)", line)
                    if match:
                        track_ids.append(match.group(1))

        elif format_type == "csv":
            reader = csv.reader(io.StringIO(raw))
            rows = list(reader)
            if rows:
                header = [h.strip().lower() for h in rows[0]]
                id_col = -1
                for candidate in ["tidal_id", "tidal id", "track_id", "id"]:
                    if candidate in header:
                        id_col = header.index(candidate)
                        break

                for row in rows[1:]:
                    if id_col != -1 and len(row) > id_col and row[id_col].strip().isdigit():
                        track_ids.append(row[id_col].strip())

        if not track_ids:
            raise TidalManagerError("No valid TIDAL track IDs could be found in the imported file.")

        if target_playlist_id:
            target_pl = self.get_playlist_obj(target_playlist_id)
            self.add_tracks(target_playlist_id, track_ids, allow_duplicates=True)
            return {
                "success": True,
                "playlist_id": target_playlist_id,
                "title": target_pl.name,
                "imported_tracks_count": len(track_ids),
                "mode": "appended",
            }

        new_pl = self.create_playlist(title=parsed_title, description=description)
        new_id = new_pl["id"]
        self.add_tracks(new_id, track_ids, allow_duplicates=True)

        return {
            "success": True,
            "playlist_id": new_id,
            "title": parsed_title,
            "imported_tracks_count": len(track_ids),
            "mode": "created",
        }

    # -------------------------------------------------------------------------
    # 3. Playlist Merge & Shuffle
    # -------------------------------------------------------------------------

    def merge_playlists(
        self,
        source_ids: Sequence[str],
        target_title: str,
        target_description: str = "",
        deduplicate: bool = True,
    ) -> Dict[str, Any]:
        """Merge tracks from multiple source playlists into a new target playlist."""
        if not source_ids:
            raise TidalManagerError("Must specify at least one source playlist to merge.")

        all_track_ids: List[str] = []
        seen: Set[str] = set()

        for pid in source_ids:
            pl = self.get_playlist_obj(pid)
            tracks = pl.tracks_paginated() if hasattr(pl, "tracks_paginated") else pl.tracks()
            for t in tracks:
                tid = str(t.id)
                if deduplicate:
                    if tid not in seen:
                        seen.add(tid)
                        all_track_ids.append(tid)
                else:
                    all_track_ids.append(tid)

        if not all_track_ids:
            raise TidalManagerError("Source playlists contain no tracks.")

        new_pl = self.create_playlist(title=target_title, description=target_description)
        self.add_tracks(new_pl["id"], all_track_ids, allow_duplicates=True)

        return {
            "success": True,
            "merged_playlist_id": new_pl["id"],
            "title": target_title,
            "total_tracks": len(all_track_ids),
            "sources_count": len(source_ids),
        }

    def shuffle_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Shuffle a playlist on TIDAL into a randomized cloud order."""
        pl = self.get_playlist_obj(playlist_id)
        raw_tracks = pl.tracks_paginated() if hasattr(pl, "tracks_paginated") else pl.tracks()
        track_ids = [str(t.id) for t in raw_tracks]

        if len(track_ids) <= 1:
            return {"success": True, "message": "Playlist has 1 or fewer tracks, no shuffle needed."}

        random.shuffle(track_ids)

        pl.clear()
        self.add_tracks(playlist_id, track_ids, allow_duplicates=True)

        return {
            "success": True,
            "shuffled_count": len(track_ids),
            "message": f"Successfully shuffled {len(track_ids)} tracks in '{pl.name}'.",
        }

    # -------------------------------------------------------------------------
    # 4. Sorting & Reordering
    # -------------------------------------------------------------------------

    def reorder_track(self, playlist_id: str, from_index: int, to_index: int) -> bool:
        """Move a track from one position to another within the same playlist."""
        pl = self.get_playlist_obj(playlist_id)
        try:
            pl.tracks(limit=1)
        except Exception:
            pass
        return pl.move_by_index(from_index, to_index)

    def reorder_playlist_sorted(
        self,
        playlist_id: str,
        sort_by: str = "title",
        ascending: bool = True,
    ) -> Dict[str, Any]:
        """Permanently sort and save a playlist order on TIDAL."""
        pl = self.get_playlist_obj(playlist_id)
        raw_tracks = pl.tracks_paginated() if hasattr(pl, "tracks_paginated") else pl.tracks()
        tracks_formatted = [self._format_track(i, t) for i, t in enumerate(raw_tracks)]

        key_fn = lambda x: x["name"].lower()
        if sort_by == "artist":
            key_fn = lambda x: (x["artist"].lower(), x["name"].lower())
        elif sort_by == "album":
            key_fn = lambda x: (x["album"].lower(), x["name"].lower())
        elif sort_by == "duration":
            key_fn = lambda x: x["duration"]

        tracks_formatted.sort(key=key_fn, reverse=not ascending)
        sorted_ids = [t["id"] for t in tracks_formatted]

        pl.clear()
        self.add_tracks(playlist_id, sorted_ids, allow_duplicates=True)

        return {
            "success": True,
            "sorted_by": sort_by,
            "ascending": ascending,
            "track_count": len(sorted_ids),
            "message": f"Playlist sorted by {sort_by} ({'A-Z' if ascending else 'Z-A'}).",
        }

    # -------------------------------------------------------------------------
    # 5. Audio Preview & 7. Catalog Search
    # -------------------------------------------------------------------------

    def search_catalog(self, query: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Search the TIDAL catalog for tracks."""
        if not self.is_logged_in():
            raise TidalAuthError("Not logged in to Tidal")

        clean_q = (query or "").strip()
        if not clean_q:
            return []

        res = self.session.search(query=clean_q, models=[tidalapi.media.Track], limit=limit)
        tracks = res.get("tracks", []) if isinstance(res, dict) else getattr(res, "tracks", [])

        results = []
        for idx, t in enumerate(tracks):
            results.append(self._format_track(idx, t))
        return results

    def get_track_preview(self, track_id: str) -> Dict[str, Any]:
        """Retrieve direct audio stream URL or preview link for a track."""
        if not self.is_logged_in():
            raise TidalAuthError("Not logged in to Tidal")

        track = self.session.track(track_id)
        preview_url = None
        try:
            preview_url = track.get_url()
        except Exception:
            preview_url = None

        artist_name = "Unknown Artist"
        if hasattr(track, "artist") and track.artist and hasattr(track.artist, "name"):
            artist_name = track.artist.name

        album_img = ""
        if hasattr(track, "album") and track.album and hasattr(track.album, "image"):
            try:
                album_img = track.album.image(dimensions=160)
            except Exception:
                pass

        return {
            "id": str(track_id),
            "name": getattr(track, "name", ""),
            "artist": artist_name,
            "album_image": album_img,
            "preview_url": preview_url,
            "web_url": f"https://listen.tidal.com/track/{track_id}",
        }
