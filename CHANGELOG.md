# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.2] - 2026-11-11

### Added
- **Windows & Linux Support**:
  - Added native Windows launcher `run.bat` for one-click setup and execution on Windows.
  - Added `requirements.txt` for standard dependency installation across all environments.
  - Documented setup and prerequisites for macOS, Windows, and Linux in `README.md`.
- **Explicit Liability & Testing Disclaimers**:
  - Added dedicated limitation of liability section in `README.md` and user-facing testing notices in the Web UI login screen and in-app Guide modal stating the software is provided "as is" for testing and evaluation purposes without warranty.
- **Project Status & Forking Notice**: Clarified that active ongoing feature development is not planned and invited users to freely fork and adapt the code under the MIT License.

### Changed
- **Full Internationalization (English)**:
  - Standardized all application text, in-app user guide modal, UI hints, tooltips, and documentation into fluent English for international users.

## [1.2.1] - 2026-11-11

### Added
- **In-App User Guide Modal**: Added an interactive "Guide" button in the header bar and an illustrated Quickstart / Feature walkthrough modal explaining drag-and-drop, sorting, duplicates, backup/export/import, split, and search.
- **Enhanced Transfer Hints**: Updated transfer dock hints to highlight both in-playlist reordering via `⋮⋮` handles and cross-panel transfers.
- **Modal Backdrop Dismiss**: Clicking outside any modal dialog on the darkened overlay now gracefully closes the dialog.

### Documentation
- **Comprehensive README.md**: Added detailed feature descriptions, an organized Web UI walkthrough table, keyboard shortcuts reference, and complete CLI command table.

### Security
- **Hardened Repository Ignored Patterns**: Extended `.gitignore` with strict exclusion filters for session files, OAuth tokens, `.env` variants, private keys (`.pem`, `.key`), certificates, credentials, and secrets to ensure zero sensitive data or credentials can ever be tracked or committed.

## [1.2.0] - 2026-11-11

### Added
- **In-Playlist Drag & Drop Reordering**:
  - Drag tracks up or down within the same playlist to instantly reorder their playback position.
  - Interactive visual drop indicators (`drop-before` / `drop-after` cyan border lines) and drag grip handle (`⋮⋮`).
  - Optimistic UI reordering for instant visual feedback, synchronized with TIDAL cloud via `POST /api/playlists/{id}/reorder`.

## [1.1.2] - 2026-11-11

### Added
- **Flexible Import Destination**: The Import modal now lets users choose their destination target:
  - ✨ Create as a brand new playlist on TIDAL (with custom or detected title)
  - 📥 Append imported tracks directly to the currently selected playlist in **Panel A**
  - 📥 Append imported tracks directly to the currently selected playlist in **Panel B**
- Automatically disables panel options when no playlist is loaded in that panel and reloads the respective panel upon completion.

## [1.1.1] - 2026-11-11

### Fixed
- **Title Sorting**: Fixed property name mapping (`title` -> `name`) in client-side sort algorithm so sorting by Title (A-Z) operates correctly. Added `localeCompare` for international/accented titles.
- **Dynamic Row Indexing**: When sorted, row numbering reflects the current sorted positions (1, 2, 3...) instead of raw playlist indices.
- **Server Auto-Reload**: Configured uvicorn with `reload=True` to prevent stale Python server processes after updates.
- **Duplicates Endpoint**: Resolved 404 error caused by stale server instance running prior to endpoint addition.

## [1.1.0] - 2026-11-11

### Added
- **🔍 Duplicate Finder & Cleaner**:
  - Automatic detection of duplicate tracks by exact TIDAL Media ID and normalized Title + Artist.
  - Duplicates inspection modal with grouped copies and 1-click duplicate removal (keeping earliest added).
  - CLI command: `tidal-manager duplicates <playlist> [--clean]`.
- **💾 Backup & Export / Import**:
  - Export playlists directly to **JSON** (full metadata), **CSV** (spreadsheet format), or **M3U8** (media players / DJ gear).
  - Import playlists from JSON, CSV, or M3U files (auto-detected) with automatic track resolution.
  - CLI commands: `tidal-manager export <playlist>` and `tidal-manager import <file>`.
- **🔀 Playlist Merge & Cloud Shuffle**:
  - Merge multiple playlists into a new unified playlist with optional automatic deduplication.
  - True cloud shuffle: randomize playlist track ordering permanently on TIDAL.
  - CLI commands: `tidal-manager merge` and `tidal-manager shuffle <playlist>`.
- **📊 Sorting & Ordering**:
  - Sort tracks by Title, Artist, Album, or Duration in ascending or descending order.
  - One-click "Save Order" to commit sorted order permanently to TIDAL.
- **🎧 30-Second Audio Preview**:
  - Play preview button directly on album artwork of every track.
  - Sticky bottom mini audio player bar with scrub slider, duration display, and 1-click fallback to the TIDAL web player.
- **🖱️ Drag & Drop**:
  - Interactive HTML5 Drag & Drop: drag tracks directly from Panel A into Panel B (and vice versa) to copy or move.
- **🔎 Integrated TIDAL Catalog Search**:
  - Search full TIDAL catalog across all tracks, artists, and albums (shortcut: `Cmd+K` / `Ctrl+K`).
  - Direct "+ Add to Panel A" / "+ Add to Panel B" buttons on search results.
  - CLI command: `tidal-manager search <query>`.
- **Open Source & Licensing**:
  - Added MIT License ([`LICENSE`](LICENSE)) and made the repository public on GitHub.

---

## [1.0.0] - 2026-11-11

### Added
- **Initial Release of TIDAL Playlist Manager**:
  - Dual-pane side-by-side Web UI for visual playlist comparison and transfer.
  - Read user playlists with album art, track counts, explicit tags, and formatted durations.
  - Create, rename, and delete personal playlists.
  - Copy tracks between playlists with multi-selection and live search filter.
  - Move tracks between playlists (atomic append to destination and removal from source).
  - **⚡ Auto-Split (>99 Tracks)**: Automatically split large playlists into chunks of max 99 tracks with numerical suffixes (`[Name] 1`, `[Name] 2`, `[Name] 3`...).
  - Secure TIDAL OAuth2 Device Code authorization flow (`link.tidal.com`) with persistent token storage and auto-refresh.
  - Comprehensive Command-Line Interface (`cli.py` / `main.py`).
  - macOS double-clickable launchers: `Start.command` and `Tidal Playlist Manager.app`.
  - Comprehensive automated test suite with unit and API integration tests.
