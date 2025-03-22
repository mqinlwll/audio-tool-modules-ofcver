from pathlib import Path
import sqlite3
import os
from .lock_utils import acquire_lock, release_lock, LOCK_FILE
from .file_hash import calculate_file_hash

def determine_action(db_path: Path, file_path: str, force_recheck: bool = False) -> tuple:
    """Determine the action for a file with process-safe database access."""
    if force_recheck:
        try:
            current_mtime = os.path.getmtime(file_path)
            current_hash = calculate_file_hash(file_path)
            return 'RUN_FFMPEG', None, current_hash, current_mtime
        except FileNotFoundError:
            return 'FILE_NOT_FOUND', None, None, None

    try:
        current_mtime = os.path.getmtime(file_path)
    except FileNotFoundError:
        return 'FILE_NOT_FOUND', None, None, None

    lock_fd = acquire_lock(LOCK_FILE)
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        for table in ['passed_files', 'failed_files']:
            cursor.execute(f"SELECT status, file_hash, mtime FROM {table} WHERE file_path = ?", (file_path,))
            result = cursor.fetchone()
            if result:
                stored_status, stored_hash, stored_mtime = result
                if stored_mtime == current_mtime:
                    conn.close()
                    return 'USE_CACHED', stored_status, None, current_mtime
                else:
                    current_hash = calculate_file_hash(file_path)
                    if stored_hash == current_hash:
                        conn.close()
                        return 'UPDATE_MTIME', stored_status, current_hash, current_mtime
                    else:
                        conn.close()
                        return 'RUN_FFMPEG', None, current_hash, current_mtime
        conn.close()
        current_hash = calculate_file_hash(file_path)
        return 'RUN_FFMPEG', None, current_hash, current_mtime
    finally:
        release_lock(lock_fd)