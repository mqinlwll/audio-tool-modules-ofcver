import time
import datetime
from pathlib import Path
from .core import check_database_exists, get_database_summary
import sqlite3

def watch_database(db_path: Path, interval: int = 5):
    """Watch the database for changes in real-time."""
    if not check_database_exists(db_path):
        print(f"Error: Database '{db_path}' not found.")
        return

    print(f"Watching database at: {db_path}")
    print(f"Checking for updates every {interval} seconds (Ctrl+C to stop)")

    last_passed, last_failed, _ = get_database_summary(db_path)
    print(f"Initial count - Passed: {last_passed}, Failed: {last_failed}")

    try:
        while True:
            current_passed, current_failed, error = get_database_summary(db_path)
            if error:
                print(error)
                return

            if current_passed != last_passed or current_failed != last_failed:
                print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Database updated:")
                print(f"Passed: {last_passed} → {current_passed}")
                print(f"Failed: {last_failed} → {current_failed}")
                last_passed, last_failed = current_passed, current_failed

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped watching database.")
    except Exception as e:
        print(f"Error while watching database: {e}")

def quick_check_database(db_path: Path):
    """Perform a quick check of the database status."""
    try:
        if not db_path.exists():
            print(f"Error: Database file not found: {db_path}")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Validate database structure
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('passed_files', 'failed_files')")
            tables = cursor.fetchall()
            if len(tables) != 2:
                print("Error: Database structure is invalid. Missing required tables.")
                return
        except sqlite3.Error as e:
            print(f"Error validating database structure: {e}")
            return
        
        # Get basic statistics with error handling
        try:
            cursor.execute("SELECT COUNT(*) FROM passed_files")
            passed_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM failed_files")
            failed_count = cursor.fetchone()[0]
            total_count = passed_count + failed_count
        except sqlite3.Error as e:
            print(f"Error getting basic statistics: {e}")
            return
        
        # Get codec statistics with error handling
        try:
            cursor.execute("""
                SELECT codec, COUNT(*) as count 
                FROM passed_files 
                WHERE codec IS NOT NULL AND codec != 'unknown'
                GROUP BY codec
                ORDER BY count DESC
            """)
            passed_codecs = cursor.fetchall()
            
            cursor.execute("""
                SELECT codec, COUNT(*) as count 
                FROM failed_files 
                WHERE codec IS NOT NULL AND codec != 'unknown'
                GROUP BY codec
                ORDER BY count DESC
            """)
            failed_codecs = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting codec statistics: {e}")
            passed_codecs = []
            failed_codecs = []
        
        # Get recent activity with error handling
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM passed_files 
                WHERE last_checked >= date('now', '-7 days')
            """)
            recent_passed = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM failed_files 
                WHERE last_checked >= date('now', '-7 days')
            """)
            recent_failed = cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting recent activity: {e}")
            recent_passed = 0
            recent_failed = 0
        
        conn.close()
        
        # Print report
        print("\nIntegrity Check Database Status")
        print("=" * 50)
        print(f"Total Files: {total_count}")
        if total_count > 0:
            print(f"Passed: {passed_count} ({passed_count/total_count*100:.1f}%)")
            print(f"Failed: {failed_count} ({failed_count/total_count*100:.1f}%)")
        else:
            print("No files found in database")
        
        if passed_codecs or failed_codecs:
            print("\nCodec Distribution")
            print("-" * 50)
            if passed_codecs:
                print("Passed Files:")
                for codec, count in passed_codecs:
                    print(f"  {codec}: {count} files ({count/passed_count*100:.1f}%)")
            if failed_codecs:
                print("\nFailed Files:")
                for codec, count in failed_codecs:
                    print(f"  {codec}: {count} files ({count/failed_count*100:.1f}%)")
        
        print("\nRecent Activity (Last 7 Days)")
        print("-" * 50)
        print(f"Passed: {recent_passed} files")
        print(f"Failed: {recent_failed} files")
        
        # Health status
        print("\nHealth Status")
        print("-" * 50)
        if total_count == 0:
            print("⚠️ Database is empty")
        elif failed_count == 0:
            print("✅ Database is healthy - all files passed integrity check")
        elif failed_count < total_count * 0.1:
            print("⚠️ Database has some issues - less than 10% of files failed")
        else:
            print("❌ Database needs attention - more than 10% of files failed")
            
    except Exception as e:
        print(f"Error checking database: {e}")
        if 'conn' in locals():
            conn.close()

def format_size(size_in_bytes):
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB" 