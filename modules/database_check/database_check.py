import datetime
from pathlib import Path
import utils  # Import from root directory
from .core import get_database_summary, check_database_exists
from .schema import update_database_schema
from .list_entries import list_database_entries
from .monitor import watch_database, quick_check_database
import os
import json
import csv
import sqlite3
from ..database_utils import init_db_with_wal, get_db_connection
from ..logo_utils import print_database_check_logo
from tqdm import tqdm

def format_size(size_in_bytes):
    """Format size in bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} TB"

def get_database_info(db_path: Path) -> dict:
    """Get information about a database file."""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get row counts for each table
            table_info = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                table_info[table] = {
                    "row_count": count,
                    "columns": columns
                }
        
        # Get file info
        size_bytes = db_path.stat().st_size
        modified = datetime.datetime.fromtimestamp(db_path.stat().st_mtime)
        
        return {
            "name": db_path.name,
            "size": size_bytes,
            "modified": modified,
            "tables": table_info,
            "description": get_database_description(db_path.name)
        }
    except Exception as e:
        return {
            "name": db_path.name,
            "error": str(e)
        }

def get_database_description(db_name: str) -> str:
    """Get a description of what the database is used for."""
    descriptions = {
        "album_metadata.db": "Stores album metadata including title, artist, album, ISRC, and UPC",
        "audio_analysis.db": "Stores audio technical details including codec, bitrate, sample rate, and channels"
    }
    return descriptions.get(db_name, "Unknown database")

def list_databases(args):
    """List all databases in the cache folder with their information."""
    config = utils.load_config()
    cache_folder = Path(config.get("cache_folder", "cache log"))
    
    if not cache_folder.exists():
        print(f"Cache folder '{cache_folder}' does not exist.")
        return
    
    databases = list(cache_folder.glob("*.db"))
    if not databases:
        print("No databases found.")
        return
    
    print("\nAvailable databases:")
    print("===================")
    
    for db_path in databases:
        info = get_database_info(db_path)
        if "error" in info:
            print(f"\n{info['name']}:")
            print(f"  Error: {info['error']}")
            continue
            
        size_str = format_size(info["size"])
        modified_str = info["modified"].strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n{info['name']}:")
        print(f"  Description: {info['description']}")
        print(f"  Size: {size_str}")
        print(f"  Last modified: {modified_str}")
        print("  Tables:")
        for table_name, table_info in info["tables"].items():
            print(f"    - {table_name}: {table_info['row_count']} rows")
            print(f"      Columns: {', '.join(table_info['columns'])}")

def show_filtered_results(db_path: Path, filter_status: str = None, codec_filter: str = None, codec_type_filter: str = None):
    """Display filtered results in the CLI."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\nFiltered results for database: {db_path.name}")
        print("-" * 80)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for (table,) in tables:
            try:
                # Build query based on filters
                query = f"SELECT * FROM {table}"
                params = []
                conditions = []
                
                if filter_status and table in ['passed_files', 'failed_files']:
                    conditions.append("status = ?")
                    params.append(filter_status)
                
                if codec_filter:
                    conditions.append("LOWER(codec) = LOWER(?)")
                    params.append(codec_filter)
                
                if codec_type_filter:
                    conditions.append("LOWER(codec_type) = LOWER(?)")
                    params.append(codec_type_filter)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                if rows:
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    print(f"\nTable: {table}")
                    print(f"Found {len(rows)} matching records")
                    print("-" * 80)
                    
                    # Print header
                    print(" | ".join(f"{col:<20}" for col in columns))
                    print("-" * 80)
                    
                    # Print rows (limit to 10 rows)
                    for row in rows[:10]:
                        print(" | ".join(f"{str(val)[:20]:<20}" for val in row))
                    
                    if len(rows) > 10:
                        print(f"\n... and {len(rows) - 10} more records")
                    
            except Exception as e:
                if "no such column: codec" not in str(e) and "no such column: codec_type" not in str(e):
                    print(f"\nError querying table {table}: {e}")
                continue
        
        conn.close()
        print("\n" + "-" * 80)
        
    except Exception as e:
        print(f"Error showing filtered results: {e}")
        if 'conn' in locals():
            conn.close()

def check_database(args):
    """Handle the database check command."""
    try:
        config = utils.load_config()
        cache_folder = Path(config.get("cache_folder", "cache log"))
        
        if not cache_folder.exists():
            print(f"Error: Cache folder not found: {cache_folder}")
            return

        if args.update:
            print("Checking for databases to update...")
            updated = False
            db_files = list(cache_folder.glob("*.db"))
            
            if not db_files:
                print("No databases found to update.")
                return
                
            print(f"Found {len(db_files)} database(s) to process")
            for db_file in tqdm(db_files, desc="Updating databases"):
                try:
                    if migrate_database(db_file):
                        updated = True
                except Exception as e:
                    print(f"\nError updating database {db_file.name}: {e}")
                    
            if not updated:
                print("No databases needed updating.")
            return

        if args.list:
            list_databases(args)
            return

        if args.check:
            integrity_db = cache_folder / "integrity_check.db"
            if not integrity_db.exists():
                print(f"Error: Integrity check database not found: {integrity_db}")
                return
            quick_check_database(integrity_db)
            return

        if args.show:
            if args.database:
                # Show filtered results for specific database
                db_file = cache_folder / args.database
                if not db_file.exists():
                    print(f"Error: Database not found: {db_file}")
                    return
                show_filtered_results(db_file, args.filter, args.codec, args.codec_type)
            else:
                # Show filtered results for all databases
                for db_file in cache_folder.glob("*.db"):
                    show_filtered_results(db_file, args.filter, args.codec, args.codec_type)
            return

        if args.csv or args.json:
            if args.database:
                # Export specific database
                db_file = cache_folder / args.database
                if not db_file.exists():
                    print(f"Error: Database not found: {db_file}")
                    return
                if args.csv:
                    export_database(db_file, 'csv', args.filter, args.codec, args.codec_type)
                if args.json:
                    export_database(db_file, 'json', args.filter, args.codec, args.codec_type)
            else:
                # Export all databases
                for db_file in cache_folder.glob("*.db"):
                    if args.csv:
                        export_database(db_file, 'csv', args.filter, args.codec, args.codec_type)
                    if args.json:
                        export_database(db_file, 'json', args.filter, args.codec, args.codec_type)
            return

        # Show help if no options are specified
        print_database_check_logo()
        print("\nAvailable options for 'dbcheck' command:")
        print("-" * 50)
        print("Usage: audio_tool.py dbcheck [primary_option] [secondary_options]")
        print("\nPrimary options (mutually exclusive):")
        print("  --list                List all available databases with their status")
        print("    Secondary options:")
        print("        --show          Display filtered results in CLI")
        print("        --verbose       Show detailed information")
        print("\n  --update             Update databases to new schema and enable WAL mode")
        print("    Secondary options:")
        print("        --verbose       Show detailed information")
        print("\n  --csv                Export database contents to CSV format")
        print("    Secondary options:")
        print("        --database DB   Specific database to export (e.g., audio_analysis.db)")
        print("        --filter STATUS Filter export by status (PASSED/FAILED) [integrity_check.db only]")
        print("        --codec CODEC   Filter export by codec type (e.g., flac, mp3)")
        print("        --codec-type TYPE Filter export by codec type (lossless/lossy) [integrity_check.db only]")
        print("        --show          Display filtered results in CLI")
        print("        --verbose       Show detailed information")
        print("\n  --json               Export database contents to JSON format")
        print("    Secondary options:")
        print("        --database DB   Specific database to export (e.g., audio_analysis.db)")
        print("        --filter STATUS Filter export by status (PASSED/FAILED) [integrity_check.db only]")
        print("        --codec CODEC   Filter export by codec type (e.g., flac, mp3)")
        print("        --codec-type TYPE Filter export by codec type (lossless/lossy) [integrity_check.db only]")
        print("        --show          Display filtered results in CLI")
        print("        --verbose       Show detailed information")
        print("\n  --check              Check integrity check database status")
        print("    Secondary options:")
        print("        --verbose       Show detailed information")
        print("        --verify        Verify file existence and hashes")
        print("\n  --show               Display database contents")
        print("    Secondary options:")
        print("        --database DB   Specific database to show (e.g., audio_analysis.db)")
        print("        --filter STATUS Filter results by status (PASSED/FAILED) [integrity_check.db only]")
        print("        --codec CODEC   Filter results by codec type (e.g., flac, mp3)")
        print("        --codec-type TYPE Filter results by codec type (lossless/lossy) [integrity_check.db only]")
        print("        --verbose       Show detailed information")
        print("\nExample usage:")
        print("  audio_tool.py dbcheck --list")
        print("  audio_tool.py dbcheck --list --show")
        print("  audio_tool.py dbcheck --update")
        print("  audio_tool.py dbcheck --csv --database audio_analysis.db")
        print("  audio_tool.py dbcheck --json --filter PASSED")
        print("  audio_tool.py dbcheck --check --verify")
        print("  audio_tool.py dbcheck --show --database audio_analysis.db")
        print("  audio_tool.py dbcheck --show --database integrity_check.db --codec-type lossless")

    except Exception as e:
        print(f"Error: {e}")
        return

def export_database(db_path: Path, format: str, filter_status: str = None, codec_filter: str = None, codec_type_filter: str = None):
    """Export database contents to specified format."""
    try:
        # Create exports directory if it doesn't exist
        exports_dir = Path("exports")
        exports_dir.mkdir(exist_ok=True)
        
        # Create subfolder based on database name
        db_name = db_path.stem
        db_export_dir = exports_dir / db_name
        db_export_dir.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"Exporting database: {db_path.name}")
        print(f"Export directory: {db_export_dir}")
        
        for (table,) in tqdm(tables, desc="Exporting tables"):
            try:
                # Build query based on filters
                query = f"SELECT * FROM {table}"
                params = []
                conditions = []
                
                if filter_status and table in ['passed_files', 'failed_files']:
                    conditions.append("status = ?")
                    params.append(filter_status)
                
                if codec_filter:
                    conditions.append("LOWER(codec) = LOWER(?)")
                    params.append(codec_filter)
                
                if codec_type_filter:
                    conditions.append("LOWER(codec_type) = LOWER(?)")
                    params.append(codec_type_filter)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                if format == 'csv':
                    csv_path = db_export_dir / f"{table}.csv"
                    with open(csv_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(columns)
                        writer.writerows(rows)
                    print(f"Exported {table} to {csv_path}")
                    
                elif format == 'json':
                    json_path = db_export_dir / f"{table}.json"
                    data = [dict(zip(columns, row)) for row in rows]
                    with open(json_path, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    print(f"Exported {table} to {json_path}")
                    
            except Exception as e:
                if "no such column: codec" in str(e) or "no such column: codec_type" in str(e):
                    # For tables without codec column, export without filtering
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    if format == 'csv':
                        csv_path = db_export_dir / f"{table}.csv"
                        with open(csv_path, 'w', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(columns)
                            writer.writerows(rows)
                        print(f"Exported {table} to {csv_path}")
                        
                    elif format == 'json':
                        json_path = db_export_dir / f"{table}.json"
                        data = [dict(zip(columns, row)) for row in rows]
                        with open(json_path, 'w') as f:
                            json.dump(data, f, indent=2, default=str)
                        print(f"Exported {table} to {json_path}")
                else:
                    print(f"\nError exporting table {table}: {e}")
                continue
        
        conn.close()
        print(f"\nExport complete. Files saved in: {db_export_dir}")
        
    except Exception as e:
        print(f"Error exporting database: {e}")
        if 'conn' in locals():
            conn.close()

def migrate_database(db_path: Path) -> bool:
    """Migrate database to new schema and enable WAL mode."""
    try:
        # Get the module name from the database filename
        module_name = db_path.stem.replace('_db', '').replace('_', '')
        
        # Import the corresponding module's schema
        if module_name == 'audioanalysis':
            from ..audio_analysis.schema import AUDIO_ANALYSIS_SCHEMA as schema
        elif module_name == 'albummetadata':
            from ..album_counter.schema import ALBUM_METADATA_SCHEMA as schema
        elif module_name == 'integritycheck':
            from ..integrity_check.integrity_check import INTEGRITY_CHECK_SCHEMA as schema
        else:
            print(f"Unknown database type: {db_path.name}")
            return False

        # Create a backup
        backup_path = db_path.with_suffix('.db.bak')
        if not backup_path.exists():
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"Created backup: {backup_path}")

        # Enable WAL mode and update schema
        init_db_with_wal(db_path, schema)
        
        # Update codec information for integrity check database
        if module_name == 'integritycheck':
            update_codec_information(db_path)
            
        print(f"Updated schema and enabled WAL mode for: {db_path}")
        return True

    except Exception as e:
        print(f"Error migrating database {db_path}: {e}")
        return False

def update_codec_information(db_path: Path):
    """Update codec information for files in the integrity check database."""
    print("Updating codec information...")
    from ..integrity_check.check_file import get_codec, normalize_codec
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if codec and codec_type columns exist
        cursor.execute("PRAGMA table_info(passed_files)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'codec' not in columns:
            print("Adding codec column to passed_files table...")
            cursor.execute("ALTER TABLE passed_files ADD COLUMN codec TEXT")
        if 'codec_type' not in columns:
            print("Adding codec_type column to passed_files table...")
            cursor.execute("ALTER TABLE passed_files ADD COLUMN codec_type TEXT")
        
        cursor.execute("PRAGMA table_info(failed_files)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'codec' not in columns:
            print("Adding codec column to failed_files table...")
            cursor.execute("ALTER TABLE failed_files ADD COLUMN codec TEXT")
        if 'codec_type' not in columns:
            print("Adding codec_type column to failed_files table...")
            cursor.execute("ALTER TABLE failed_files ADD COLUMN codec_type TEXT")
        
        # Update passed files
        cursor.execute("SELECT file_path FROM passed_files WHERE codec IS NULL OR codec = 'unknown' OR codec_type IS NULL")
        passed_files = cursor.fetchall()
        print(f"Found {len(passed_files)} passed files without complete codec information")
        
        if passed_files:
            print("Updating codec information for passed files...")
            for (file_path,) in tqdm(passed_files, desc="Processing passed files"):
                try:
                    raw_codec = get_codec(file_path)
                    codec, codec_type = normalize_codec(raw_codec)
                    cursor.execute("""
                        UPDATE passed_files 
                        SET codec = ?, codec_type = ? 
                        WHERE file_path = ?
                    """, (codec, codec_type, file_path))
                except Exception as e:
                    print(f"\nError updating codec for {file_path}: {e}")
        
        # Update failed files
        cursor.execute("SELECT file_path FROM failed_files WHERE codec IS NULL OR codec = 'unknown' OR codec_type IS NULL")
        failed_files = cursor.fetchall()
        print(f"Found {len(failed_files)} failed files without complete codec information")
        
        if failed_files:
            print("Updating codec information for failed files...")
            for (file_path,) in tqdm(failed_files, desc="Processing failed files"):
                try:
                    raw_codec = get_codec(file_path)
                    codec, codec_type = normalize_codec(raw_codec)
                    cursor.execute("""
                        UPDATE failed_files 
                        SET codec = ?, codec_type = ? 
                        WHERE file_path = ?
                    """, (codec, codec_type, file_path))
                except Exception as e:
                    print(f"\nError updating codec for {file_path}: {e}")
        
        conn.commit()
        print("Codec information update complete")
        
    except Exception as e:
        print(f"Error updating codec information: {e}")
        conn.rollback()
    finally:
        conn.close()

def register_command(subparsers):
    """Register the database check command."""
    db_parser = subparsers.add_parser("dbcheck", help="Check and manage databases")
    
    # Create mutually exclusive group for primary options
    primary_group = db_parser.add_mutually_exclusive_group(required=False)
    primary_group.add_argument("--list", action="store_true", help="List all available databases")
    primary_group.add_argument("--update", action="store_true", help="Update databases to new schema and enable WAL mode")
    primary_group.add_argument("--csv", action="store_true", help="Export database contents to CSV format")
    primary_group.add_argument("--json", action="store_true", help="Export database contents to JSON format")
    primary_group.add_argument("--check", action="store_true", help="Check integrity check database status")
    primary_group.add_argument("--show", action="store_true", help="Display database contents")
    
    # Secondary options that can be combined with primary options
    db_parser.add_argument("--database", help="Specific database to process (e.g., audio_analysis.db)")
    db_parser.add_argument("--filter", choices=["PASSED", "FAILED"], help="Filter results by status")
    db_parser.add_argument("--codec", help="Filter by codec type (e.g., flac, mp3, aac)")
    db_parser.add_argument("--codec-type", choices=["lossless", "lossy"], help="Filter by codec type (lossless/lossy)")
    db_parser.add_argument("--verbose", action="store_true", help="Show detailed information")
    db_parser.add_argument("--verify", action="store_true", help="Verify file existence and hashes")
    
    db_parser.set_defaults(func=check_database)

if __name__ == "__main__":
    # This is just for standalone testing - typically this would be part of a larger script
    import argparse
    parser = argparse.ArgumentParser(description="Database integrity checker")
    subparsers = parser.add_subparsers()
    register_command(subparsers)
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help() 