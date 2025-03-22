import os
import sqlite3
from pathlib import Path
from tqdm import tqdm

def update_database_schema(db_path: Path):
    """Update the database schema to include new columns if necessary, with a progress bar."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check and update 'passed_files' table
    cursor.execute("PRAGMA table_info(passed_files)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'mtime' not in columns:
        print("Adding 'mtime' column to passed_files...")
        cursor.execute("ALTER TABLE passed_files ADD COLUMN mtime REAL")
        # Get all file paths to update
        cursor.execute("SELECT file_path FROM passed_files")
        file_paths = [row[0] for row in cursor.fetchall()]
        # Update mtime with progress bar
        with tqdm(total=len(file_paths), desc="Updating mtime in passed_files") as pbar:
            for file_path in file_paths:
                try:
                    mtime = os.path.getmtime(file_path)
                    cursor.execute("UPDATE passed_files SET mtime = ? WHERE file_path = ?", (mtime, file_path))
                except (FileNotFoundError, OSError):
                    pass  # Leave mtime as NULL if file is inaccessible
                pbar.update(1)  # Increment progress bar

    # Check and update 'failed_files' table
    cursor.execute("PRAGMA table_info(failed_files)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'mtime' not in columns:
        print("Adding 'mtime' column to failed_files...")
        cursor.execute("ALTER TABLE failed_files ADD COLUMN mtime REAL")
        # Get all file paths to update
        cursor.execute("SELECT file_path FROM failed_files")
        file_paths = [row[0] for row in cursor.fetchall()]
        # Update mtime with progress bar
        with tqdm(total=len(file_paths), desc="Updating mtime in failed_files") as pbar:
            for file_path in file_paths:
                try:
                    mtime = os.path.getmtime(file_path)
                    cursor.execute("UPDATE failed_files SET mtime = ? WHERE file_path = ?", (mtime, file_path))
                except (FileNotFoundError, OSError):
                    pass  # Leave mtime as NULL if file is inaccessible
                pbar.update(1)  # Increment progress bar

    conn.commit()
    conn.close()
    print("Database schema updated successfully.") 