"""FastAPI server providing REST API and static frontend for Tidal Playlist Manager."""

import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tidal_manager.client import TidalAuthError, TidalClient, TidalManagerError
from tidal_manager.config import BASE_DIR
from tidal_manager.local_matcher import match_playlist_against_local, scan_local_directory
from tidal_manager.spotify_client import SpotifyAuthError, SpotifyClient, SpotifyError

app = FastAPI(
    title="TIDAL & Spotify Playlist Manager API",
    version="1.3.0",
    description="REST API for managing Tidal and Spotify playlists, moving/copying tracks within and across platforms, splitting, merging, duplicates cleaning, and catalog search.",
)

# Allow CORS for development if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global client singletons
client = TidalClient()
spotify_client = SpotifyClient()

# -----------------------------------------------------------------------------
# Pydantic Request / Response Models
# -----------------------------------------------------------------------------

class CreatePlaylistRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Playlist title")
    description: Optional[str] = Field("", description="Optional playlist description")


class RenamePlaylistRequest(BaseModel):
    name: str = Field(..., min_length=1, description="New playlist title")
    description: Optional[str] = Field(None, description="Optional updated description")


class TrackOperationRequest(BaseModel):
    from_id: str = Field(..., description="Source playlist ID")
    to_id: str = Field(..., description="Destination playlist ID")
    indices: Optional[List[int]] = Field(None, description="List of track indices to copy/move")
    track_ids: Optional[List[str]] = Field(None, description="List of track IDs to copy/move")
    allow_duplicates: Optional[bool] = Field(True, description="Whether to allow duplicate tracks")


class RemoveTracksRequest(BaseModel):
    indices: Optional[List[int]] = Field(None, description="Track indices to remove")
    track_ids: Optional[List[str]] = Field(None, description="Track IDs to remove")


class SplitPlaylistRequest(BaseModel):
    max_tracks: Optional[int] = Field(99, ge=1, le=1000, description="Max tracks per playlist chunk")
    rename_original: Optional[bool] = Field(True, description="Whether to rename original playlist to '[Name] 1'")


class MergePlaylistsRequest(BaseModel):
    source_ids: List[str] = Field(..., min_items=1, description="List of source playlist IDs to merge")
    target_title: str = Field(..., min_length=1, description="Title of merged playlist")
    target_description: Optional[str] = Field("", description="Description of merged playlist")
    deduplicate: Optional[bool] = Field(True, description="Remove duplicate tracks during merge")


class SortPlaylistRequest(BaseModel):
    sort_by: str = Field("title", description="Sort by 'title', 'artist', 'album', or 'duration'")
    ascending: Optional[bool] = Field(True, description="Sort ascending (A-Z) or descending (Z-A)")


class ReorderTrackRequest(BaseModel):
    from_index: int = Field(..., ge=0, description="Current track index (0-based)")
    to_index: int = Field(..., ge=0, description="Target track index (0-based)")


class ImportPlaylistRequest(BaseModel):
    title: Optional[str] = Field(None, description="Playlist title override")
    content: str = Field(..., description="Raw text of JSON, CSV, or M3U file")
    format_type: Optional[str] = Field("auto", description="'auto', 'json', 'csv', or 'm3u'")
    description: Optional[str] = Field("Imported via TIDAL Playlist Manager", description="Playlist description")
    target_playlist_id: Optional[str] = Field(None, description="Target playlist ID to append tracks to")


class SpotifyConfigRequest(BaseModel):
    client_id: str = Field(..., min_length=5, description="Spotify App Client ID")
    client_secret: str = Field(..., min_length=5, description="Spotify App Client Secret")
    redirect_uri: Optional[str] = Field(None, description="Optional custom OAuth redirect URI")


class MatchLocalDirectoryRequest(BaseModel):
    directory_path: str = Field(..., min_length=1, description="Local folder path to recursively scan")
    max_files: Optional[int] = Field(50000, ge=1, le=200000, description="Max audio files to scan")


class RemoveLocalTracksRequest(BaseModel):
    indices: List[int] = Field(..., min_items=1, description="Track indices to remove from playlist")



class UniversalTransferRequest(BaseModel):
    from_platform: str = Field(..., description="'tidal' or 'spotify'")
    to_platform: str = Field(..., description="'tidal' or 'spotify'")
    from_playlist_id: str = Field(..., description="Source playlist ID")
    to_playlist_id: str = Field(..., description="Destination playlist ID")
    indices: List[int] = Field(..., min_items=1, description="Track indices in source playlist")
    is_move: Optional[bool] = Field(False, description="Whether to remove tracks from source after copy")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def ensure_authenticated():
    if not client.is_logged_in():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with Tidal. Please log in first.",
        )


def get_platform_client(platform: str):
    """Retrieve the client instance for specified platform with auth check."""
    p = (platform or "").lower().strip()
    if p == "tidal":
        if not client.is_logged_in():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in to TIDAL.")
        return client
    elif p == "spotify":
        if not spotify_client.is_authenticated():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in to Spotify.")
        return spotify_client
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform '{platform}'. Choose 'tidal' or 'spotify'.")



# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------

@app.get("/api/auth/status")
def get_auth_status():
    """Get the current authentication status and user details."""
    logged_in = client.is_logged_in()
    user_info = client.get_user_info() if logged_in else {"logged_in": False}
    return {
        "logged_in": logged_in,
        "user": user_info,
    }


@app.post("/api/auth/start")
def start_auth():
    """Start the OAuth2 Device Authorization login flow."""
    try:
        return client.start_oauth_login()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start device login: {e}")


@app.get("/api/auth/poll")
def poll_auth():
    """Poll the status of the OAuth2 device authorization."""
    try:
        return client.poll_oauth_login()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/logout")
def logout():
    """Log out and remove local credentials."""
    client.logout()
    return {"success": True, "message": "Logged out successfully"}


# -----------------------------------------------------------------------------
# Spotify Authentication Routes
# -----------------------------------------------------------------------------

@app.get("/api/spotify/status")
def get_spotify_status():
    """Get the current Spotify configuration and authentication status."""
    configured = spotify_client.is_configured()
    authenticated = spotify_client.is_authenticated()
    user_info = None
    error_detail = None

    if authenticated:
        try:
            user_info = spotify_client.get_current_user()
        except Exception as e:
            err_msg = str(e)
            logger.warning(f"Failed to fetch Spotify user: {err_msg}")
            authenticated = False
            if "Active premium subscription required" in err_msg or "403" in err_msg:
                error_detail = "Active Spotify Premium subscription required for the owner of the Spotify Developer App (Spotify API policy)."
            else:
                error_detail = err_msg

    return {
        "configured": configured,
        "authenticated": authenticated,
        "client_id": spotify_client.client_id,
        "redirect_uri": spotify_client.redirect_uri,
        "user": user_info,
        "error": error_detail,
    }


@app.post("/api/spotify/config")
def set_spotify_config(payload: SpotifyConfigRequest):
    """Save Spotify Client ID and Client Secret."""
    try:
        spotify_client.set_config(
            client_id=payload.client_id,
            client_secret=payload.client_secret,
            redirect_uri=payload.redirect_uri,
        )
        return {"success": True, "configured": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/spotify/auth-url")
def get_spotify_auth_url():
    """Generate the Spotify OAuth authorization URL."""
    try:
        url = spotify_client.get_auth_url()
        return {"auth_url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/spotify/callback")
def spotify_callback(code: Optional[str] = None, error: Optional[str] = None):
    """Handle the OAuth2 callback from Spotify."""
    if error:
        html = f"""
        <html>
        <head><title>Spotify Connection Error</title></head>
        <body style="background:#121212;color:#fff;font-family:sans-serif;padding:40px;text-align:center;">
          <h2 style="color:#ff4444;">Spotify Connection Denied</h2>
          <p>{error}</p>
          <button onclick="window.close()" style="background:#333;color:#fff;padding:10px 20px;border:none;border-radius:4px;cursor:pointer;">Close Window</button>
        </body>
        </html>
        """
        return Response(content=html, media_type="text/html")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing.")

    try:
        spotify_client.exchange_code(code)
        html = """
        <html>
        <head><title>Spotify Connected</title></head>
        <body style="background:#121212;color:#fff;font-family:sans-serif;padding:40px;text-align:center;">
          <h2 style="color:#1DB954;">Spotify Connected Successfully!</h2>
          <p>You can close this window now.</p>
          <script>
            try {
              if (window.opener) {
                window.opener.postMessage({ type: 'SPOTIFY_AUTH_SUCCESS' }, '*');
                window.close();
              } else {
                setTimeout(function() { window.location.href = '/?spotify_connected=1'; }, 1500);
              }
            } catch (e) {
              window.location.href = '/?spotify_connected=1';
            }
          </script>
        </body>
        </html>
        """
        return Response(content=html, media_type="text/html")
    except Exception as e:
        html = f"""
        <html>
        <head><title>Spotify Connection Error</title></head>
        <body style="background:#121212;color:#fff;font-family:sans-serif;padding:40px;text-align:center;">
          <h2 style="color:#ff4444;">Spotify Authentication Failed</h2>
          <p>{e}</p>
          <button onclick="window.close()" style="background:#333;color:#fff;padding:10px 20px;border:none;border-radius:4px;cursor:pointer;">Close Window</button>
        </body>
        </html>
        """
        return Response(content=html, media_type="text/html")


@app.post("/api/spotify/logout")
def spotify_logout():
    """Disconnect Spotify account."""
    spotify_client.logout()
    return {"success": True, "message": "Spotify account disconnected."}



# -----------------------------------------------------------------------------
# Platform-Agnostic Playlist CRUD Routes (/api/{platform}/playlists)
# -----------------------------------------------------------------------------

@app.get("/api/{platform}/playlists")
def list_platform_playlists(platform: str):
    """List playlists from specified platform ('tidal' or 'spotify')."""
    target_client = get_platform_client(platform)
    try:
        return target_client.list_playlists()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/{platform}/playlists")
def create_platform_playlist(platform: str, payload: CreatePlaylistRequest):
    """Create a new playlist on specified platform ('tidal' or 'spotify')."""
    target_client = get_platform_client(platform)
    try:
        return target_client.create_playlist(title=payload.name, description=payload.description or "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/{platform}/playlists/{playlist_id}")
def get_platform_playlist_details(platform: str, playlist_id: str):
    """Get playlist details and tracks from specified platform ('tidal' or 'spotify')."""
    target_client = get_platform_client(platform)
    try:
        return target_client.get_playlist_details(playlist_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/api/{platform}/playlists/{playlist_id}")
@app.patch("/api/{platform}/playlists/{playlist_id}")
def rename_platform_playlist(platform: str, playlist_id: str, payload: RenamePlaylistRequest):
    """Rename a playlist on specified platform ('tidal' or 'spotify')."""
    target_client = get_platform_client(platform)
    try:
        return target_client.rename_playlist(
            playlist_id=playlist_id,
            new_title=payload.name,
            new_description=payload.description,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/{platform}/playlists/{playlist_id}")
def delete_platform_playlist(platform: str, playlist_id: str):
    """Delete a playlist on specified platform ('tidal' or 'spotify')."""
    target_client = get_platform_client(platform)
    try:
        target_client.delete_playlist(playlist_id)
        return {"success": True, "message": f"Playlist {playlist_id} deleted."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/{platform}/playlists/{playlist_id}/reorder")
def reorder_platform_track(platform: str, playlist_id: str, payload: ReorderTrackRequest):
    """Reorder track within playlist on specified platform."""
    target_client = get_platform_client(platform)
    try:
        if platform.lower() == "spotify":
            ok = target_client.reorder_tracks(playlist_id, payload.from_index, payload.to_index)
        else:
            ok = target_client.reorder_track(playlist_id, payload.from_index, payload.to_index)
        return {"success": ok, "message": f"Track moved from {payload.from_index} to {payload.to_index}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/{platform}/playlists/{playlist_id}/tracks")
def remove_platform_tracks(platform: str, playlist_id: str, payload: RemoveTracksRequest):
    """Remove tracks from playlist on specified platform."""
    target_client = get_platform_client(platform)
    try:
        if payload.indices is not None and len(payload.indices) > 0:
            removed = target_client.remove_tracks_by_indices(playlist_id, payload.indices)
        elif payload.track_ids is not None and len(payload.track_ids) > 0:
            if hasattr(target_client, "remove_tracks_by_ids"):
                removed = target_client.remove_tracks_by_ids(playlist_id, payload.track_ids)
            else:
                raise HTTPException(status_code=400, detail="Removal by ID not supported on this platform.")
        else:
            raise HTTPException(status_code=400, detail="Must provide indices or track_ids to remove")
        return {"success": True, "removed_count": removed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/{platform}/playlists/{playlist_id}/match-local")
def match_platform_playlist_local(platform: str, playlist_id: str, payload: MatchLocalDirectoryRequest):
    """Scan local directory and find playlist tracks that are locally available."""
    target_client = get_platform_client(platform)
    try:
        details = target_client.get_playlist_details(playlist_id)
        tracks = details.get("tracks", [])
        if not tracks:
            return {
                "scanned_files_count": 0,
                "total_playlist_tracks": 0,
                "matched_count": 0,
                "matches": [],
            }

        local_files = scan_local_directory(payload.directory_path, max_files=payload.max_files or 50000)
        match_result = match_playlist_against_local(tracks, local_files)
        return match_result
    except (FileNotFoundError, NotADirectoryError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/{platform}/playlists/{playlist_id}/remove-local")
def remove_platform_playlist_local(platform: str, playlist_id: str, payload: RemoveLocalTracksRequest):
    """Remove locally matched tracks by their indices from the playlist."""
    target_client = get_platform_client(platform)
    try:
        removed_count = target_client.remove_tracks_by_indices(playlist_id, payload.indices)
        return {"success": True, "removed_count": removed_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# -----------------------------------------------------------------------------
# Universal Cross-Platform Transfer Route
# -----------------------------------------------------------------------------

@app.post("/api/transfer/universal")
def universal_transfer(payload: UniversalTransferRequest):
    """
    Universal track transfer:
    - TIDAL -> TIDAL
    - Spotify -> Spotify
    - TIDAL -> Spotify
    - Spotify -> TIDAL
    Supports matching via ISRC (primary) and Title + Artist (secondary).
    """
    try:
        from_p = payload.from_platform.lower().strip()
        to_p = payload.to_platform.lower().strip()
        src_client = get_platform_client(from_p)
        dst_client = get_platform_client(to_p)

        src_details = src_client.get_playlist_details(payload.from_playlist_id)
        dst_details = dst_client.get_playlist_details(payload.to_playlist_id)

        src_tracks = src_details.get("tracks", [])
        selected_tracks = [src_tracks[i] for i in payload.indices if 0 <= i < len(src_tracks)]
        if not selected_tracks:
            raise HTTPException(status_code=400, detail="No valid tracks selected to transfer.")

        # 1. TIDAL -> TIDAL
        if from_p == "tidal" and to_p == "tidal":
            if payload.is_move:
                res = client.move_tracks(
                    from_playlist_id=payload.from_playlist_id,
                    to_playlist_id=payload.to_playlist_id,
                    indices=payload.indices,
                )
            else:
                res = client.copy_tracks(
                    from_playlist_id=payload.from_playlist_id,
                    to_playlist_id=payload.to_playlist_id,
                    indices=payload.indices,
                )
            return {
                "success": True,
                "transferred_count": len(selected_tracks),
                "unmatched_count": 0,
                "unmatched_tracks": [],
                "message": f"Successfully {'moved' if payload.is_move else 'copied'} {len(selected_tracks)} tracks to '{dst_details.get('name')}'!",
            }

        # 2. Spotify -> Spotify
        if from_p == "spotify" and to_p == "spotify":
            uris = [t["uri"] for t in selected_tracks]
            spotify_client.add_tracks(payload.to_playlist_id, uris)
            if payload.is_move:
                spotify_client.remove_tracks_by_indices(payload.from_playlist_id, payload.indices)
            return {
                "success": True,
                "transferred_count": len(selected_tracks),
                "unmatched_count": 0,
                "unmatched_tracks": [],
                "message": f"Successfully {'moved' if payload.is_move else 'copied'} {len(selected_tracks)} tracks to '{dst_details.get('name')}'!",
            }

        # 3. TIDAL -> Spotify
        if from_p == "tidal" and to_p == "spotify":
            matched_uris = []
            unmatched = []
            for t in selected_tracks:
                m = spotify_client.search_track(isrc=t.get("isrc"), title=t.get("name"), artist=t.get("artist"))
                if m:
                    matched_uris.append(m["uri"])
                else:
                    unmatched.append(f"{t.get('name')} - {t.get('artist')}")

            if matched_uris:
                spotify_client.add_tracks(payload.to_playlist_id, matched_uris)
                if payload.is_move:
                    client.remove_tracks_by_indices(payload.from_playlist_id, payload.indices)

            msg = f"Transferred {len(matched_uris)} of {len(selected_tracks)} tracks to Spotify playlist '{dst_details.get('name')}'."
            if unmatched:
                msg += f" ({len(unmatched)} unmatched)"

            return {
                "success": bool(matched_uris),
                "transferred_count": len(matched_uris),
                "unmatched_count": len(unmatched),
                "unmatched_tracks": unmatched,
                "message": msg,
            }

        # 4. Spotify -> TIDAL
        if from_p == "spotify" and to_p == "tidal":
            matched_ids = []
            unmatched = []
            for t in selected_tracks:
                m = client.search_track(isrc=t.get("isrc"), title=t.get("name"), artist=t.get("artist"))
                if m:
                    matched_ids.append(m["id"])
                else:
                    unmatched.append(f"{t.get('name')} - {t.get('artist')}")

            if matched_ids:
                client.add_tracks(payload.to_playlist_id, matched_ids)
                if payload.is_move:
                    spotify_client.remove_tracks_by_indices(payload.from_playlist_id, payload.indices)

            msg = f"Transferred {len(matched_ids)} of {len(selected_tracks)} tracks to TIDAL playlist '{dst_details.get('name')}'."
            if unmatched:
                msg += f" ({len(unmatched)} unmatched)"

            return {
                "success": bool(matched_ids),
                "transferred_count": len(matched_ids),
                "unmatched_count": len(unmatched),
                "unmatched_tracks": unmatched,
                "message": msg,
            }

        raise HTTPException(status_code=400, detail=f"Unsupported transfer from {from_p} to {to_p}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# Playlist Basic CRUD Routes
# -----------------------------------------------------------------------------

@app.get("/api/playlists")
def list_playlists():
    """List all personal playlists."""
    ensure_authenticated()
    try:
        return client.list_playlists()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/playlists")
def create_playlist(payload: CreatePlaylistRequest):
    """Create a new playlist."""
    ensure_authenticated()
    try:
        return client.create_playlist(title=payload.name, description=payload.description or "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/playlists/{playlist_id}")
def get_playlist_details(playlist_id: str):
    """Get playlist details and full list of tracks."""
    ensure_authenticated()
    try:
        return client.get_playlist_details(playlist_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/api/playlists/{playlist_id}")
@app.patch("/api/playlists/{playlist_id}")
def rename_playlist(playlist_id: str, payload: RenamePlaylistRequest):
    """Rename a playlist and/or update its description."""
    ensure_authenticated()
    try:
        return client.rename_playlist(
            playlist_id=playlist_id,
            new_title=payload.name,
            new_description=payload.description,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/playlists/{playlist_id}")
def delete_playlist(playlist_id: str):
    """Delete a user playlist."""
    ensure_authenticated()
    try:
        client.delete_playlist(playlist_id)
        return {"success": True, "message": f"Playlist {playlist_id} deleted."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# Track Operations Routes (Copy, Move, Remove, Split)
# -----------------------------------------------------------------------------

@app.post("/api/playlists/copy")
def copy_tracks(payload: TrackOperationRequest):
    """Copy selected tracks from one playlist to another."""
    ensure_authenticated()
    try:
        return client.copy_tracks(
            from_playlist_id=payload.from_id,
            to_playlist_id=payload.to_id,
            indices=payload.indices,
            track_ids=payload.track_ids,
            allow_duplicates=payload.allow_duplicates if payload.allow_duplicates is not None else True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/playlists/move")
def move_tracks(payload: TrackOperationRequest):
    """Move selected tracks from one playlist to another."""
    ensure_authenticated()
    try:
        return client.move_tracks(
            from_playlist_id=payload.from_id,
            to_playlist_id=payload.to_id,
            indices=payload.indices,
            track_ids=payload.track_ids,
            allow_duplicates=payload.allow_duplicates if payload.allow_duplicates is not None else True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/playlists/{playlist_id}/tracks")
def remove_tracks(playlist_id: str, payload: RemoveTracksRequest):
    """Remove tracks by indices or track IDs."""
    ensure_authenticated()
    try:
        if payload.indices is not None and len(payload.indices) > 0:
            client.remove_tracks_by_indices(playlist_id, payload.indices)
        elif payload.track_ids is not None and len(payload.track_ids) > 0:
            client.remove_tracks_by_ids(playlist_id, payload.track_ids)
        else:
            raise HTTPException(status_code=400, detail="Must provide indices or track_ids")
        return {"success": True, "message": "Tracks removed."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/playlists/{playlist_id}/match-local")
def match_playlist_local(playlist_id: str, payload: MatchLocalDirectoryRequest):
    """Legacy route: Match local tracks against TIDAL playlist."""
    return match_platform_playlist_local("tidal", playlist_id, payload)


@app.post("/api/playlists/{playlist_id}/remove-local")
def remove_playlist_local(playlist_id: str, payload: RemoveLocalTracksRequest):
    """Legacy route: Remove locally available tracks from TIDAL playlist."""
    return remove_platform_playlist_local("tidal", playlist_id, payload)



@app.post("/api/playlists/{playlist_id}/split")
def split_playlist(playlist_id: str, payload: SplitPlaylistRequest):
    """Split a playlist into chunks of max 99 tracks with numerical suffixes."""
    ensure_authenticated()
    try:
        max_tracks = payload.max_tracks or 99
        rename_original = payload.rename_original if payload.rename_original is not None else True
        result = client.split_playlist(
            playlist_id=playlist_id,
            max_tracks=max_tracks,
            rename_original=rename_original,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# 1. Duplicate Finder & Cleaner Routes
# -----------------------------------------------------------------------------

@app.get("/api/playlists/{playlist_id}/duplicates")
def get_duplicates(playlist_id: str):
    """Find duplicate tracks in a playlist."""
    ensure_authenticated()
    try:
        return client.find_duplicates(playlist_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/playlists/{playlist_id}/duplicates/clean")
def clean_duplicates(playlist_id: str):
    """Remove duplicate tracks in a playlist, keeping the first occurrence."""
    ensure_authenticated()
    try:
        return client.clean_duplicates(playlist_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# 2. Backup & Export / Import Routes
# -----------------------------------------------------------------------------

@app.get("/api/playlists/{playlist_id}/export")
def export_playlist(playlist_id: str, format: str = Query("json", pattern="^(json|csv|m3u)$")):
    """Download a playlist backup as JSON, CSV, or M3U."""
    ensure_authenticated()
    try:
        content, mime, filename = client.export_playlist(playlist_id, format_type=format)
        return Response(
            content=content,
            media_type=mime,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/playlists/import")
def import_playlist(payload: ImportPlaylistRequest):
    """Import a playlist from uploaded JSON, CSV, or M3U content."""
    ensure_authenticated()
    try:
        return client.import_playlist(
            title=payload.title,
            file_content=payload.content,
            format_type=payload.format_type or "auto",
            description=payload.description or "Imported via TIDAL Playlist Manager",
            target_playlist_id=payload.target_playlist_id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# 3. Merge & Shuffle Routes
# -----------------------------------------------------------------------------

@app.post("/api/playlists/merge")
def merge_playlists(payload: MergePlaylistsRequest):
    """Merge multiple playlists into a new playlist."""
    ensure_authenticated()
    try:
        return client.merge_playlists(
            source_ids=payload.source_ids,
            target_title=payload.target_title,
            target_description=payload.target_description or "",
            deduplicate=payload.deduplicate if payload.deduplicate is not None else True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/playlists/{playlist_id}/shuffle")
def shuffle_playlist(playlist_id: str):
    """Shuffle playlist tracks in random cloud order."""
    ensure_authenticated()
    try:
        return client.shuffle_playlist(playlist_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# 4. Sorting & Reordering Routes
# -----------------------------------------------------------------------------

@app.post("/api/playlists/{playlist_id}/reorder")
def reorder_track(playlist_id: str, payload: ReorderTrackRequest):
    """Reorder a track within a playlist by moving it from from_index to to_index."""
    ensure_authenticated()
    try:
        ok = client.reorder_track(playlist_id, payload.from_index, payload.to_index)
        return {"success": ok, "message": f"Track moved from index {payload.from_index} to {payload.to_index}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/playlists/{playlist_id}/sort")
def sort_playlist(playlist_id: str, payload: SortPlaylistRequest):
    """Permanently sort playlist on TIDAL."""
    ensure_authenticated()
    try:
        return client.reorder_playlist_sorted(
            playlist_id=playlist_id,
            sort_by=payload.sort_by,
            ascending=payload.ascending if payload.ascending is not None else True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# 5. Audio Preview & 7. Catalog Search Routes
# -----------------------------------------------------------------------------

@app.get("/api/search")
def search_catalog(q: str = Query(..., min_length=1), limit: int = Query(30, ge=1, le=100)):
    """Search TIDAL catalog for tracks."""
    ensure_authenticated()
    try:
        return client.search_catalog(query=q, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/tracks/{track_id}/preview")
def get_track_preview(track_id: str):
    """Get direct audio stream URL or preview link for a track."""
    ensure_authenticated()
    try:
        return client.get_track_preview(track_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# Static Frontend Serving
# -----------------------------------------------------------------------------

import sys

if hasattr(sys, "_MEIPASS"):
    static_dir = Path(sys._MEIPASS) / "tidal_manager" / "static"
    if not static_dir.exists():
        static_dir = Path(sys._MEIPASS) / "static"
else:
    static_dir = Path(__file__).resolve().parent / "static"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def serve_frontend():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not found"}
