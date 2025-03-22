from pathlib import Path
import sqlite3

def initialize_database(db_path: Path):
    """Initialize the SQLite database with WAL mode and busy timeout."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passed_files (
            file_path TEXT PRIMARY KEY,
            file_hash TEXT,
            mtime REAL,
            status TEXT,
            last_checked TEXT,
            codec TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS failed_files (
            file_path TEXT PRIMARY KEY,
            file_hash TEXT,
            mtime REAL,
            status TEXT,
            last_checked TEXT,
            codec TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database initialized with WAL mode at: {db_path}")