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
    # 1. If running from local source checkout (main.py or run.sh present), store locally
    local_session = BASE_DIR / ".tidal_session.json"
    cwd_session = Path.cwd() / ".tidal_session.json"
    home_session = Path.home() / ".tidal_session.json"
    if (BASE_DIR / "main.py").exists() or (BASE_DIR / "run.sh").exists():
        SESSION_FILE = local_session
    elif cwd_session.exists():
        SESSION_FILE = cwd_session
    else:
        SESSION_FILE = home_session

DEFAULT_HOST = os.environ.get("TIDAL_WEB_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("TIDAL_WEB_PORT", "8000"))

# Spotify Session & Configuration file
_env_spotify = os.environ.get("SPOTIFY_SESSION_FILE")
if _env_spotify:
    SPOTIFY_SESSION_FILE = Path(_env_spotify).expanduser().resolve()
else:
    local_spotify = BASE_DIR / ".spotify_session.json"
    cwd_spotify = Path.cwd() / ".spotify_session.json"
    home_spotify = Path.home() / ".spotify_session.json"
    if (BASE_DIR / "main.py").exists() or (BASE_DIR / "run.sh").exists():
        SPOTIFY_SESSION_FILE = local_spotify
    elif cwd_spotify.exists():
        SPOTIFY_SESSION_FILE = cwd_spotify
    else:
        SPOTIFY_SESSION_FILE = home_spotify

SPOTIFY_DEFAULT_REDIRECT_URI = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/api/spotify/callback"

