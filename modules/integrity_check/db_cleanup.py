from pathlib import Path
import sqlite3
import os
from .lock_utils import acquire_lock, release_lock, LOCK_FILE

def cleanup_database(db_path: Path):
    """Remove database entries for files that no longer exist with locking."""
    lock_fd = acquire_lock(LOCK_FILE)
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        for table in ['passed_files', 'failed_files']:
            cursor.execute(f"SELECT file_path FROM {table}")
            for (file_path,) in cursor.fetchall():
                if not os.path.exists(file_path):
                    cursor.execute(f"DELETE FROM {table} WHERE file_path = ?", (file_path,))
        conn.commit()
        conn.close()
    finally:
        release_lock(lock_fd)