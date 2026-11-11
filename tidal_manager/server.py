"""FastAPI server providing REST API and static frontend for Tidal Playlist Manager."""

import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tidal_manager.client import TidalAuthError, TidalClient, TidalManagerError
from tidal_manager.config import BASE_DIR

app = FastAPI(
    title="TIDAL Playlist Manager API",
    version="1.1.0",
    description="REST API for managing Tidal playlists, moving/copying tracks, splitting, merging, duplicates cleaning, and catalog search.",
)

# Allow CORS for development if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global client singleton
client = TidalClient()

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


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def ensure_authenticated():
    if not client.is_logged_in():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with Tidal. Please log in first.",
        )


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

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def serve_frontend():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not found"}
