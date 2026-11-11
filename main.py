#!/usr/bin/env python3
"""
TIDAL Playlist Manager - Main Entry Point.

Usage:
  python main.py              # Launches the modern Web UI in your default browser
  python main.py web          # Explicitly run Web UI server
  python main.py login        # CLI Device Code OAuth login
  python main.py list         # CLI list personal playlists
  python main.py show <name>  # CLI show tracks in playlist
  python main.py split <name> # CLI auto-split playlist (>99 tracks) with suffix
  python main.py --help       # View all available CLI commands
"""

import sys
from pathlib import Path

# Ensure package is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tidal_manager.cli import main

if __name__ == "__main__":
    main()
