# TIDAL Playlist Manager 🎵

A powerful, modern TIDAL playlist management application featuring a dual-pane **Web UI** and a comprehensive **CLI**.

Built with Python, FastAPI, and `tidalapi`, with zero build-step requirements.

---

## ✨ Features

- 🎧 **Read Playlists**: View all personal TIDAL playlists, tracklists, album covers, explicit badges, durations, and total running time.
- ➕ **Create & Rename**: Add new playlists with descriptions or rename existing ones in-place.
- 📋 **Copy & Move Tracks**: Copy or move selected tracks between playlists with multi-selection.
- ⚡ **Auto-Split Playlists (> 99 Tracks)**:
  - Automatically splits any playlist with > 99 tracks into chunks of max 99 tracks.
  - Automatically names them with numerical suffixes: `[Name] 1`, `[Name] 2`, `[Name] 3`...
  - Moves excess tracks seamlessly into the new suffix playlists.
- 🔍 **Duplicate Finder & Cleaner**:
  - Detects duplicate tracks (by exact TIDAL ID and fuzzy normalized Title + Artist matching).
  - Highlights duplicates with warning badges and offers a 1-click duplicate cleaner (keeping the earliest added song).
- 💾 **Backup & Export / Import**:
  - Export playlists directly as **JSON** (full metadata), **CSV** (for spreadsheets or transfer tools), or **M3U8** (for media players / DJ software).
  - Import playlists from JSON, CSV, or M3U files, automatically recreating them on TIDAL.
- 🔀 **Playlist Merge & Cloud Shuffle**:
  - Merge multiple playlists into a unified master playlist (with optional automatic deduplication).
  - True cloud shuffle: randomize a playlist's order permanently on TIDAL.
- 📊 **Sorting & Ordering**:
  - Sort tracks by Title, Artist, Album, or Duration in ascending or descending order.
  - One-click **"Save Order"** to make the sorted order permanent on TIDAL.
- 🎧 **Audio Preview Player**:
  - Play button on every track thumbnail with a sticky bottom preview bar, scrub bar, and 1-click fallback to the TIDAL web player.
- 🖱️ **Drag & Drop**:
  - Drag songs directly from Panel A to Panel B (and vice-versa) to copy or move them.
- 🔎 **Integrated TIDAL Search**:
  - Search the full TIDAL catalog across all artists, albums, and tracks directly within the app (shortcut: `Cmd+K` or `Ctrl+K`), with instant "+ Add to Panel A" / "+ Add to Panel B" buttons.
- 🔐 **Secure TIDAL OAuth2 Authentication**:
  - Connects using TIDAL's official Device Code authorization (`link.tidal.com`). No password stored locally. Sessions are persisted and refreshed automatically.

---

## 🚀 Quick Start

### 1. Launch on Mac

In Finder, simply **double-click** either:
- **`Start.command`** (Recommended for Mac)
- or **`Tidal Playlist Manager.app`**

Or in Terminal:
```bash
./run.sh
```

The local web server starts and your browser will open automatically at:
👉 **`http://127.0.0.1:8000`**

### 2. Connect your TIDAL Account

1. Click **Connect with TIDAL**.
2. Click the authorization link to approve the code in your browser.
3. Once approved, the manager will instantly load your playlists side-by-side!

---

## 🛠️ CLI Reference

| Command | Description | Example |
|---|---|---|
| `web` | Start the Web UI server | `./run.sh web --port 8000` |
| `login` | Authenticate with TIDAL via OAuth | `./run.sh login` |
| `status` | Check authentication status | `./run.sh status` |
| `logout` | Log out and delete stored session | `./run.sh logout` |
| `list` | List all user playlists | `./run.sh list` |
| `show <pl>` | View tracks in a playlist | `./run.sh show "Chill Vibes"` |
| `create <title>` | Create a new playlist | `./run.sh create "Workout" -d "High energy"` |
| `rename <pl> <title>` | Rename an existing playlist | `./run.sh rename "Workout" "Gym Bangers"` |
| `delete-playlist <pl>` | Delete a playlist | `./run.sh delete-playlist "Old Mix" -y` |
| `copy` | Copy tracks between playlists | `./run.sh copy --from "Pop" --to "Best Of" --indices 0,1,2-5` |
| `move` | Move tracks between playlists | `./run.sh move --from "Inbox" --to "Favorites" --indices 0,3` |
| `split <pl>` | Auto-split playlist (>99 tracks) | `./run.sh split "Massive Library"` |
| `duplicates <pl>` | Check or clean duplicates | `./run.sh duplicates "My Mix" --clean` |
| `export <pl>` | Export playlist to file | `./run.sh export "Chill" -f csv` |
| `import <file>` | Import playlist from file | `./run.sh import "chill_backup.json"` |
| `merge` | Merge multiple playlists | `./run.sh merge --from "Rock,Indie" -t "Rock & Indie"` |
| `shuffle <pl>` | Shuffle tracks on TIDAL | `./run.sh shuffle "Party Mix"` |
| `search <query>` | Search TIDAL catalog | `./run.sh search "Daft Punk"` |

---

## 🧪 Running Tests

```bash
.venv/bin/python3 -m unittest discover -s tests
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
Copyright (c) 2026 Tobias Schudy.

