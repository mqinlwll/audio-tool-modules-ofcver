import mutagen
from mutagen.mp4 import MP4
from .codec import get_codec
import subprocess
import json
import sys
from pathlib import Path

def get_album_metadata(file_path: str) -> tuple:
    """Extract album, artist, and codec metadata from an audio file."""
    try:
        audio = mutagen.File(file_path, easy=True)
        if audio is None:
            return None, None, None

        album = audio.get("album", [None])[0]
        artist = audio.get("albumartist", audio.get("artist", [None]))[0]
        codec = get_codec(file_path) if isinstance(audio, MP4) else type(audio).__name__
        return album, artist, codec
    except Exception as e:
        print(f"Error reading metadata from {file_path}: {e}", file=sys.stderr)
        return None, None, None

def extract_metadata(file_path: str) -> dict:
    """Extract metadata from an audio file using ffprobe."""
    try:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path]
        result = subprocess.check_output(cmd, universal_newlines=True)
        data = json.loads(result)
        tags = data.get("format", {}).get("tags", {})

        # Normalize tag names (they can be inconsistent across formats)
        title = tags.get("title", tags.get("TITLE", "Unknown"))
        album = tags.get("album", tags.get("ALBUM", "Unknown"))
        artist = tags.get("artist", tags.get("ARTIST", "Unknown"))
        album_artist = tags.get("album_artist", tags.get("ALBUM_ARTIST", artist))
        isrc = tags.get("ISRC", tags.get("isrc", "Unknown"))
        upc = tags.get("BARCODE", tags.get("UPC", tags.get("upc", "Unknown")))

        return {
            "file_path": str(file_path),
            "title": title,
            "album": album,
            "artist": artist,
            "album_artist": album_artist,
            "isrc": isrc,
            "upc": upc
        }
    except Exception as e:
        return {
            "file_path": str(file_path),
            "error": str(e)
        }

def is_same_album(metadata1: dict, metadata2: dict) -> bool:
    """Compare two metadata dictionaries to determine if they're from the same album."""
    # If either has an error, they're not the same
    if "error" in metadata1 or "error" in metadata2:
        return False

    # If UPC matches and is not Unknown, it's definitely the same album
    if metadata1["upc"] != "Unknown" and metadata1["upc"] == metadata2["upc"]:
        return True

    # Compare album and album artist
    if metadata1["album"].lower() == metadata2["album"].lower() and \
       metadata1["album_artist"].lower() == metadata2["album_artist"].lower():
        return True

    return False
