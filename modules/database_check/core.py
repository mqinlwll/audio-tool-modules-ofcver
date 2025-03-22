import os
import hashlib
from pathlib import Path
import sqlite3

def calculate_file_hash(file_path: str) -> str:
    """Calculate the MD5 hash of a file."""
    md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                md5.update(chunk)
        return md5.hexdigest()
    except (FileNotFoundError, PermissionError):
        return None

def check_database_exists(db_path: Path) -> bool:
    """Check if the database file exists."""
    return db_path.exists()

def get_database_summary(db_path: Path) -> tuple:
    """Get a summary of the database contents."""
    if not check_database_exists(db_path):
        return 0, 0, "Database not found"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM passed_files")
    passed_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM failed_files")
    failed_count = cursor.fetchone()[0]

    conn.close()
    return passed_count, failed_count, None 