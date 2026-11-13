# TIDAL & Spotify Playlist Manager 🎵🟢

[![PyPI version](https://img.shields.io/pypi/v/tidal-playlist-manager.svg?color=blue)](https://pypi.org/project/tidal-playlist-manager/)
[![Release](https://img.shields.io/github/v/release/tas231/TidalPlaylist?color=cyan&label=release)](https://github.com/tas231/TidalPlaylist/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Platform: macOS | Linux | Windows](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)](https://github.com/tas231/TidalPlaylist)

A powerful, modern music playlist management application featuring a dual-pane **Web UI** and a comprehensive **CLI** for **TIDAL** and **Spotify**.

Manage in-platform playlists or transfer tracks across platforms in both directions (**TIDAL ↔ Spotify**) with smart ISRC track matching and zero build-step requirements!

---

## ✨ Features

- 🔄 **Dual-Platform & Cross-Platform Transfers (TIDAL & Spotify)**:
  - Independently toggle either **Panel A** or **Panel B** between **🎵 TIDAL** and **🟢 Spotify**.
  - **In-Platform transfers**: TIDAL ↔ TIDAL, Spotify ↔ Spotify.
  - **Cross-Platform transfers**: Transfer songs seamlessly from **TIDAL → Spotify** or **Spotify → TIDAL**!
  - Supports both **Copy** (keep in source) and **Move** (remove from source after copying).
  - **Smart ISRC Track Matching**: Automatically queries target catalogs by international standard ISRC (International Standard Recording Code) for 100% exact track matches, with intelligent fallback to normalized Title + Artist search.
  - **Detailed Transfer Report**: Displays a clear summary dialog showing successfully transferred tracks and any tracks not found in the destination service.

> [!IMPORTANT]
> ### ⚠️ SPOTIFY PREMIUM REQUIREMENT (SPOTIFY DEVELOPER POLICY)
> **SPOTIFY STRICTLY REQUIRES AN ACTIVE SPOTIFY PREMIUM SUBSCRIPTION FOR THE ACCOUNT THAT OWNS THE DEVELOPER APP.**  
> Spotify Free accounts are blocked server-side by Spotify's Web API with:  
> `403 Forbidden: Active premium subscription required for the owner of the app`.  
> *Please ensure your Spotify Developer App is created using an account with an active Spotify Premium subscription (Individual, Duo, or Family).*

- 🎧 **Read & Manage Playlists**: View personal playlists side-by-side, inspect tracklists, high-res album covers, explicit badges, track durations, and total running times.
- ➕ **Create & Rename**: Add new playlists with descriptions on TIDAL or Spotify, or rename existing ones in-place.
- 📋 **Copy & Move Tracks**: Copy or move selected tracks between playlists with multi-selection.
- 🖱️ **Drag & Drop (Cross-Panel & In-Playlist)**:
  - **In-Playlist Reordering**: Reorder songs directly within any playlist by grabbing the grip handle (`⋮⋮`) and dragging them up or down. A cyan indicator line shows the exact drop location, and the new sequence is instantly synced to the cloud!
  - **Cross-Panel Transfers**: Drag tracks directly from Panel A to Panel B (or vice versa)—even between TIDAL and Spotify—to copy them, or hold <kbd>Alt</kbd> / <kbd>Shift</kbd> to move them.
- ⚡ **Auto-Split Playlists (> 99 Tracks)**:
  - Automatically splits any playlist with > 99 tracks into chunks of max 99 tracks (ideal for car head-units and audio gear with 99-track limits).
  - Automatically names them with numerical suffixes: `[Name] 1`, `[Name] 2`, `[Name] 3`...
  - Moves excess tracks seamlessly into the new suffix playlists.
- 🔍 **Duplicate Finder & 1-Click Cleaner**:
  - Scans for duplicate tracks by exact Media ID and normalized Title + Artist matching.
  - Groups duplicate copies and provides a 1-click **Clean Duplicates** action (safely retaining the earliest added copy).
- 💾 **Backup & Flexible Export / Import**:
  - **Export**: Export playlists directly as **JSON** (full metadata), **CSV** (for spreadsheets and DJ tools), or **M3U8** (for media players).
  - **Import**: Import playlists from JSON, CSV, or M3U files with flexible destinations:
    - ✨ Create as a brand-new playlist
    - 📥 Append imported tracks directly into the playlist active in **Panel A**
    - 📥 Append imported tracks directly into the playlist active in **Panel B**
- 🔀 **Playlist Merge & Cloud Shuffle**:
  - **Merge**: Combine multiple playlists into a unified master playlist (with optional automatic deduplication).
  - **Cloud Shuffle**: Randomize track ordering permanently in the cloud.
- 📊 **Sorting & Ordering**:
  - Sort tracks on-the-fly by Title, Artist, Album, or Duration in ascending or descending order.
  - One-click **"Save Order"** button to permanently commit the sorted order to the cloud.
- 🎧 **Audio Preview Player**:
  - 30-second audio preview button directly on every track's artwork thumbnail.
  - Sticky bottom preview player bar with scrubber, duration counter, and a 1-click direct link to web players.
- 🔎 **Integrated Catalog Search**:
  - Global catalog search (<kbd>Cmd+K</kbd> / <kbd>Ctrl+K</kbd>) to discover tracks and add them directly to Panel A or Panel B with 1 click.
- 📖 **In-App Guide & Shortcuts Modal**:
  - Built-in **Guide** button in the header bar with step-by-step feature walkthroughs and tips.
- 🔐 **Privacy & Security First**:
  - Connects using official OAuth authorization.
  - No passwords or sensitive credentials are ever stored. Session tokens are stored locally and strictly excluded from git tracking.

---

## 🚀 Installation & Launch Options

Choose whichever method is easiest for you:

### 📦 Option 1: Standalone Desktop App (No Python Required)
If you don't have Python installed and want a simple 1-click experience:
1. Head over to the **[Latest Releases](https://github.com/tas231/TidalPlaylist/releases)** page on GitHub.
2. Download the pre-built archive for your operating system:
   - **Windows**: `TidalPlaylistManager-Windows-x64.zip` (extract and double-click `TidalPlaylistManager.exe`)
   - **macOS**: `TidalPlaylistManager-macOS.zip` (extract and open `TidalPlaylistManager`)
   - **Linux**: `TidalPlaylistManager-Linux-x64.tar.gz`
3. The app starts locally and immediately opens the Web UI in your default browser!

---

### 🐍 Option 2: Install via pip / pipx (PyPI)
If you have Python 3.9+ installed:

#### Installation
```bash
# Recommended: Install in an isolated environment with pipx:
pipx install tidal-playlist-manager

# Or install in your active Python environment:
pip install tidal-playlist-manager
```

#### Launch
Start the app anytime from any terminal:
```bash
tidal-manager
```

#### How to update to the latest version:
To update your installation to the latest release on PyPI:
```bash
# For pipx users (bypasses local cache to fetch the newest release immediately):
pipx upgrade --pip-args="--no-cache-dir" tidal-playlist-manager

# For standard pip users:
pip install --upgrade --no-cache-dir tidal-playlist-manager
```

---

### 💻 Option 3: Run from Git Source Checkout

#### Prerequisites
- **Python 3.9 or higher** ([python.org](https://www.python.org/downloads/)).
  - *Windows users:* Make sure to check **"Add Python to PATH"** during setup.
  - *Linux users (Ubuntu/Debian):* `sudo apt install python3 python3-venv python3-pip`.

#### Launching from source:
- **🍎 macOS**: Double-click `Start.command` or `Tidal Playlist Manager.app` (or `./run.sh` in Terminal).
- **🪟 Windows**: Double-click `run.bat` in File Explorer.
- **🐧 Linux**: Run `chmod +x run.sh && ./run.sh` in Terminal.

---

### 🔑 Connect your Accounts

#### 1. TIDAL (Primary)
1. Once started, your default browser opens at **`http://127.0.0.1:8000`**.
2. Click **Connect with TIDAL**.
3. Click the authorization link to approve the code in your browser (no password required).
4. Once approved, the manager will instantly load your TIDAL playlists!

#### 2. Spotify (Optional for Dual-Platform & Transfers)

> [!WARNING]
> ### 🚨 CRITICAL SPOTIFY REQUIREMENT (MUST READ BEFORE CONNECTING):
> **SPOTIFY STRICTLY REQUIRES AN ACTIVE SPOTIFY PREMIUM SUBSCRIPTION FOR THE ACCOUNT USED TO CREATE THE DEVELOPER APP.**  
> 
> Due to Spotify's developer API policy changes, **Spotify Free accounts are blocked by Spotify's API** and will fail with `403 Forbidden: Active premium subscription required for the owner of the app`.  
> 
> 👉 **YOU MUST LOG INTO [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) WITH AN ACCOUNT THAT HAS AN ACTIVE SPOTIFY PREMIUM PLAN (Individual, Duo, or Family) TO CREATE YOUR APP!**

1. In the top-right header, click **🟢 Connect Spotify** (or select the **🟢 Spotify** tab on Panel A or Panel B).
2. Enter your Spotify Developer App credentials:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) (logged into your **Spotify Premium** account).
   - Click **Create app** (App name: *TidalPlaylist*, Redirect URI: `http://127.0.0.1:8000/api/spotify/callback`).
   - Copy and paste your **Client ID** and **Client Secret**.
3. Click **Save & Authorize Spotify**. A popup window will prompt you to approve access.
4. Once connected, your Spotify account badge appears and you can select Spotify in either panel!

---

## 📖 User Guide (Web UI Walkthrough)

| Feature | How to Use |
|---|---|
| **Platform Switcher** | Use the `[ 🎵 TIDAL ]` and `[ 🟢 Spotify ]` tabs at the top of Panel A and Panel B to choose the music service for each side independently. |
| **Dual-Pane View** | Select a playlist in Dropdown A and Dropdown B to inspect and manage two playlists side-by-side. |
| **Cross-Platform Transfer** | Set Panel A to TIDAL and Panel B to Spotify (or vice-versa). Select songs and click `Copy →` or `Move →` (or drag & drop). Matches via ISRC standard with Title/Artist fallback and shows a detailed transfer report. |
| **In-Playlist Reordering (Drag & Drop)** | Grab any song by the grip handle (`⋮⋮`) on the left and drag it up or down. A cyan indicator line shows the drop position. The new order is saved directly to your cloud playlist. |
| **Copy / Move Tracks** | Select tracks using checkboxes and click `Copy →` or `Move →`, or drag & drop songs directly between panels (hold <kbd>Alt</kbd> or <kbd>Shift</kbd> to move). |
| **Sort & Save Order** | Select a sort criteria like `Title (A-Z)` in the panel header. Click `Save Order` to commit this order permanently to your cloud playlist. |
| **Clean Duplicates** | Click `Duplicates` in the playlist header. Inspect grouped duplicate copies and click `Clean Duplicates` to remove redundant tracks safely. |
| **Backup & Export** | Click `Export`, select JSON, CSV, or M3U, and download your playlist backup. |
| **Import** | Click `Import` in the top bar, upload a backup file, and choose whether to create a new playlist or append tracks directly into Panel A or Panel B. |
| **Split Large Playlists** | Click `⚡ Split (>99)` to divide playlists with > 99 tracks into clean 99-track chunks (`... 1`, `... 2`). |
| **Catalog Search & Preview** | Press `Cmd+K` to search millions of tracks. Click any track cover artwork for an instant 30-second audio preview. |

---

## ⌨️ Keyboard Shortcuts

- <kbd>Cmd</kbd> + <kbd>K</kbd> / <kbd>Ctrl</kbd> + <kbd>K</kbd> : Open global catalog search
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
- **Third-Party Services:** This project is an independent open-source tool and is not affiliated with, endorsed by, or sponsored by TIDAL, Aspiro AB, or Spotify AB.

---

## 📌 Project Status & Forking

This project is feature-complete for its intended scope and is provided as a finished utility. Active ongoing feature development or maintenance is not planned.

If you would like to customize, extend, or build upon this tool, you are very welcome to **fork, copy, or adapt the code** freely under the terms of the [MIT License](LICENSE).

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  
Copyright (c) 2026 magicclue.

See [CHANGELOG.md](CHANGELOG.md) for version history.
