import os
import sqlite3
import json
import csv
from pathlib import Path
from .core import calculate_file_hash, check_database_exists

def list_database_entries(db_path: Path, verbose: bool = False, verify: bool = False,
                         export_csv: Path = None, export_json: Path = None,
                         filter_status: str = None, filter_codec: str = None):
    """List entries in the database with optional export and filtering."""
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
        
        # Build query based on filters
        query = "SELECT * FROM {} WHERE 1=1"
        params = []
        
        if filter_status:
            table = "passed_files" if filter_status == "passed" else "failed_files"
            query = query.format(table)
        else:
            # If no status filter, query both tables
            query = "SELECT *, 'PASSED' as status FROM passed_files UNION ALL SELECT *, 'FAILED' as status FROM failed_files"
        
        if filter_codec:
            if filter_status:
                query += " AND codec = ?"
                params.append(filter_codec)
            else:
                query += " WHERE codec = ?"
                params.append(filter_codec)
        
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error executing query: {e}")
            return
        
        if not rows:
            print("No entries found matching the specified filters.")
            return
        
        # Get column names
        try:
            cursor.execute("PRAGMA table_info(passed_files)")
            columns = [row[1] for row in cursor.fetchall()]
            if not filter_status:
                columns.append('status')
        except sqlite3.Error as e:
            print(f"Error getting column information: {e}")
            return
        
        # Export to CSV if requested
        if export_csv:
            try:
                with open(export_csv, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(rows)
                print(f"Exported {len(rows)} entries to {export_csv}")
            except Exception as e:
                print(f"Error exporting to CSV: {e}")
        
        # Export to JSON if requested
        if export_json:
            try:
                data = []
                for row in rows:
                    entry = dict(zip(columns, row))
                    if verify:
                        try:
                            entry['exists'] = Path(entry['file_path']).exists()
                        except Exception:
                            entry['exists'] = False
                    data.append(entry)
                with open(export_json, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                print(f"Exported {len(rows)} entries to {export_json}")
            except Exception as e:
                print(f"Error exporting to JSON: {e}")
        
        # Print summary
        print(f"\nFound {len(rows)} entries")
        if filter_status:
            print(f"Status: {filter_status.upper()}")
        if filter_codec:
            print(f"Codec: {filter_codec}")
        
        # Print detailed information if verbose
        if verbose:
            print("\nDetailed Information:")
            print("-" * 80)
            for row in rows:
                try:
                    entry = dict(zip(columns, row))
                    print(f"\nFile: {entry['file_path']}")
                    print(f"Status: {entry.get('status', 'N/A')}")
                    print(f"Codec: {entry.get('codec', 'N/A')}")
                    print(f"Last Checked: {entry.get('last_checked', 'N/A')}")
                    if verify:
                        print(f"Exists: {Path(entry['file_path']).exists()}")
                    print("-" * 80)
                except Exception as e:
                    print(f"Error processing entry: {e}")
        
    except Exception as e:
        print(f"Error listing database entries: {e}")
    finally:
        if 'conn' in locals():
            conn.close() 