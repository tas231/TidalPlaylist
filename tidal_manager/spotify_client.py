"""Spotify API Client wrapper for session management, playlist operations, and cross-platform track matching."""

from __future__ import annotations

import base64
import json
import logging
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Union

import requests

from tidal_manager.config import SPOTIFY_SESSION_FILE, SPOTIFY_DEFAULT_REDIRECT_URI

logger = logging.getLogger(__name__)

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

SPOTIFY_SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-library-read",
    "user-read-private",
    "user-read-email",
]


class SpotifyError(Exception):
    """Base exception for Spotify client errors."""
    pass


class SpotifyAuthError(SpotifyError):
    """Authentication or token error."""
    pass


class SpotifyClient:
    """Manages Spotify OAuth session, playlists, track operations, and catalog search."""

    def __init__(self, session_file: Optional[Path] = None):
        self.session_file = session_file or SPOTIFY_SESSION_FILE
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: float = 0.0
        self.redirect_uri: str = SPOTIFY_DEFAULT_REDIRECT_URI
        self._user_cache: Optional[Dict[str, Any]] = None

        self.load_session()

    # -------------------------------------------------------------------------
    # Session & Configuration
    # -------------------------------------------------------------------------

    def load_session(self) -> bool:
        """Load credentials and tokens from local session file."""
        if not self.session_file.exists():
            return False

        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.client_id = data.get("client_id")
            self.client_secret = data.get("client_secret")
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.expires_at = data.get("expires_at", 0.0)
            self.redirect_uri = data.get("redirect_uri", SPOTIFY_DEFAULT_REDIRECT_URI)
            return True
        except Exception as e:
            logger.warning(f"Failed to load Spotify session from {self.session_file}: {e}")
            return False

    def save_session(self) -> None:
        """Persist credentials and tokens to local session file."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "redirect_uri": self.redirect_uri,
        }
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def set_config(self, client_id: str, client_secret: str, redirect_uri: Optional[str] = None) -> None:
        """Configure Spotify Developer App Client ID and Secret."""
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        if redirect_uri:
            self.redirect_uri = redirect_uri.strip()
        self.save_session()

    def logout(self) -> None:
        """Log out and remove stored Spotify tokens (keeps client_id/secret for convenience)."""
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0.0
        self._user_cache = None
        self.save_session()

    def is_configured(self) -> bool:
        """Check if Spotify Client ID and Secret are configured."""
        return bool(self.client_id and self.client_secret)

    def is_authenticated(self) -> bool:
        """Check if client has a valid or refreshable token."""
        if not self.is_configured():
            return False
        if not self.access_token and not self.refresh_token:
            return False
        return True

    # -------------------------------------------------------------------------
    # OAuth2 Flow
    # -------------------------------------------------------------------------

    def get_auth_url(self, state: str = "spotify_auth") -> str:
        """Generate the Spotify OAuth2 Authorization URL."""
        if not self.client_id:
            raise SpotifyAuthError("Spotify Client ID is not configured. Please set credentials first.")

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(SPOTIFY_SCOPES),
            "state": state,
            "show_dialog": "true",
        }
        return f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        if not self.is_configured():
            raise SpotifyAuthError("Spotify Client ID and Secret must be configured.")

        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        resp = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=15)
        if resp.status_code != 200:
            raise SpotifyAuthError(f"Failed to exchange Spotify code: {resp.text}")

        res_data = resp.json()
        self.access_token = res_data.get("access_token")
        if "refresh_token" in res_data:
            self.refresh_token = res_data["refresh_token"]
        expires_in = res_data.get("expires_in", 3600)
        self.expires_at = time.time() + expires_in
        self._user_cache = None
        self.save_session()
        return res_data

    def refresh_access_token(self) -> bool:
        """Refresh expired access token using refresh_token."""
        if not self.refresh_token or not self.is_configured():
            return False

        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        try:
            resp = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=15)
            if resp.status_code != 200:
                logger.error(f"Spotify token refresh failed: {resp.text}")
                return False

            res_data = resp.json()
            self.access_token = res_data.get("access_token")
            if "refresh_token" in res_data:
                self.refresh_token = res_data["refresh_token"]
            expires_in = res_data.get("expires_in", 3600)
            self.expires_at = time.time() + expires_in
            self.save_session()
            return True
        except Exception as e:
            logger.error(f"Error during Spotify token refresh: {e}")
            return False

    def get_valid_token(self) -> str:
        """Ensure token is valid and return access token."""
        if not self.access_token and not self.refresh_token:
            raise SpotifyAuthError("Not connected to Spotify. Please authenticate first.")

        if time.time() >= (self.expires_at - 60):
            if not self.refresh_access_token():
                raise SpotifyAuthError("Spotify session expired. Please reconnect.")

        if not self.access_token:
            raise SpotifyAuthError("No valid Spotify access token available.")

        return self.access_token

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an authenticated API request to Spotify Web API."""
        token = self.get_valid_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        url = endpoint if endpoint.startswith("http") else f"{SPOTIFY_API_BASE}{endpoint}"
        resp = requests.request(method, url, headers=headers, **kwargs)

        # Handle 401 token expiration retry
        if resp.status_code == 401 and self.refresh_token:
            if self.refresh_access_token():
                headers["Authorization"] = f"Bearer {self.access_token}"
                resp = requests.request(method, url, headers=headers, **kwargs)

        if resp.status_code >= 400:
            try:
                err_json = resp.json()
                msg = err_json.get("error", {}).get("message", resp.text)
            except Exception:
                msg = resp.text
            raise SpotifyError(f"Spotify API error ({resp.status_code}): {msg}")

        return resp

    # -------------------------------------------------------------------------
    # User Profile
    # -------------------------------------------------------------------------

    def get_current_user(self) -> Dict[str, Any]:
        """Fetch current authenticated Spotify user profile."""
        if self._user_cache:
            return self._user_cache

        resp = self._request("GET", "/me")
        data = resp.json()
        images = data.get("images") or []
        image_url = images[0].get("url") if images else ""

        user_info = {
            "id": data.get("id"),
            "username": data.get("display_name") or data.get("id"),
            "email": data.get("email"),
            "country_code": data.get("country", ""),
            "product": data.get("product", ""),
            "image": image_url,
            "platform": "spotify",
            "logged_in": True,
        }
        self._user_cache = user_info
        return user_info

    # -------------------------------------------------------------------------
    # Playlists
    # -------------------------------------------------------------------------

    def list_playlists(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all playlists owned or followed by current user."""
        user = self.get_current_user()
        user_id = user["id"]

        playlists: List[Dict[str, Any]] = []
        offset = 0

        while True:
            resp = self._request("GET", f"/me/playlists?limit={limit}&offset={offset}")
            data = resp.json()
            items = data.get("items", [])
            if not items:
                break

            for p in items:
                if not p:
                    continue
                owner_id = p.get("owner", {}).get("id")
                is_user = (owner_id == user_id)
                images = p.get("images") or []
                image_url = images[0].get("url") if images else ""
                tracks_total = p.get("tracks", {}).get("total", 0)

                playlists.append({
                    "id": p["id"],
                    "name": p.get("name", "Untitled Playlist"),
                    "description": p.get("description", "") or "",
                    "num_tracks": tracks_total,
                    "duration": 0,
                    "duration_formatted": "",
                    "image": image_url,
                    "is_user_playlist": is_user,
                    "public": p.get("public", False),
                    "owner": p.get("owner", {}).get("display_name") or owner_id or "",
                    "platform": "spotify",
                })

            if len(items) < limit or len(playlists) >= data.get("total", 0):
                break
            offset += limit

        return playlists

    def get_playlist_details(self, playlist_id: str) -> Dict[str, Any]:
        """Fetch playlist metadata and all tracks."""
        resp = self._request("GET", f"/playlists/{playlist_id}")
        pl = resp.json()
        user = self.get_current_user()
        is_user = (pl.get("owner", {}).get("id") == user["id"])

        images = pl.get("images") or []
        image_url = images[0].get("url") if images else ""

        # Fetch all tracks (paginated)
        tracks: List[Dict[str, Any]] = []
        total_duration_sec = 0

        next_url = f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks?limit=100"
        idx = 0

        while next_url:
            tr_resp = self._request("GET", next_url)
            tr_data = tr_resp.json()
            items = tr_data.get("items", [])

            for item in items:
                if not item:
                    continue
                track = item.get("track")
                if not track:  # Can be None for local/deleted items
                    continue

                duration_ms = track.get("duration_ms", 0)
                dur_sec = duration_ms // 1000
                total_duration_sec += dur_sec

                mins = dur_sec // 60
                secs = dur_sec % 60
                dur_fmt = f"{mins}:{secs:02d}"

                # Artists
                artists_list = track.get("artists") or []
                artist_names = ", ".join(a.get("name", "") for a in artists_list if a.get("name"))

                # Album & cover
                album = track.get("album") or {}
                album_name = album.get("name", "")
                album_imgs = album.get("images") or []
                cover_url = album_imgs[-1].get("url") if album_imgs else (album_imgs[0].get("url") if album_imgs else "")

                # ISRC
                external_ids = track.get("external_ids") or {}
                isrc = external_ids.get("isrc")

                tracks.append({
                    "index": idx,
                    "id": track["id"],
                    "name": track.get("name", "Unknown Title"),
                    "artist": artist_names,
                    "album": album_name,
                    "album_image": cover_url,
                    "duration": dur_sec,
                    "duration_formatted": dur_fmt,
                    "explicit": track.get("explicit", False),
                    "isrc": isrc,
                    "uri": track.get("uri", f"spotify:track:{track['id']}"),
                    "preview_url": track.get("preview_url"),
                    "platform": "spotify",
                })
                idx += 1

            next_url = tr_data.get("next")

        # Total duration formatting
        hrs = total_duration_sec // 3600
        mins = (total_duration_sec % 3600) // 60
        if hrs > 0:
            duration_formatted = f"{hrs} hr {mins} min"
        else:
            duration_formatted = f"{mins} min"

        return {
            "id": pl["id"],
            "name": pl.get("name", "Untitled Playlist"),
            "description": pl.get("description", "") or "",
            "num_tracks": len(tracks),
            "duration": total_duration_sec,
            "duration_formatted": duration_formatted,
            "image": image_url,
            "is_user_playlist": is_user,
            "public": pl.get("public", False),
            "platform": "spotify",
            "tracks": tracks,
        }

    def create_playlist(self, title: str, description: str = "", public: bool = False) -> Dict[str, Any]:
        """Create a new playlist in Spotify for the authenticated user."""
        user = self.get_current_user()
        user_id = user["id"]

        payload = {
            "name": title.strip(),
            "description": description.strip() if description else "",
            "public": public,
        }
        resp = self._request("POST", f"/users/{user_id}/playlists", json=payload)
        data = resp.json()
        return {
            "id": data["id"],
            "name": data["name"],
            "description": data.get("description", ""),
            "num_tracks": 0,
            "duration": 0,
            "duration_formatted": "0 min",
            "image": "",
            "is_user_playlist": True,
            "public": data.get("public", False),
            "platform": "spotify",
        }

    def rename_playlist(self, playlist_id: str, new_title: str, new_description: Optional[str] = None) -> Dict[str, Any]:
        """Update playlist name and optional description."""
        payload: Dict[str, Any] = {"name": new_title.strip()}
        if new_description is not None:
            payload["description"] = new_description.strip()

        self._request("PUT", f"/playlists/{playlist_id}", json=payload)
        return {"id": playlist_id, "name": new_title.strip(), "description": new_description or ""}

    def delete_playlist(self, playlist_id: str) -> bool:
        """Unfollow/delete a Spotify playlist."""
        self._request("DELETE", f"/playlists/{playlist_id}/followers")
        return True

    # -------------------------------------------------------------------------
    # Track Manipulations
    # -------------------------------------------------------------------------

    def add_tracks(self, playlist_id: str, track_uris_or_ids: Sequence[str], position: Optional[int] = None) -> int:
        """Add tracks to playlist (batching in max 100 tracks per request)."""
        if not track_uris_or_ids:
            return 0

        # Ensure URIs have 'spotify:track:' prefix
        uris = [
            t if t.startswith("spotify:track:") else f"spotify:track:{t}"
            for t in track_uris_or_ids
        ]

        # Spotify API accepts max 100 tracks per request
        added = 0
        chunk_size = 100
        for i in range(0, len(uris), chunk_size):
            chunk = uris[i : i + chunk_size]
            payload: Dict[str, Any] = {"uris": chunk}
            if position is not None and i == 0:
                payload["position"] = position

            self._request("POST", f"/playlists/{playlist_id}/tracks", json=payload)
            added += len(chunk)

        return added

    def remove_tracks_by_indices(self, playlist_id: str, indices: Sequence[int]) -> int:
        """Remove tracks at specific playlist indices."""
        if not indices:
            return 0

        details = self.get_playlist_details(playlist_id)
        tracks = details.get("tracks", [])

        # Map indices to URIs with positions
        # Group identical URIs with their positions
        items_to_remove: Dict[str, List[int]] = {}
        for idx in indices:
            if 0 <= idx < len(tracks):
                uri = tracks[idx]["uri"]
                items_to_remove.setdefault(uri, []).append(idx)

        if not items_to_remove:
            return 0

        # Construct Spotify payload
        # Max 100 items per request
        tracks_payload = [
            {"uri": uri, "positions": pos_list}
            for uri, pos_list in items_to_remove.items()
        ]

        self._request("DELETE", f"/playlists/{playlist_id}/tracks", json={"tracks": tracks_payload})
        return len(indices)

    def reorder_tracks(self, playlist_id: str, from_index: int, to_index: int) -> bool:
        """Reorder a single track in a Spotify playlist."""
        # Spotify's 'insert_before': if moving down, target position is to_index + 1
        insert_before = to_index + 1 if from_index < to_index else to_index
        payload = {
            "range_start": from_index,
            "insert_before": insert_before,
            "range_length": 1,
        }
        self._request("PUT", f"/playlists/{playlist_id}/tracks", json=payload)
        return True

    # -------------------------------------------------------------------------
    # Catalog Search & Track Matching
    # -------------------------------------------------------------------------

    def search_track(
        self,
        isrc: Optional[str] = None,
        title: Optional[str] = None,
        artist: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        High-precision track matching:
        1. Query exact ISRC (highest accuracy)
        2. Fallback: track title + artist search
        3. Fallback: general query
        """
        # 1. Exact ISRC search
        if isrc and len(isrc.strip()) == 12:
            clean_isrc = isrc.strip()
            resp = self._request("GET", f"/search?q={urllib.parse.quote(f'isrc:{clean_isrc}')}&type=track&limit=1")
            items = resp.json().get("tracks", {}).get("items", [])
            if items:
                return self._normalize_search_item(items[0], match_type="isrc")

        # 2. Track + Artist structured search
        if title and artist:
            # Clean title (remove common extra tags like '(feat. ...)', '[Remastered]', etc.)
            clean_title = re.sub(r"\s*[\(\[][^()\[\]]*(feat|remaster|version|explicit|deluxe)[^()\[\]]*[\)\]]", "", title, flags=re.I).strip()
            clean_artist = artist.split(",")[0].split("&")[0].split("feat.")[0].strip()

            q_structured = f"track:{clean_title} artist:{clean_artist}"
            resp = self._request("GET", f"/search?q={urllib.parse.quote(q_structured)}&type=track&limit=3")
            items = resp.json().get("tracks", {}).get("items", [])
            if items:
                return self._normalize_search_item(items[0], match_type="title_artist")

        # 3. General query fallback
        if title:
            query = f"{title} {artist or ''}".strip()
            resp = self._request("GET", f"/search?q={urllib.parse.quote(query)}&type=track&limit=3")
            items = resp.json().get("tracks", {}).get("items", [])
            if items:
                return self._normalize_search_item(items[0], match_type="fuzzy")

        return None

    def _normalize_search_item(self, track: Dict[str, Any], match_type: str = "search") -> Dict[str, Any]:
        """Normalize raw Spotify track search item."""
        duration_ms = track.get("duration_ms", 0)
        dur_sec = duration_ms // 1000
        mins = dur_sec // 60
        secs = dur_sec % 60
        dur_fmt = f"{mins}:{secs:02d}"

        artists_list = track.get("artists") or []
        artist_names = ", ".join(a.get("name", "") for a in artists_list if a.get("name"))

        album = track.get("album") or {}
        album_name = album.get("name", "")
        album_imgs = album.get("images") or []
        cover_url = album_imgs[-1].get("url") if album_imgs else (album_imgs[0].get("url") if album_imgs else "")

        external_ids = track.get("external_ids") or {}
        isrc = external_ids.get("isrc")

        return {
            "id": track["id"],
            "name": track.get("name", "Unknown Title"),
            "artist": artist_names,
            "album": album_name,
            "album_image": cover_url,
            "duration": dur_sec,
            "duration_formatted": dur_fmt,
            "explicit": track.get("explicit", False),
            "isrc": isrc,
            "uri": track.get("uri", f"spotify:track:{track['id']}"),
            "preview_url": track.get("preview_url"),
            "platform": "spotify",
            "match_type": match_type,
        }

    def _normalize_string(self, s: str) -> str:
        """Normalize string for fuzzy comparison."""
        if not s:
            return ""
        s = s.lower()
        s = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", s)
        s = re.sub(r"[^\w\s]", "", s)
        return " ".join(s.split())

    def find_duplicates(self, playlist_id: str) -> Dict[str, Any]:
        """Find duplicate tracks within a Spotify playlist."""
        details = self.get_playlist_details(playlist_id)
        tracks = details.get("tracks", [])

        seen_ids: Dict[str, int] = {}
        seen_normalized: Dict[str, int] = {}
        duplicate_indices: Set[int] = set()
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for t in tracks:
            idx = t["index"]
            tid = t.get("id") or ""
            norm_key = f"{self._normalize_string(t.get('name') or '')} - {self._normalize_string(t.get('artist') or '')}"

            is_dup = False
            group_key = norm_key or tid

            if tid and tid in seen_ids:
                is_dup = True
                duplicate_indices.add(idx)
            elif tid:
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
                    if first_track:
                        first_copy = dict(first_track)
                        first_copy["is_duplicate"] = False
                        groups[group_key] = [first_copy]
                    else:
                        groups[group_key] = []
                dup_copy = dict(t)
                dup_copy["is_duplicate"] = True
                groups[group_key].append(dup_copy)

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

    def clean_duplicates(
        self, playlist_id: str, indices: Optional[Sequence[int]] = None
    ) -> Dict[str, Any]:
        """Remove duplicate tracks from a Spotify playlist.
        
        If `indices` is provided, remove only those specific indices.
        Otherwise, find all duplicates and remove them, keeping the first occurrence.
        """
        if indices is not None:
            dup_indices = sorted(set(indices))
        else:
            dup_info = self.find_duplicates(playlist_id)
            dup_indices = dup_info["duplicate_indices"]

        if not dup_indices:
            return {
                "success": True,
                "removed_count": 0,
                "message": "No duplicates selected to remove.",
            }

        self.remove_tracks_by_indices(playlist_id, dup_indices)
        return {
            "success": True,
            "removed_count": len(dup_indices),
            "message": f"Successfully removed {len(dup_indices)} duplicate track(s).",
        }
