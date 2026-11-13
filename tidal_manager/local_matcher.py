"""Local music directory scanner and playlist matcher.

Recursively scans a local folder for audio files, extracts metadata tags
(via mutagen) and filename patterns, and matches them against streaming
playlist tracks to remove tracks that are already available locally.
"""

import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Supported audio extensions
AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".m4a",
    ".aac",
    ".alac",
    ".wav",
    ".aiff",
    ".aif",
    ".ogg",
    ".opus",
    ".wma",
}

# Regex to strip common track noise: (Remastered 2011), (2011 Remaster), [feat. X], (Live), etc.
NOISE_PATTERN = re.compile(
    r"\s*[\(\[\{]\s*(?:(?:\d{4}\s*)?remaster(?:ed)?(?:\s*\d{4})?|live(?:\s+at[^\)\]\}]*)?|feat\.?[^\)\]\}]*|ft\.?[^\)\]\}]*|deluxe[^\)\]\}]*|bonus[^\)\]\}]*|official[^\)\]\}]*|version[^\)\]\}]*|audio|video|explicit|clean|radio edit)\s*[\)\]\}]",
    re.IGNORECASE,
)

# Regex to strip unparenthesized features like "Artist feat. Other" or "Artist ft. Other"
FEAT_PATTERN = re.compile(r"\s+(?:feat\.?|ft\.?)\s+.*$", re.IGNORECASE)

# Regex to strip trailing dash noise like " - Live", " - Remastered"
DASH_NOISE_PATTERN = re.compile(
    r"\s+-\s+(?:remaster(?:ed)?(?:\s*\d{4})?|\d{4}\s*remaster(?:ed)?|live(?:\s+at.*)?|radio edit|mono|stereo|acoustic)$",
    re.IGNORECASE,
)

# Leading track numbers like "01 - ", "01. ", "1 - "
LEADING_TRACK_NUM = re.compile(r"^\s*\d{1,3}\s*[\.\-\s]\s*")


def normalize_string(text: Optional[str]) -> str:
    """Normalize string for fuzzy comparison (lowercase, strip diacritics, remove noise & punctuation)."""
    if not text:
        return ""

    # Unicode NFKD normalization (e.g. é -> e)
    s = unicodedata.normalize("NFKD", str(text))
    s = "".join(c for c in s if not unicodedata.combining(c))

    # Strip noise in parentheses/brackets like (2011 Remaster), [feat. XYZ]
    s = NOISE_PATTERN.sub("", s)

    # Strip trailing dash noise like " - Live", " - Remastered"
    s = DASH_NOISE_PATTERN.sub("", s)

    # Strip unparenthesized features (e.g. "Daft Punk feat. Nile Rodgers" -> "Daft Punk")
    s = FEAT_PATTERN.sub("", s)

    # Convert to lowercase
    s = s.lower().strip()

    # Remove non-alphanumeric except spaces
    s = re.sub(r"[^\w\s]", " ", s)

    # Collapse multiple whitespaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


@dataclass
class LocalAudioFile:
    path: str
    filename: str
    title: str
    artist: str
    album: str
    isrc: Optional[str] = None
    norm_title: str = ""
    norm_artist: str = ""

    def __post_init__(self):
        if not self.norm_title:
            self.norm_title = normalize_string(self.title)
        if not self.norm_artist:
            self.norm_artist = normalize_string(self.artist)


def extract_metadata_from_file(file_path: Path) -> LocalAudioFile:
    """Extract metadata using mutagen with fallback to filename parsing."""
    title = ""
    artist = ""
    album = ""
    isrc = None

    try:
        import mutagen
        audio = mutagen.File(str(file_path), easy=True)
        if audio:
            if "title" in audio and audio["title"]:
                title = str(audio["title"][0])
            if "artist" in audio and audio["artist"]:
                artist = str(audio["artist"][0])
            if "album" in audio and audio["album"]:
                album = str(audio["album"][0])

            # Check ISRC if available
            raw_audio = mutagen.File(str(file_path))
            if raw_audio and hasattr(raw_audio, "tags") and raw_audio.tags:
                tags = raw_audio.tags
                # ID3v2 (MP3) TSRC frame
                if hasattr(tags, "getall"):
                    tsrc = tags.getall("TSRC")
                    if tsrc:
                        isrc = str(tsrc[0]).strip().upper()
                # Vorbis comments (FLAC/OGG)
                if not isrc and hasattr(tags, "get"):
                    isrc_tag = tags.get("isrc") or tags.get("ISRC")
                    if isrc_tag:
                        isrc = str(isrc_tag[0] if isinstance(isrc_tag, list) else isrc_tag).strip().upper()
    except Exception:
        # Fallback to filename parsing
        pass

    # Fallback to filename parsing if title or artist is empty
    stem = file_path.stem
    stem_cleaned = LEADING_TRACK_NUM.sub("", stem)

    if not title:
        # If filename contains " - ", usually "Artist - Title" or "Title - Artist"
        if " - " in stem_cleaned:
            parts = stem_cleaned.split(" - ", 1)
            if not artist:
                artist = parts[0].strip()
            title = parts[1].strip()
        else:
            title = stem_cleaned.strip()

    if not artist:
        # Check parent folder: e.g. Music/Artist/Album/Track.mp3
        parent = file_path.parent
        if parent and parent.name and parent.name.lower() not in {"music", "songs", "downloads", "desktop"}:
            artist = parent.name.strip()

    return LocalAudioFile(
        path=str(file_path),
        filename=file_path.name,
        title=title or stem,
        artist=artist,
        album=album,
        isrc=isrc,
    )


def scan_local_directory(directory_path: str | Path, max_files: int = 50000) -> List[LocalAudioFile]:
    """
    Recursively scan directory for audio files and extract metadata.
    """
    root_path = Path(directory_path).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")

    results: List[LocalAudioFile] = []

    for dirpath, _, filenames in os.walk(root_path, followlinks=True):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in AUDIO_EXTENSIONS:
                fpath = Path(dirpath) / fname
                results.append(extract_metadata_from_file(fpath))
                if len(results) >= max_files:
                    return results

    return results


def match_playlist_against_local(
    playlist_tracks: List[Dict[str, Any]],
    local_files: List[LocalAudioFile],
) -> Dict[str, Any]:
    """
    Match playlist tracks against a list of scanned local audio files.

    Returns:
        Dict containing:
        - scanned_files_count: int
        - matched_count: int
        - matches: List of match dicts with playlist_index, track_id, track_name, artist, local_file, match_type
    """
    # Index local files for fast lookup
    isrc_map: Dict[str, LocalAudioFile] = {}
    title_artist_map: Dict[Tuple[str, str], LocalAudioFile] = {}
    title_only_map: Dict[str, List[LocalAudioFile]] = {}

    for lf in local_files:
        if lf.isrc:
            isrc_map[lf.isrc.upper()] = lf

        if lf.norm_title and lf.norm_artist:
            title_artist_map[(lf.norm_title, lf.norm_artist)] = lf

        if lf.norm_title:
            title_only_map.setdefault(lf.norm_title, []).append(lf)

    matches: List[Dict[str, Any]] = []

    for item in playlist_tracks:
        idx = item.get("index", 0)
        track_id = item.get("id")
        t_name = item.get("name") or item.get("title") or ""
        t_artist = item.get("artist") or ""
        t_isrc = (item.get("isrc") or "").strip().upper()

        norm_t_name = normalize_string(t_name)
        norm_t_artist = normalize_string(t_artist)

        matched_local: Optional[LocalAudioFile] = None
        match_type = ""

        # 1. Match by ISRC if both present
        if t_isrc and t_isrc in isrc_map:
            matched_local = isrc_map[t_isrc]
            match_type = "isrc"

        # 2. Match by exact normalized (Title, Artist)
        if not matched_local and (norm_t_name, norm_t_artist) in title_artist_map:
            matched_local = title_artist_map[(norm_t_name, norm_t_artist)]
            match_type = "title_artist"

        # 3. Match by Title if Artist matches partially or in path
        if not matched_local and norm_t_name in title_only_map:
            candidates = title_only_map[norm_t_name]
            for cand in candidates:
                cand_artist = cand.norm_artist
                if (
                    (cand_artist and (cand_artist in norm_t_artist or norm_t_artist in cand_artist))
                    or (norm_t_artist and norm_t_artist in normalize_string(cand.path))
                ):
                    matched_local = cand
                    match_type = "fuzzy_artist"
                    break

        if matched_local:
            matches.append({
                "index": idx,
                "track_id": track_id,
                "track_name": t_name,
                "artist_name": t_artist,
                "duration_formatted": item.get("duration_formatted", ""),
                "local_file_path": matched_local.path,
                "local_filename": matched_local.filename,
                "local_title": matched_local.title,
                "local_artist": matched_local.artist,
                "match_type": match_type,
            })

    return {
        "scanned_files_count": len(local_files),
        "total_playlist_tracks": len(playlist_tracks),
        "matched_count": len(matches),
        "matches": matches,
    }
