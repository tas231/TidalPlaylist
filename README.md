# TIDAL Playlist Manager 🎵

A powerful, modern TIDAL playlist management application featuring a dual-pane **Web UI** and a comprehensive **CLI**.

Built with Python, FastAPI, and `tidalapi`, with zero build-step requirements.

---

## ✨ Features

- 🎧 **Read Playlists**: View all your personal TIDAL playlists, tracklists, album covers, explicit badges, track durations, and playlist total running time.
- ➕ **Create Playlists**: Create new playlists with custom titles and descriptions.
- ✏️ **Rename Playlists**: Quickly edit and rename existing playlists.
- 📋 **Copy Tracks**: Select individual or multiple tracks and copy them from one playlist to another.
- 🚚 **Move Tracks**: Seamlessly move tracks between playlists (adds to destination and deletes from source).
- ⚡ **Auto-Split Playlists (> 99 Tracks)**:
  - Automatically splits any playlist that has more than 99 tracks into multiple playlists of maximum 99 tracks each.
  - Automatically names them with numerical suffixes: `[Playlist Name] 1`, `[Playlist Name] 2`, `[Playlist Name] 3`, etc.
  - Automatically moves excess tracks from the original playlist into the newly created suffix playlists.
- 🖥️ **Dual-Pane Web Interface**: Side-by-side playlist browser with track search, multi-selection, transfer buttons, and instant feedback.
- ⌨️ **Full Command-Line Interface (CLI)**: Scriptable terminal commands for every operation.
- 🔐 **Secure TIDAL OAuth2 Authentication**: Authenticates via TIDAL's official Device Code Authorization Grant. Your password is never stored or transmitted locally. Sessions are persisted and refreshed automatically.

---

## 🚀 Quick Start

### 1. Launch the Web Application

Simply run:

```bash
./run.sh
```

Or with python:

```bash
python3 main.py
```

This will automatically start the local web server at `http://127.0.0.1:8000` and open it in your browser.

### 2. Connect your TIDAL Account

1. Click **Connect with TIDAL** in the web app or run:
   ```bash
   ./run.sh login
   ```
2. A verification code and link will be displayed (e.g. `https://link.tidal.com/XXXXX`).
3. Open the link in your browser, log in to your TIDAL account, and approve access.
4. The application will detect authorization automatically and display your playlists!

---

## ⚡ Auto-Split Feature (Max 99 Tracks)

When a playlist exceeds 99 tracks (common for car media systems, DJ hardware, or specific CD/device limitations):

### In the Web UI:
1. Select the playlist in Panel A or Panel B.
2. If it has > 99 tracks, the **⚡ Split (>99)** button is highlighted.
3. Click **⚡ Split (>99)** to open the split dialog.
4. Review the plan:
   - **Part 1**: Original playlist renamed to `[Name] 1` (keeps tracks 1 to 99).
   - **Part 2**: New playlist created as `[Name] 2` (receives tracks 100 to 198).
   - **Part 3**: New playlist created as `[Name] 3` (receives tracks 199 to end).
5. Click **Start Auto-Split**. The playlists are created and tracks are moved automatically. Both parts are loaded side-by-side so you can review them immediately!

### In the CLI:
```bash
# Split by playlist name or ID
./run.sh split "My Road Trip"

# Customize max track count if desired (default 99):
./run.sh split "My Road Trip" --max-tracks 50

# Keep original playlist name without adding suffix '1':
./run.sh split "My Road Trip" --no-rename
```

---

## 🛠️ CLI Reference

| Command | Description | Example |
|---|---|---|
| `web` | Start the Web UI server | `./run.sh web --port 8080` |
| `login` | Authenticate with TIDAL via OAuth | `./run.sh login` |
| `status` | Check authentication status | `./run.sh status` |
| `logout` | Log out and delete stored session | `./run.sh logout` |
| `list` | List all user playlists | `./run.sh list` |
| `show <playlist>` | View tracks in a playlist | `./run.sh show "Chill Vibes"` |
| `create <title>` | Create a new playlist | `./run.sh create "Workout 2026" -d "Upbeat tracks"` |
| `rename <pl> <new_title>` | Rename an existing playlist | `./run.sh rename "Workout" "Gym Bangers"` |
| `delete-playlist <pl>` | Delete a playlist | `./run.sh delete-playlist "Old Mix" -y` |
| `copy` | Copy tracks between playlists | `./run.sh copy --from "Pop" --to "Best Of" --indices 0,1,2-5` |
| `move` | Move tracks between playlists | `./run.sh move --from "Inbox" --to "Favorites" --indices 0,3` |
| `split <playlist>` | Auto-split playlist (>99 tracks) | `./run.sh split "Massive Library"` |

---

## 📂 Project Structure

```
TidalPlaylist/
├── main.py                  # CLI and Web UI entry point
├── run.sh                   # One-click startup script
├── pyproject.toml           # Project dependencies & package metadata
├── tidal_manager/
│   ├── client.py            # TIDAL API client, OAuth, playlist & track logic
│   ├── server.py            # FastAPI REST backend & static file router
│   ├── cli.py               # CLI command parsers and table output
│   ├── config.py            # Configuration & session file path
│   └── static/              # Modern frontend
│       ├── index.html       # Dual-pane UI layout & modals
│       ├── app.js           # Multi-select, transfers, splitting, and live filters
│       └── style.css        # TIDAL dark aesthetic & animations
└── tests/
    ├── test_client.py       # Client unit tests & splitting boundary tests
    └── test_api.py          # FastAPI REST endpoint integration tests
```

---

## 🧪 Running Tests

To run the full unit and integration test suite:

```bash
.venv/bin/python3 -m unittest discover -s tests
```
