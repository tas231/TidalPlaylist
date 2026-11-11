# TIDAL Playlist Manager 🎵

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

## 📖 Bedienungsanleitung (Web UI Walkthrough)

| Funktion | Anleitung |
|---|---|
| **Zwei-Spalten-Ansicht** | Wähle in Dropdown A und Dropdown B jeweils eine Playlist aus, um zwei Playlists nebeneinander zu sehen. |
| **Umsortieren (Drag & Drop)** | Ziehe einen Song an den Punkten (`⋮⋮`) links nach oben oder unten. Die Cyan-Linie zeigt die Position. Die Reihenfolge wird direkt in TIDAL gespeichert. |
| **Songs kopieren / verschieben** | Wähle Songs per Checkbox aus und klicke auf `Copy →` bzw. `Move →`, oder ziehe Songs per Drag & Drop zwischen die Panels. |
| **Sortieren & Speichern** | Wähle oben rechts in Panel A oder B z. B. `Title (A-Z)`. Klicke auf `Save Order`, um diese Reihenfolge in der TIDAL-Cloud zu speichern. |
| **Duplikate bereinigen** | Klicke auf `Duplicates` in der Playlist-Kopfzeile. Prüfe gefundene Kopien und klicke auf `Clean Duplicates`. |
| **Backup & Export** | Klicke auf `Export`, wähle JSON, CSV oder M3U und lade die Playlist-Sicherung herunter. |
| **Import** | Klicke oben auf `Import`, wähle eine Backup-Datei und entscheide, ob eine neue Playlist erstellt oder die Songs an Panel A bzw. B angehängt werden sollen. |
| **Große Playlists aufteilen** | Klicke auf `⚡ Split (>99)`. Playlists mit mehr als 99 Songs werden automatisch in 99er-Blöcke (`... 1`, `... 2`) aufgeteilt. |
| **Katalogsuche & Vorhören** | Drücke `Cmd+K` zum Suchen. Klicke auf ein Albumcover für die 30-Sekunden Audio-Vorschau. |

---

## ⌨️ Tastatur-Kürzel

- <kbd>Cmd</kbd> + <kbd>K</kbd> / <kbd>Ctrl</kbd> + <kbd>K</kbd> : TIDAL-Katalogsuche öffnen
- <kbd>Esc</kbd> : Aktives Dialogfenster / Modal schließen

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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  
Copyright (c) 2026 Tobias Schudy.

See [CHANGELOG.md](CHANGELOG.md) for version history.
