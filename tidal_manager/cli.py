"""Command-Line Interface for Tidal Playlist Manager v1.1."""

import argparse
import sys
import time
import webbrowser
from pathlib import Path
from typing import List, Optional

from tidal_manager.client import TidalAuthError, TidalClient, TidalManagerError
from tidal_manager.config import DEFAULT_HOST, DEFAULT_PORT


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Render a clean ASCII table."""
    if not rows:
        return "No items found."

    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(val)))

    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_str = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"

    lines = [sep, header_str, sep]
    for row in rows:
        row_str = "| " + " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)) + " |"
        lines.append(row_str)
    lines.append(sep)
    return "\n".join(lines)


def cmd_login(args: argparse.Namespace) -> None:
    """Perform interactive device code OAuth login."""
    client = TidalClient()
    print("Initiating TIDAL device authorization...")
    login_info = client.start_oauth_login()

    print("\n" + "=" * 60)
    print(f"  TIDAL AUTHENTICATION CODE:  {login_info['user_code']}")
    print(f"  VISIT URL:                  {login_info['verification_url']}")
    print("=" * 60)
    print("\nWaiting for confirmation in browser (expires in 5 minutes)...")

    try:
        webbrowser.open(login_info["verification_url"])
    except Exception:
        pass

    start_time = time.time()
    while time.time() - start_time < login_info["expires_in"]:
        time.sleep(login_info.get("interval", 2))
        poll = client.poll_oauth_login()
        if poll.get("logged_in"):
            user = poll.get("user", {})
            print(f"\n[SUCCESS] Successfully logged in as: {user.get('username') or user.get('id')}")
            return
        elif poll.get("status") == "expired":
            print("\n[ERROR] Device login code expired. Please run 'login' again.")
            sys.exit(1)
        else:
            sys.stdout.write(".")
            sys.stdout.flush()

    print("\n[TIMEOUT] Login timed out. Please try again.")
    sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    """Show current login status and user profile."""
    client = TidalClient()
    if client.is_logged_in():
        info = client.get_user_info()
        print("[STATUS] Connected to TIDAL")
        print(f"User ID:  {info.get('id')}")
        print(f"Username: {info.get('username')}")
        print(f"Country:  {info.get('country_code')}")
    else:
        print("[STATUS] Not logged in. Run 'python main.py login' or start the web interface.")


def cmd_logout(args: argparse.Namespace) -> None:
    """Clear local session credentials."""
    client = TidalClient()
    client.logout()
    print("[SUCCESS] Logged out from TIDAL. Session removed.")


def cmd_list(args: argparse.Namespace) -> None:
    """List all user playlists."""
    client = TidalClient()
    try:
        playlists = client.list_playlists()
        headers = ["#", "Playlist Name", "Tracks", "Duration", "Playlist ID"]
        rows = [
            [
                str(i + 1),
                p["name"],
                str(p["num_tracks"]),
                p["duration_formatted"],
                p["id"],
            ]
            for i, p in enumerate(playlists)
        ]
        print(format_table(headers, rows))
    except TidalAuthError as e:
        print(f"[AUTH ERROR] {e}. Please run 'python main.py login' first.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_show(args: argparse.Namespace) -> None:
    """Show tracks in a playlist."""
    client = TidalClient()
    try:
        pl = client.resolve_playlist(args.playlist)
        details = client.get_playlist_details(pl.id)

        print(f"\nPlaylist: {details['name']} ({details['num_tracks']} tracks • {details['duration_formatted']})")
        if details.get("description"):
            print(f"Description: {details['description']}")
        print(f"ID: {details['id']}\n")

        headers = ["Index", "Title", "Artist", "Album", "Duration"]
        rows = [
            [
                str(t["index"] + 1),
                t["name"] + (" [E]" if t["explicit"] else ""),
                t["artist"],
                t["album"],
                t["duration_formatted"],
            ]
            for t in details["tracks"]
        ]
        print(format_table(headers, rows))
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_create(args: argparse.Namespace) -> None:
    """Create a new playlist."""
    client = TidalClient()
    try:
        res = client.create_playlist(title=args.title, description=args.description or "")
        print(f"[SUCCESS] Created playlist '{res['name']}' (ID: {res['id']})")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_rename(args: argparse.Namespace) -> None:
    """Rename a playlist."""
    client = TidalClient()
    try:
        pl = client.resolve_playlist(args.playlist)
        res = client.rename_playlist(playlist_id=pl.id, new_title=args.new_title, new_description=args.description)
        print(f"[SUCCESS] Renamed playlist to '{res['name']}'")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_delete_playlist(args: argparse.Namespace) -> None:
    """Delete a playlist."""
    client = TidalClient()
    try:
        pl = client.resolve_playlist(args.playlist)
        if not args.yes:
            confirm = input(f"Are you sure you want to delete playlist '{pl.name}'? (y/N): ")
            if confirm.strip().lower() != "y":
                print("Cancelled.")
                return

        client.delete_playlist(pl.id)
        print(f"[SUCCESS] Deleted playlist '{pl.name}'")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def parse_indices(indices_str: Optional[str]) -> List[int]:
    """Parse comma-separated or range string like '0,1,4-7' into list of integers (0-based)."""
    if not indices_str:
        return []
    indices = set()
    parts = indices_str.split(",")
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if "-" in p:
            start, end = map(int, p.split("-"))
            indices.update(range(start, end + 1))
        else:
            indices.add(int(p))
    return sorted(indices)


def cmd_copy(args: argparse.Namespace) -> None:
    """Copy tracks between playlists."""
    client = TidalClient()
    try:
        src = client.resolve_playlist(args.from_playlist)
        dst = client.resolve_playlist(args.to_playlist)
        indices = parse_indices(args.indices)
        track_ids = [t.strip() for t in args.tracks.split(",")] if args.tracks else None

        res = client.copy_tracks(
            from_playlist_id=src.id,
            to_playlist_id=dst.id,
            indices=indices if indices else None,
            track_ids=track_ids,
            allow_duplicates=True,
        )
        print(f"[SUCCESS] Copied {res['copied_count']} tracks from '{src.name}' to '{dst.name}'")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_move(args: argparse.Namespace) -> None:
    """Move tracks between playlists."""
    client = TidalClient()
    try:
        src = client.resolve_playlist(args.from_playlist)
        dst = client.resolve_playlist(args.to_playlist)
        indices = parse_indices(args.indices)
        track_ids = [t.strip() for t in args.tracks.split(",")] if args.tracks else None

        res = client.move_tracks(
            from_playlist_id=src.id,
            to_playlist_id=dst.id,
            indices=indices if indices else None,
            track_ids=track_ids,
            allow_duplicates=True,
        )
        print(f"[SUCCESS] Moved {res['moved_count']} tracks from '{src.name}' to '{dst.name}'")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_split(args: argparse.Namespace) -> None:
    """Auto-split playlist with >99 tracks into 99-track playlists with suffix."""
    client = TidalClient()
    try:
        pl = client.resolve_playlist(args.playlist)
        rename_orig = not args.no_rename
        max_tracks = args.max_tracks

        print(f"Splitting playlist '{pl.name}' (max {max_tracks} tracks per playlist)...")
        res = client.split_playlist(
            playlist_id=pl.id,
            max_tracks=max_tracks,
            rename_original=rename_orig,
        )

        if not res["needed_split"]:
            print(f"[INFO] {res['message']}")
            return

        print("\n" + "=" * 60)
        print(f"[SUCCESS] {res['message']}")
        print("=" * 60)
        headers = ["Part", "Playlist Name", "Tracks", "Original?"]
        rows = [
            [
                str(p["part"]),
                p["name"],
                str(p["tracks_count"]),
                "Yes" if p.get("is_original") else "New",
            ]
            for p in res["playlists"]
        ]
        print(format_table(headers, rows))
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_duplicates(args: argparse.Namespace) -> None:
    """Check for or clean duplicate tracks in a playlist."""
    client = TidalClient()
    try:
        pl = client.resolve_playlist(args.playlist)
        if args.clean:
            res = client.clean_duplicates(pl.id)
            print(f"[SUCCESS] {res['message']}")
        else:
            data = client.find_duplicates(pl.id)
            print(f"\nPlaylist: {data['playlist_name']} ({data['total_tracks']} tracks)")
            print(f"Duplicates Found: {data['duplicate_count']}\n")
            if data["duplicate_count"] == 0:
                print("✨ No duplicates found.")
            else:
                for grp in data["groups"]:
                    print(f"• {grp['key']} ({grp['count']} copies):")
                    for t in grp["tracks"]:
                        print(f"    - Index {t['index'] + 1}: {t['name']} ({t['duration_formatted']})")
                print("\nTo remove these duplicates, run:")
                print(f"  python main.py duplicates '{args.playlist}' --clean")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_export(args: argparse.Namespace) -> None:
    """Export a playlist backup to a file."""
    client = TidalClient()
    try:
        pl = client.resolve_playlist(args.playlist)
        content, mime, default_filename = client.export_playlist(pl.id, format_type=args.format)
        out_path = Path(args.output or default_filename)
        out_path.write_text(content, encoding="utf-8")
        print(f"[SUCCESS] Exported playlist '{pl.name}' ({args.format.upper()}) to: {out_path.resolve()}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_import(args: argparse.Namespace) -> None:
    """Import a playlist from a JSON, CSV, or M3U file."""
    client = TidalClient()
    try:
        in_path = Path(args.file)
        if not in_path.exists():
            print(f"[ERROR] File not found: {in_path}")
            sys.exit(1)

        content = in_path.read_text(encoding="utf-8")
        title = args.title or in_path.stem
        res = client.import_playlist(title=title, file_content=content, format_type="auto")
        print(f"[SUCCESS] Imported playlist '{res['title']}' with {res['imported_tracks_count']} tracks (ID: {res['playlist_id']})")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_merge(args: argparse.Namespace) -> None:
    """Merge multiple playlists into a new playlist."""
    client = TidalClient()
    try:
        source_names = [s.strip() for s in args.from_playlists.split(",") if s.strip()]
        source_ids = []
        for name in source_names:
            p = client.resolve_playlist(name)
            source_ids.append(p.id)

        res = client.merge_playlists(
            source_ids=source_ids,
            target_title=args.title,
            deduplicate=not args.no_dedupe,
        )
        print(f"[SUCCESS] Merged {res['sources_count']} playlists into '{res['title']}' ({res['total_tracks']} tracks)")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_shuffle(args: argparse.Namespace) -> None:
    """Shuffle playlist tracks in TIDAL."""
    client = TidalClient()
    try:
        pl = client.resolve_playlist(args.playlist)
        res = client.shuffle_playlist(pl.id)
        print(f"[SUCCESS] {res['message']}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_search(args: argparse.Namespace) -> None:
    """Search the TIDAL catalog."""
    client = TidalClient()
    try:
        tracks = client.search_catalog(query=args.query, limit=args.limit)
        print(f"\nSearch results for: '{args.query}' ({len(tracks)} tracks)\n")
        headers = ["ID", "Title", "Artist", "Album", "Duration"]
        rows = [
            [
                t["id"],
                t["name"] + (" [E]" if t["explicit"] else ""),
                t["artist"],
                t["album"],
                t["duration_formatted"],
            ]
            for t in tracks
        ]
        print(format_table(headers, rows))
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_remove_local(args: argparse.Namespace) -> None:
    """Scan local directory for audio files and remove locally available tracks from playlist."""
    from tidal_manager.local_matcher import match_playlist_against_local, scan_local_directory

    client = TidalClient()
    try:
        pl = client.resolve_playlist(args.playlist)
        details = client.get_playlist_details(pl.id)
        tracks = details.get("tracks", [])
        if not tracks:
            print(f"[INFO] Playlist '{pl.name}' has no tracks.")
            return

        dir_path = Path(args.directory).expanduser().resolve()
        if not dir_path.is_dir():
            print(f"[ERROR] Directory not found: {dir_path}")
            sys.exit(1)

        print(f"Scanning local directory '{dir_path}' for audio files...")
        local_files = scan_local_directory(dir_path)
        print(f"Found {len(local_files)} local audio files.")

        print(f"Matching against {len(tracks)} tracks in '{pl.name}'...")
        result = match_playlist_against_local(tracks, local_files)
        matches = result["matches"]

        if not matches:
            print(f"\n✨ No locally available tracks found in playlist '{pl.name}'. All tracks are unique!")
            return

        print(f"\n[FOUND] {len(matches)} locally available tracks in '{pl.name}':\n")
        headers = ["#", "Track Title", "Artist", "Match Type", "Matched Local File"]
        rows = [
            [
                str(m["index"] + 1),
                m["track_name"],
                m["artist_name"],
                m["match_type"],
                Path(m["local_file_path"]).name,
            ]
            for m in matches
        ]
        print(format_table(headers, rows))

        if args.dry_run:
            print(f"\n[DRY RUN] Would remove {len(matches)} tracks from '{pl.name}'. No changes made.")
            return

        if not args.yes:
            confirm = input(f"\nRemove these {len(matches)} tracks from playlist '{pl.name}'? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Operation cancelled.")
                return

        indices_to_remove = [m["index"] for m in matches]
        removed_count = client.remove_tracks_by_indices(pl.id, indices_to_remove)
        print(f"\n[SUCCESS] Removed {removed_count} locally available tracks from '{pl.name}'.")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_web(args: argparse.Namespace) -> None:
    """Launch the Web UI server."""
    import uvicorn
    from tidal_manager.server import app

    host = args.host or DEFAULT_HOST
    port = args.port or DEFAULT_PORT
    url = f"http://{host}:{port}"

    print(f"\n=======================================================")
    print(f"  TIDAL & Spotify Playlist Manager Web UI v1.4.4")
    print(f"  Running at: {url}")
    print(f"  Press Ctrl+C to stop the server.")
    print(f"=======================================================\n")

    if not args.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run(app, host=host, port=port, reload=False, log_level="info")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="tidal-manager",
        description="TIDAL Playlist Manager - Read, create, rename, duplicate check, export/import, merge, shuffle, and auto-split playlists.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # web
    p_web = subparsers.add_parser("web", help="Start the Web UI server")
    p_web.add_argument("--host", default=DEFAULT_HOST, help=f"Host (default: {DEFAULT_HOST})")
    p_web.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    p_web.add_argument("--no-open", action="store_true", help="Do not automatically open the browser")
    p_web.set_defaults(func=cmd_web)

    # login
    p_login = subparsers.add_parser("login", help="Authenticate with TIDAL via OAuth device code")
    p_login.set_defaults(func=cmd_login)

    # status
    p_status = subparsers.add_parser("status", help="Check TIDAL authentication status")
    p_status.set_defaults(func=cmd_status)

    # logout
    p_logout = subparsers.add_parser("logout", help="Log out from TIDAL")
    p_logout.set_defaults(func=cmd_logout)

    # list
    p_list = subparsers.add_parser("list", help="List all user playlists")
    p_list.set_defaults(func=cmd_list)

    # show
    p_show = subparsers.add_parser("show", help="Show tracks in a playlist")
    p_show.add_argument("playlist", help="Playlist ID or Title")
    p_show.set_defaults(func=cmd_show)

    # create
    p_create = subparsers.add_parser("create", help="Create a new playlist")
    p_create.add_argument("title", help="Playlist title")
    p_create.add_argument("--description", "-d", help="Optional playlist description")
    p_create.set_defaults(func=cmd_create)

    # rename
    p_rename = subparsers.add_parser("rename", help="Rename an existing playlist")
    p_rename.add_argument("playlist", help="Playlist ID or current Title")
    p_rename.add_argument("new_title", help="New playlist title")
    p_rename.add_argument("--description", "-d", help="Optional updated description")
    p_rename.set_defaults(func=cmd_rename)

    # delete-playlist
    p_del = subparsers.add_parser("delete-playlist", help="Delete a playlist")
    p_del.add_argument("playlist", help="Playlist ID or Title")
    p_del.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    p_del.set_defaults(func=cmd_delete_playlist)

    # copy
    p_copy = subparsers.add_parser("copy", help="Copy tracks between playlists")
    p_copy.add_argument("--from", dest="from_playlist", required=True, help="Source playlist ID or Title")
    p_copy.add_argument("--to", dest="to_playlist", required=True, help="Destination playlist ID or Title")
    p_copy.add_argument("--indices", help="Track indices (0-based, e.g. '0,1,5-10')")
    p_copy.add_argument("--tracks", help="Track IDs (comma-separated)")
    p_copy.set_defaults(func=cmd_copy)

    # move
    p_move = subparsers.add_parser("move", help="Move tracks between playlists")
    p_move.add_argument("--from", dest="from_playlist", required=True, help="Source playlist ID or Title")
    p_move.add_argument("--to", dest="to_playlist", required=True, help="Destination playlist ID or Title")
    p_move.add_argument("--indices", help="Track indices (0-based, e.g. '0,1,5-10')")
    p_move.add_argument("--tracks", help="Track IDs (comma-separated)")
    p_move.set_defaults(func=cmd_move)

    # split
    p_split = subparsers.add_parser("split", help="Auto-split playlist with >99 tracks into 99-track playlists with suffix")
    p_split.add_argument("playlist", help="Playlist ID or Title")
    p_split.add_argument("--max-tracks", type=int, default=99, help="Max tracks per playlist (default: 99)")
    p_split.add_argument("--no-rename", action="store_true", help="Do not rename original playlist to '[Name] 1'")
    p_split.set_defaults(func=cmd_split)

    # duplicates
    p_dup = subparsers.add_parser("duplicates", help="Find or remove duplicate tracks in a playlist")
    p_dup.add_argument("playlist", help="Playlist ID or Title")
    p_dup.add_argument("--clean", action="store_true", help="Automatically remove duplicate tracks")
    p_dup.set_defaults(func=cmd_duplicates)

    # export
    p_exp = subparsers.add_parser("export", help="Export playlist to JSON, CSV, or M3U file")
    p_exp.add_argument("playlist", help="Playlist ID or Title")
    p_exp.add_argument("--format", "-f", choices=["json", "csv", "m3u"], default="json", help="Export format")
    p_exp.add_argument("--output", "-o", help="Output file path")
    p_exp.set_defaults(func=cmd_export)

    # import
    p_imp = subparsers.add_parser("import", help="Import playlist from JSON, CSV, or M3U file")
    p_imp.add_argument("file", help="File path to import")
    p_imp.add_argument("--title", "-t", help="Optional new playlist title")
    p_imp.set_defaults(func=cmd_import)

    # merge
    p_mrg = subparsers.add_parser("merge", help="Merge multiple playlists into a new playlist")
    p_mrg.add_argument("--from", dest="from_playlists", required=True, help="Comma-separated playlist IDs or names")
    p_mrg.add_argument("--title", "-t", required=True, help="Title of new merged playlist")
    p_mrg.add_argument("--no-dedupe", action="store_true", help="Do not deduplicate songs during merge")
    p_mrg.set_defaults(func=cmd_merge)

    # shuffle
    p_shuf = subparsers.add_parser("shuffle", help="Shuffle tracks of a playlist in TIDAL")
    p_shuf.add_argument("playlist", help="Playlist ID or Title")
    p_shuf.set_defaults(func=cmd_shuffle)

    # search
    p_srch = subparsers.add_parser("search", help="Search the TIDAL catalog for tracks")
    p_srch.add_argument("query", help="Search keywords (title, artist)")
    p_srch.add_argument("--limit", "-l", type=int, default=20, help="Max results (default: 20)")
    p_srch.set_defaults(func=cmd_search)

    # remove-local
    p_remloc = subparsers.add_parser(
        "remove-local",
        help="Scan local directory and remove locally available tracks from a playlist",
    )
    p_remloc.add_argument("playlist", help="Playlist ID or Title")
    p_remloc.add_argument("directory", help="Local folder path containing audio files (e.g. ~/Music)")
    p_remloc.add_argument("--dry-run", action="store_true", help="Preview matches without deleting anything")
    p_remloc.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    p_remloc.set_defaults(func=cmd_remove_local)

    return parser


def main() -> None:
    parser = build_parser()
    if len(sys.argv) == 1:
        cmd_web(argparse.Namespace(host=DEFAULT_HOST, port=DEFAULT_PORT, no_open=False))
        return

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
