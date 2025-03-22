import sqlite3
import json
from pathlib import Path
import datetime
from ..database_utils import init_db_with_wal, needs_processing, update_file_tracking, get_db_connection
from .schema import ALBUM_METADATA_SCHEMA

def init_metadata_db(db_path: Path):
    """Initialize the metadata database."""
    init_db_with_wal(db_path, ALBUM_METADATA_SCHEMA)

def save_metadata_to_db(metadata_list: list, db_path: Path):
    """Save metadata to database."""
    # Initialize database if it doesn't exist
    init_metadata_db(db_path)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()

        for metadata in metadata_list:
            # Get file path and check if processing is needed
            file_path = Path(metadata.get('file_path', ''))
            if not file_path.exists() or not needs_processing(db_path, file_path):
                continue

            # Insert or update metadata
            cursor.execute("""
            INSERT OR REPLACE INTO album_metadata 
            (title, album, artist, album_artist, isrc, upc, first_seen, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, COALESCE((
                SELECT first_seen FROM album_metadata 
                WHERE title = ? AND album = ? AND artist = ? AND album_artist = ?
            ), ?), ?)
            """, (
                metadata.get('title', 'Unknown'),
                metadata.get('album', 'Unknown'),
                metadata.get('artist', 'Unknown'),
                metadata.get('album_artist', 'Unknown'),
                metadata.get('isrc', 'Unknown'),
                metadata.get('upc', 'Unknown'),
                # For the COALESCE subquery
                metadata.get('title', 'Unknown'),
                metadata.get('album', 'Unknown'),
                metadata.get('artist', 'Unknown'),
                metadata.get('album_artist', 'Unknown'),
                # Default values if not found
                now,
                now
            ))

            # Update file tracking in the same transaction
            update_file_tracking(conn, file_path)

        conn.commit()

def get_unique_albums_from_db(db_path: Path) -> list:
    """Get list of unique albums from database."""
    if not db_path.exists():
        return []

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT DISTINCT album, artist, album_artist
        FROM album_metadata
        ORDER BY album, artist
        """)

        results = []
        for row in cursor.fetchall():
            results.append({
                'album': row[0],
                'artist': row[1],
                'album_artist': row[2]
            })

        return results 