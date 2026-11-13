"""Configuration and path management for Tidal Playlist Manager."""

import os
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Session storage file
# Can be customized via TIDAL_SESSION_FILE environment variable
_env_session = os.environ.get("TIDAL_SESSION_FILE")
if _env_session:
    SESSION_FILE = Path(_env_session).expanduser().resolve()
else:
    # Default to current workspace directory first, fallback to home directory
    local_session = BASE_DIR / ".tidal_session.json"
    SESSION_FILE = local_session

DEFAULT_HOST = os.environ.get("TIDAL_WEB_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("TIDAL_WEB_PORT", "8000"))

# Spotify Session & Configuration file
_env_spotify = os.environ.get("SPOTIFY_SESSION_FILE")
if _env_spotify:
    SPOTIFY_SESSION_FILE = Path(_env_spotify).expanduser().resolve()
else:
    SPOTIFY_SESSION_FILE = BASE_DIR / ".spotify_session.json"

SPOTIFY_DEFAULT_REDIRECT_URI = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/api/spotify/callback"

