import sqlite3
import datetime
from pathlib import Path
from ..database_utils import init_db_with_wal, needs_processing, update_file_tracking, get_db_connection

AUDIO_ANALYSIS_SCHEMA = """
CREATE TABLE IF NOT EXISTS audio_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    album TEXT,
    artist TEXT,
    album_artist TEXT,
    isrc TEXT,
    upc TEXT,
    codec TEXT,
    sample_rate INTEGER,
    bit_depth INTEGER,
    bit_rate INTEGER,
    channels INTEGER,
    first_analyzed TEXT,
    last_updated TEXT,
    UNIQUE(title, album, artist, album_artist, codec, sample_rate, bit_depth, bit_rate, channels)
)
"""

def init_audio_analysis_db(db_path: Path):
    """Initialize the audio analysis database with WAL mode."""
    init_db_with_wal(db_path, AUDIO_ANALYSIS_SCHEMA)

def save_analysis_to_db(analysis_data: dict, db_path: Path):
    """Save audio analysis data to database with file tracking."""
    # Initialize database if it doesn't exist
    init_audio_analysis_db(db_path)

    # Get file path and check if processing is needed
    file_path = Path(analysis_data.get('file_path', ''))
    if not file_path.exists() or not needs_processing(db_path, file_path):
        return

    now = datetime.datetime.now().isoformat()
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Insert or update analysis data
        cursor.execute("""
        INSERT OR REPLACE INTO audio_analysis 
        (title, album, artist, album_artist, isrc, upc, codec, sample_rate, bit_depth, bit_rate, channels,
         first_analyzed, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((
            SELECT first_analyzed FROM audio_analysis 
            WHERE title = ? AND album = ? AND artist = ? AND album_artist = ? AND codec = ? 
            AND sample_rate = ? AND bit_depth = ? AND bit_rate = ? AND channels = ?
        ), ?), ?)
        """, (
            analysis_data.get('title', 'Unknown'),
            analysis_data.get('album', 'Unknown'),
            analysis_data.get('artist', 'Unknown'),
            analysis_data.get('album_artist', 'Unknown'),
            analysis_data.get('isrc', 'Unknown'),
            analysis_data.get('upc', 'Unknown'),
            analysis_data.get('codec', 'Unknown'),
            analysis_data.get('sample_rate', 0),
            analysis_data.get('bit_depth', 0),
            analysis_data.get('bit_rate', 0),
            analysis_data.get('channels', 0),
            # For the COALESCE subquery
            analysis_data.get('title', 'Unknown'),
            analysis_data.get('album', 'Unknown'),
            analysis_data.get('artist', 'Unknown'),
            analysis_data.get('album_artist', 'Unknown'),
            analysis_data.get('codec', 'Unknown'),
            analysis_data.get('sample_rate', 0),
            analysis_data.get('bit_depth', 0),
            analysis_data.get('bit_rate', 0),
            analysis_data.get('channels', 0),
            # Default values if not found
            now,
            now
        ))

        # Update file tracking in the same transaction
        update_file_tracking(conn, file_path)
        conn.commit()

def get_analysis_from_db(db_path: Path) -> list:
    """Get all audio analysis data from database."""
    if not db_path.exists():
        return []

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT title, album, artist, album_artist, isrc, upc, codec, sample_rate, bit_depth, bit_rate, channels,
               first_analyzed, last_updated
        FROM audio_analysis
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
                'codec': row[6],
                'sample_rate': row[7],
                'bit_depth': row[8],
                'bit_rate': row[9],
                'channels': row[10],
                'first_analyzed': row[11],
                'last_updated': row[12]
            })

        return results 