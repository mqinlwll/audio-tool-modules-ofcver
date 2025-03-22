from pathlib import Path
import datetime
from ..database_utils import init_db_with_wal, needs_processing, update_file_tracking, get_db_connection

ALBUM_METADATA_SCHEMA = """
CREATE TABLE IF NOT EXISTS album_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    album TEXT,
    artist TEXT,
    album_artist TEXT,
    isrc TEXT,
    upc TEXT,
    total_tracks INTEGER,
    total_discs INTEGER,
    first_seen TEXT,
    last_updated TEXT,
    UNIQUE(title, album, artist, album_artist)
)
"""

def init_metadata_db(db_path: Path):
    """Initialize the metadata database with WAL mode."""
    init_db_with_wal(db_path, ALBUM_METADATA_SCHEMA)

def save_metadata_to_db(metadata: dict, db_path: Path):
    """Save metadata to database with file tracking."""
    # Initialize database if it doesn't exist
    init_metadata_db(db_path)

    # Get file path and check if processing is needed
    file_path = Path(metadata.get('file_path', ''))
    if not file_path.exists() or not needs_processing(db_path, file_path):
        return

    now = datetime.datetime.now().isoformat()
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
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

        conn.commit()

    # Update file tracking
    update_file_tracking(db_path, file_path)

def get_metadata_from_db(db_path: Path) -> list:
    """Get all metadata from database."""
    if not db_path.exists():
        return []

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT title, album, artist, album_artist, isrc, upc, first_seen, last_updated
        FROM album_metadata
        ORDER BY album, title
        """)

        results = []
        for row in cursor.fetchall():
            results.append({
                'title': row[0],
                'album': row[1],
                'artist': row[2],
                'album_artist': row[3],
                'isrc': row[4],
                'upc': row[5],
                'first_seen': row[6],
                'last_updated': row[7]
            })

        return results 