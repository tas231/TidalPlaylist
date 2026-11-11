"""Tidal API Client wrapper for session management, playlist operations, and batch splitting."""

from __future__ import annotations

import json
import logging
import math
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

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
            # Restrict permissions on session file (rw- --- ---)
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
            # Single non-blocking check
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
                # Login succeeded!
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

    def list_playlists(self) -> List[Dict[str, Any]]:
        """List all personal playlists for the current user."""
        if not self.is_logged_in():
            raise TidalAuthError("Not logged in to Tidal")

        raw_playlists = self.session.user.playlists()
        result = [self._format_playlist(p) for p in raw_playlists]
        # Sort primarily by name
        result.sort(key=lambda x: (x["name"].lower() if x.get("name") else ""))
        return result

    def get_playlist_obj(self, playlist_id: str) -> UserPlaylist:
        """Load a playlist object by ID and ensure it is wrapped as UserPlaylist."""
        if not self.is_logged_in():
            raise TidalAuthError("Not logged in to Tidal")

        try:
            pl = self.session.playlist(playlist_id)
            if not isinstance(pl, UserPlaylist):
                # Try explicit UserPlaylist wrapping
                pl = UserPlaylist(self.session, playlist_id)
            return pl
        except Exception as e:
            raise TidalManagerError(f"Could not load playlist '{playlist_id}': {e}") from e

    def get_playlist_details(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist metadata along with all tracks."""
        pl = self.get_playlist_obj(playlist_id)
        info = self._format_playlist(pl)

        # Retrieve all tracks with pagination
        raw_tracks = pl.tracks_paginated() if hasattr(pl, "tracks_paginated") else pl.tracks()
        tracks_formatted = []

        for idx, t in enumerate(raw_tracks):
            dur = getattr(t, "duration", 0) or 0
            m = dur // 60
            s = dur % 60

            # Artist name
            artist_name = "Unknown Artist"
            if hasattr(t, "artist") and t.artist and hasattr(t.artist, "name"):
                artist_name = t.artist.name
            elif hasattr(t, "artists") and t.artists:
                artist_name = ", ".join(a.name for a in t.artists if hasattr(a, "name"))

            # Album name & image
            album_name = ""
            album_img = ""
            if hasattr(t, "album") and t.album:
                album_name = getattr(t.album, "name", "") or ""
                try:
                    if hasattr(t.album, "image"):
                        album_img = t.album.image(dimensions=160) or ""
                except Exception:
                    pass

            tracks_formatted.append({
                "index": idx,
                "id": str(t.id),
                "name": t.name,
                "artist": artist_name,
                "album": album_name,
                "album_image": album_img,
                "duration": dur,
                "duration_formatted": f"{m}:{s:02d}",
                "explicit": bool(getattr(t, "explicit", False)),
                "audio_quality": getattr(t, "audio_quality", "LOSSLESS"),
            })

        info["tracks"] = tracks_formatted
        info["num_tracks"] = len(tracks_formatted)
        return info

    def resolve_playlist(self, identifier: str) -> UserPlaylist:
        """Resolve a playlist by UUID or case-insensitive title."""
        playlists = self.session.user.playlists()
        # Direct ID match
        for p in playlists:
            if p.id == identifier:
                return self.get_playlist_obj(p.id)

        # Title match (case-insensitive)
        matches = [p for p in playlists if p.name and p.name.strip().lower() == identifier.strip().lower()]
        if len(matches) == 1:
            return self.get_playlist_obj(matches[0].id)
        elif len(matches) > 1:
            raise TidalManagerError(f"Multiple playlists found with name '{identifier}'. Please specify the playlist ID.")

        # Partial title match
        partial = [p for p in playlists if p.name and identifier.strip().lower() in p.name.strip().lower()]
        if len(partial) == 1:
            return self.get_playlist_obj(partial[0].id)

        # Fallback to direct ID
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

        # Reload updated object
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
        # Fetch tracks to prime etag
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

        # Refresh etag
        pl.tracks(limit=1)

        # Try bulk delete first
        try:
            ok = pl.remove_by_indices(sorted_indices)
            if ok:
                return True
        except Exception as e:
            logger.warning("Bulk remove failed (%s), falling back to single-index deletion", e)

        # Fallback: remove one by one in descending order so earlier indices remain valid
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

        # Fetch current tracklist
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
            return {"copied": 0, "track_ids": []}

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

        # Step 1: Add to destination
        self.add_tracks(to_playlist_id, selected_ids, allow_duplicates=allow_duplicates)

        # Step 2: Remove from source playlist by index
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
        """
        Split a playlist if it has more than `max_tracks` (default 99):
        - Keeps the first `max_tracks` in the original playlist.
        - Creates new playlists with the same name + suffix ('2', '3', etc.).
        - Moves excess tracks to the corresponding new playlists.
        - If rename_original is True, renames original to '[Name] 1'.
        - Ensures every resulting playlist has at most `max_tracks`.
        """
        if max_tracks < 1:
            raise TidalManagerError("max_tracks must be at least 1")

        pl = self.get_playlist_obj(playlist_id)
        original_name = pl.name.strip()
        original_desc = getattr(pl, "description", "") or ""

        # Retrieve all tracks
        all_tracks = pl.tracks_paginated() if hasattr(pl, "tracks_paginated") else pl.tracks()
        total_tracks = len(all_tracks)

        if total_tracks <= max_tracks:
            return {
                "needed_split": False,
                "message": f"Playlist '{original_name}' has {total_tracks} tracks (<= {max_tracks}), no split needed.",
                "total_tracks": total_tracks,
                "playlists": [{"id": pl.id, "name": original_name, "tracks_count": total_tracks}],
            }

        # Calculate base name without existing trailing numbers
        # E.g. 'Chill Vibes 1' -> base 'Chill Vibes'
        match = re.match(r"^(.*?)(?:\s*[-_]?\s*(\d+))?$", original_name)
        if match and match.group(2):
            base_name = match.group(1).strip()
        else:
            base_name = original_name

        total_parts = math.ceil(total_tracks / max_tracks)
        logger.info(
            "Splitting playlist '%s' (%d tracks) into %d playlists (max %d each)...",
            original_name,
            total_tracks,
            total_parts,
            max_tracks,
        )

        results = []

        # Part 1: Stays in original playlist (tracks 0 to max_tracks - 1)
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

        # All indices that need to be removed from original playlist
        indices_to_remove_from_original: List[int] = list(range(max_tracks, total_tracks))

        # Create parts 2, 3, ...
        for part_num in range(2, total_parts + 1):
            start_idx = (part_num - 1) * max_tracks
            end_idx = min(part_num * max_tracks, total_tracks)
            chunk_tracks = all_tracks[start_idx:end_idx]
            chunk_ids = [str(t.id) for t in chunk_tracks]

            part_name = f"{base_name} {part_num}"
            part_desc = f"{original_desc} (Part {part_num})".strip()

            # Create new playlist
            new_pl_info = self.create_playlist(title=part_name, description=part_desc)
            new_id = new_pl_info["id"]

            # Add tracks to the new playlist
            self.add_tracks(new_id, chunk_ids, allow_duplicates=True)

            results.append({
                "part": part_num,
                "id": new_id,
                "name": part_name,
                "tracks_count": len(chunk_ids),
                "is_original": False,
            })

        # Remove the moved tracks from original playlist (descending)
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
