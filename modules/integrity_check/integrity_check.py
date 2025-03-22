import argparse
import utils  # Import utils from the root directory
from .check_integrity import check_integrity
from .check_file import get_codec
import os
import hashlib
from pathlib import Path
import concurrent.futures
from tqdm import tqdm
import datetime
from ..database_utils import init_db_with_wal, needs_processing, update_file_tracking, get_db_connection
import sqlite3
from ..logo_utils import print_integrity_check_logo

INTEGRITY_CHECK_SCHEMA = """
CREATE TABLE IF NOT EXISTS passed_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE,
    file_size INTEGER,
    md5_hash TEXT,
    last_checked TEXT,
    codec TEXT,
    codec_type TEXT,
    mtime REAL,
    status TEXT DEFAULT 'PASSED'
);

CREATE TABLE IF NOT EXISTS failed_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE,
    file_size INTEGER,
    error_message TEXT,
    last_checked TEXT,
    codec TEXT,
    codec_type TEXT,
    mtime REAL,
    status TEXT DEFAULT 'FAILED'
);
"""

def calculate_file_hash(file_path: str) -> str:
    """Calculate file MD5 hash."""
    hash_obj = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def check_file_integrity(file_path: str) -> dict:
    """Check integrity of a single file."""
    try:
        file_size = os.path.getsize(file_path)
        md5_hash = calculate_file_hash(file_path)
        
        return {
            'file_path': file_path,
            'file_size': file_size,
            'md5_hash': md5_hash,
            'status': 'OK'
        }
    except Exception as e:
        return {
            'file_path': file_path,
            'error': str(e),
            'status': 'ERROR'
        }

def check_integrity(args):
    """Handle the integrity check command."""
    if not args.path:
        print_integrity_check_logo()
        print("\nAvailable options for 'check' command:")
        print("-" * 50)
        print("Usage: audio_tool.py check [primary_option] [secondary_options] <file_or_directory>")
        print("\nPrimary options (mutually exclusive):")
        print("  --verify              Verify audio file integrity")
        print("    Secondary options:")
        print("        --verbose       Print results to console (no parallelism)")
        print("        --workers N     Number of worker processes for parallel checking")
        print("        --output FILE   Output file for results")
        print("        --format FORMAT Export format (txt/csv/json)")
        print("        --filter STATUS Filter results by status (PASSED/FAILED)")
        print("\n  --export             Export check results")
        print("    Secondary options:")
        print("        --output FILE   Output file for results")
        print("        --format FORMAT Export format (txt/csv/json)")
        print("        --filter STATUS Filter results by status (PASSED/FAILED)")
        print("\n  --summary            Show summary of check results")
        print("    Secondary options:")
        print("        --verbose       Print results to console")
        print("        --workers N     Number of worker processes")
        print("\nExample usage:")
        print("  audio_tool.py check --verify /path/to/music")
        print("  audio_tool.py check --verify --verbose /path/to/music")
        print("  audio_tool.py check --export --format csv /path/to/music")
        print("  audio_tool.py check --summary --workers 4 /path/to/music")
        return

    path = args.path
    output = args.output
    verbose = args.verbose
    num_workers = args.workers if args.workers is not None else (os.cpu_count() or 4)

    # Get configuration for database path
    config = utils.load_config()
    cache_folder = Path(config.get("cache_folder", "cache log"))
    db_path = cache_folder / "integrity_check.db"

    # Initialize database with WAL mode
    init_db_with_wal(db_path, INTEGRITY_CHECK_SCHEMA)

    # Determine files to check
    if os.path.isfile(path):
        audio_files = [Path(path)]
    elif os.path.isdir(path):
        audio_files = [file for ext in utils.AUDIO_EXTENSIONS for file in Path(path).rglob(f"*{ext}")]
        if not audio_files:
            print(f"No audio files found in '{path}'.")
            return
    else:
        print(f"'{path}' is not a file or directory.")
        return

    # Filter files that need processing
    files_to_process = [f for f in audio_files if needs_processing(db_path, f)]
    if not files_to_process:
        print("All files are up to date.")
        return

    total_files = len(files_to_process)
    processed_files = 0
    passed_files = 0
    failed_files = 0
    total_size = 0

    if verbose:
        # Sequential checking with console output
        for audio_file in files_to_process:
            result = check_file_integrity(str(audio_file))
            if result['status'] == 'OK':
                with get_db_connection(db_path) as conn:
                    save_integrity_check(result, conn)
                    update_file_tracking(conn, audio_file)
                passed_files += 1
                total_size += result.get('file_size', 0)
            else:
                failed_files += 1
            processed_files += 1
            print(f"Checked: {audio_file}")
            print(f"  Size: {result.get('file_size', 'N/A')}")
            print(f"  MD5: {result.get('md5_hash', 'N/A')}")
            print(f"  Status: {result['status']}\n")
    else:
        # Parallel checking with file output
        output_file = f"integrity_check_{datetime.datetime.now().strftime('%Y%m%d')}.txt" if output == "integrity_check.txt" else output
        with open(output_file, "w") as f:
            with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(check_file_integrity, str(file)) for file in files_to_process]
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Checking integrity"):
                    result = future.result()
                    if result['status'] == 'OK':
                        with get_db_connection(db_path) as conn:
                            save_integrity_check(result, conn)
                            update_file_tracking(conn, Path(result['file_path']))
                        passed_files += 1
                        total_size += result.get('file_size', 0)
                    else:
                        failed_files += 1
                    processed_files += 1
                    f.write(f"File: {result['file_path']}\n")
                    f.write(f"  Size: {result.get('file_size', 'N/A')}\n")
                    f.write(f"  MD5: {result.get('md5_hash', 'N/A')}\n")
                    f.write(f"  Status: {result['status']}\n\n")
        print(f"Integrity check complete. Results saved to '{output_file}'")

    # Print summary
    print("\nIntegrity Check Summary:")
    print("-" * 50)
    print(f"Total files processed: {processed_files}")
    print(f"Files passed: {passed_files}")
    print(f"Files failed: {failed_files}")
    print(f"Total size processed: {format_size(total_size)}")
    print(f"Success rate: {(passed_files/processed_files*100):.1f}%")
    print("-" * 50)

def format_size(size_in_bytes):
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"

def save_integrity_check(check_data: dict, conn: sqlite3.Connection):
    """Save integrity check results to database."""
    try:
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        
        # Get codec information
        from .check_file import normalize_codec
        codec = get_codec(check_data['file_path'])
        _, codec_type = normalize_codec(codec)
        
        # Determine which table to use
        table = 'passed_files' if check_data['status'] == 'OK' else 'failed_files'
        
        cursor.execute(f"""
        INSERT OR REPLACE INTO {table}
        (file_path, file_size, md5_hash, last_checked, codec, codec_type, mtime)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            check_data['file_path'],
            check_data.get('file_size', 0),
            check_data.get('md5_hash', ''),
            now,
            codec,
            codec_type,
            datetime.datetime.now().timestamp()
        ))
        
        conn.commit()
    except Exception as e:
        print(f"Error saving integrity check result: {e}")

def register_command(subparsers):
    """Register the 'check' command with the subparsers."""
    check_parser = subparsers.add_parser("check", help="Check audio file integrity (always saves to database)")
    
    # Create mutually exclusive group for primary options
    primary_group = check_parser.add_mutually_exclusive_group(required=False)
    primary_group.add_argument("--verify", action="store_true", help="Verify audio file integrity")
    primary_group.add_argument("--export", action="store_true", help="Export check results")
    primary_group.add_argument("--summary", action="store_true", help="Show summary of check results")
    
    # Secondary options that can be combined with primary options
    check_parser.add_argument("path", nargs='?', type=utils.path_type, help="File or directory to check")
    check_parser.add_argument("-o", "--output", default="integrity_check.txt", help="Output file for results")
    check_parser.add_argument("--verbose", action="store_true", help="Print results to console (no parallelism)")
    check_parser.add_argument("--workers", type=int, help="Number of worker processes for parallel checking")
    check_parser.add_argument("--format", choices=["txt", "csv", "json"], help="Export format (txt/csv/json)")
    check_parser.add_argument("--filter", choices=["PASSED", "FAILED"], help="Filter results by status")
    
    check_parser.set_defaults(func=check_integrity)