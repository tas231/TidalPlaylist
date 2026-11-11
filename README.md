# TIDAL Playlist Manager 🎵

[![Release](https://img.shields.io/github/v/release/tas231/TidalPlaylist?color=cyan&label=release)](https://github.com/tas231/TidalPlaylist/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Platform: macOS | Linux | Windows](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)](https://github.com/tas231/TidalPlaylist)

A powerful, modern TIDAL playlist management application featuring a dual-pane **Web UI** and a comprehensive **CLI**.

Built with Python, FastAPI, and `tidalapi`, with zero build-step requirements.

---

## ✨ Features

- 🎧 **Read & Manage Playlists**: View all personal TIDAL playlists side-by-side, inspect tracklists, high-res album covers, explicit badges, track durations, and total running times.
- ➕ **Create & Rename**: Add new playlists with descriptions or rename existing ones in-place.
- 📋 **Copy & Move Tracks**: Copy or move selected tracks between playlists with multi-selection.
- 🖱️ **Drag & Drop (Cross-Panel & In-Playlist)**:
  - **In-Playlist Reordering**: Reorder songs directly within any playlist by grabbing the grip handle (`⋮⋮`) and dragging them up or down. A cyan indicator line shows the exact drop location, and the new sequence is instantly synced to TIDAL in the cloud!
  - **Cross-Panel Transfers**: Drag tracks directly from Panel A to Panel B (or vice versa) to copy them, or hold <kbd>Alt</kbd> / <kbd>Shift</kbd> to move them.
- ⚡ **Auto-Split Playlists (> 99 Tracks)**:
  - Automatically splits any playlist with > 99 tracks into chunks of max 99 tracks (ideal for car head-units and audio gear with 99-track limits).
  - Automatically names them with numerical suffixes: `[Name] 1`, `[Name] 2`, `[Name] 3`...
  - Moves excess tracks seamlessly into the new suffix playlists.
- 🔍 **Duplicate Finder & 1-Click Cleaner**:
  - Scans for duplicate tracks by exact TIDAL Media ID and normalized Title + Artist matching.
  - Groups duplicate copies and provides a 1-click **Clean Duplicates** action (safely retaining the earliest added copy).
- 💾 **Backup & Flexible Export / Import**:
  - **Export**: Export playlists directly as **JSON** (full metadata), **CSV** (for spreadsheets and DJ tools), or **M3U8** (for media players).
  - **Import**: Import playlists from JSON, CSV, or M3U files with flexible destinations:
    - ✨ Create as a brand-new playlist on TIDAL
    - 📥 Append imported tracks directly into the playlist active in **Panel A**
    - 📥 Append imported tracks directly into the playlist active in **Panel B**
- 🔀 **Playlist Merge & Cloud Shuffle**:
  - **Merge**: Combine multiple playlists into a unified master playlist (with optional automatic deduplication).
  - **Cloud Shuffle**: Randomize track ordering permanently in the TIDAL cloud.
- 📊 **Sorting & Ordering**:
  - Sort tracks on-the-fly by Title, Artist, Album, or Duration in ascending or descending order.
  - One-click **"Save Order"** button to permanently commit the sorted order to TIDAL.
- 🎧 **Audio Preview Player**:
  - 30-second audio preview button directly on every track's artwork thumbnail.
  - Sticky bottom preview player bar with scrubber, duration counter, and a 1-click direct link to the TIDAL web player.
- 🔎 **Integrated TIDAL Catalog Search**:
  - Global catalog search (<kbd>Cmd+K</kbd> / <kbd>Ctrl+K</kbd>) to discover tracks across TIDAL and add them directly to Panel A or Panel B with 1 click.
- 📖 **In-App Guide & Shortcuts Modal**:
  - Built-in **Guide** button in the header bar with step-by-step feature walkthroughs and tips.
- 🔐 **Privacy & Security First**:
  - Connects using TIDAL's official Device Code authorization (`link.tidal.com`).
  - No passwords or sensitive credentials are ever stored. Session tokens are stored in `.tidal_session.json` and strictly excluded from git tracking.

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
2. Click the authorization link to approve the code in your browser (no password required).
3. Once approved, the manager will instantly load your playlists side-by-side!

---

## 📖 User Guide (Web UI Walkthrough)

| Feature | How to Use |
|---|---|
| **Dual-Pane View** | Select a playlist in Dropdown A and Dropdown B to inspect and manage two playlists side-by-side. |
| **In-Playlist Reordering (Drag & Drop)** | Grab any song by the grip handle (`⋮⋮`) on the left and drag it up or down. A cyan indicator line shows the drop position. The new order is saved directly to TIDAL. |
| **Copy / Move Tracks** | Select tracks using checkboxes and click `Copy →` or `Move →`, or drag & drop songs directly between panels (hold <kbd>Alt</kbd> or <kbd>Shift</kbd> to move). |
| **Sort & Save Order** | Select a sort criteria like `Title (A-Z)` in the panel header. Click `Save Order` to commit this order permanently to your cloud playlist on TIDAL. |
| **Clean Duplicates** | Click `Duplicates` in the playlist header. Inspect grouped duplicate copies and click `Clean Duplicates` to remove redundant tracks safely. |
| **Backup & Export** | Click `Export`, select JSON, CSV, or M3U, and download your playlist backup. |
| **Import** | Click `Import` in the top bar, upload a backup file, and choose whether to create a new playlist or append tracks directly into Panel A or Panel B. |
| **Split Large Playlists** | Click `⚡ Split (>99)` to divide playlists with > 99 tracks into clean 99-track chunks (`... 1`, `... 2`). |
| **Catalog Search & Preview** | Press `Cmd+K` to search millions of TIDAL tracks. Click any track cover artwork for an instant 30-second audio preview. |

---

## ⌨️ Keyboard Shortcuts

- <kbd>Cmd</kbd> + <kbd>K</kbd> / <kbd>Ctrl</kbd> + <kbd>K</kbd> : Open global TIDAL catalog search
- <kbd>Esc</kbd> : Close active dialog or modal window

---

## 🛠️ CLI Reference

All features are also available directly via the command-line interface:

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

## ⚠️ Disclaimer & Limitation of Liability

This free software is provided **"as is"** and is intended strictly as a **testing and evaluation tool** for educational and personal experimentation:

- **No Liability or Responsibility:** The author(s) and contributor(s) accept **no liability or responsibility whatsoever** for any direct, indirect, incidental, or consequential damages, playlist modifications, unintended track removals, loss of data, account restrictions, or API disruptions arising from the use of or inability to use this software.
- **Testing Use Only:** This application is provided for testing and evaluation purposes. Always verify changes and use it entirely at your own discretion and risk.
- **Backups Strongly Recommended:** Before modifying, sorting, splitting, or deduplicating playlists, please use the built-in **Backup & Export** feature to create a local JSON, CSV, or M3U backup of your playlists.
- **Third-Party Service:** This project is an independent open-source tool and is not affiliated with, endorsed by, or sponsored by TIDAL or Aspiro AB.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  
Copyright (c) 2026 Tobias Schudy.

See [CHANGELOG.md](CHANGELOG.md) for version history.
