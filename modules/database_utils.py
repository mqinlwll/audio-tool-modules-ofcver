import sqlite3
import os
from pathlib import Path
import datetime
import hashlib
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Constants for database settings
TIMEOUT = 60.0  # seconds
RETRY_COUNT = 3

FILE_TRACKING_SCHEMA = """
CREATE TABLE IF NOT EXISTS file_tracking (
    file_path TEXT PRIMARY KEY,
    last_modified TEXT,
    file_hash TEXT,
    last_processed TEXT
);
"""

@contextmanager
def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Get a database connection with WAL mode enabled."""
    conn = sqlite3.connect(db_path, timeout=TIMEOUT)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA busy_timeout={}".format(int(TIMEOUT * 1000)))  # Convert to milliseconds
        yield conn
    finally:
        conn.close()

def init_db_with_wal(db_path: Path, schema: str):
    """Initialize a database with WAL mode and the given schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable WAL mode
    cursor.execute("PRAGMA journal_mode=WAL")
    
    # Create file tracking table first
    cursor.execute(FILE_TRACKING_SCHEMA)
    
    # Execute each statement in the schema separately
    for statement in schema.split(';'):
        if statement.strip():
            cursor.execute(statement)
    
    conn.commit()
    conn.close()

def get_file_info(file_path: Path) -> Dict[str, Any]:
    """Get file modification time and hash."""
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
    with open(file_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    return {
        'mtime': mtime.isoformat(),
        'hash': file_hash
    }

def needs_processing(db_path: Path, file_path: Path) -> bool:
    """Check if file needs processing based on mtime and hash."""
    if not db_path.exists():
        return True

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Get current file info
        current_info = get_file_info(file_path)
        
        # Check if file is tracked
        cursor.execute("""
        SELECT last_modified, file_hash, last_processed
        FROM file_tracking 
        WHERE file_path = ?
        """, (str(file_path),))
        
        result = cursor.fetchone()
        if not result:
            return True

        # Compare mtime and hash
        stored_mtime, stored_hash, last_processed = result
        if stored_mtime != current_info['mtime'] or stored_hash != current_info['hash']:
            return True
            
        # Check if data needs updating (if last processed was more than 24 hours ago)
        last_processed_dt = datetime.datetime.fromisoformat(last_processed)
        now = datetime.datetime.now()
        if (now - last_processed_dt).total_seconds() > 24 * 3600:  # 24 hours
            return True
            
        return False

def update_file_tracking(conn: sqlite3.Connection, file_path: Path):
    """Update file tracking information in database using existing connection."""
    cursor = conn.cursor()
    file_info = get_file_info(file_path)
    now = datetime.datetime.now().isoformat()
    
    # Check if file exists in tracking
    cursor.execute("""
    SELECT last_modified, file_hash 
    FROM file_tracking 
    WHERE file_path = ?
    """, (str(file_path),))
    
    result = cursor.fetchone()
    if result:
        stored_mtime, stored_hash = result
        if stored_mtime == file_info['mtime'] and stored_hash == file_info['hash']:
            # Only update last_processed if file hasn't changed
            cursor.execute("""
            UPDATE file_tracking 
            SET last_processed = ?
            WHERE file_path = ?
            """, (now, str(file_path)))
        else:
            # Update all fields if file has changed
            cursor.execute("""
            UPDATE file_tracking 
            SET last_modified = ?, file_hash = ?, last_processed = ?
            WHERE file_path = ?
            """, (file_info['mtime'], file_info['hash'], now, str(file_path)))
    else:
        # Insert new record
        cursor.execute("""
        INSERT INTO file_tracking 
        (file_path, last_modified, file_hash, last_processed)
        VALUES (?, ?, ?, ?)
        """, (str(file_path), file_info['mtime'], file_info['hash'], now)) 