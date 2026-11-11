"""FastAPI server providing REST API and static frontend for Tidal Playlist Manager."""

import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tidal_manager.client import TidalAuthError, TidalClient, TidalManagerError
from tidal_manager.config import BASE_DIR

app = FastAPI(
    title="TIDAL Playlist Manager API",
    version="1.0.0",
    description="REST API for managing Tidal playlists, moving/copying tracks, and splitting playlists.",
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
# Playlist Routes
# -----------------------------------------------------------------------------

def ensure_authenticated():
    if not client.is_logged_in():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with Tidal. Please log in first.",
        )


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
    """Move selected tracks from one playlist to another (adds to destination, removes from source)."""
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
        if payload.indices:
            client.remove_tracks_by_indices(playlist_id, payload.indices)
        elif payload.track_ids:
            client.remove_tracks_by_ids(playlist_id, payload.track_ids)
        else:
            raise HTTPException(status_code=400, detail="Must provide indices or track_ids")
        return {"success": True, "message": "Tracks removed."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/playlists/{playlist_id}/split")
def split_playlist(playlist_id: str, payload: SplitPlaylistRequest):
    """
    Split a playlist with > 99 tracks into chunks of max 99 tracks,
    creating playlists with suffix 1, 2, 3... and moving tracks.
    """
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
