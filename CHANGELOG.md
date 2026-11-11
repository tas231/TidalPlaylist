# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
