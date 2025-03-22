from pathlib import Path
import os
import datetime
import sqlite3
import concurrent.futures
from tqdm import tqdm
import utils
from .db_init import initialize_database
from .process_file import process_file
from .db_cleanup import cleanup_database
from .lock_utils import acquire_lock, release_lock, LOCK_FILE

def check_integrity(args):
    """Handle the 'check' command with concurrent database access."""
    if not utils.is_ffmpeg_installed():
        print("Error: FFmpeg is not installed or not in your PATH.")
        return

    path = args.path
    verbose = getattr(args, 'verbose', False)
    summary = getattr(args, 'summary', False)
    save_log = getattr(args, 'save_log', False)
    force_recheck = getattr(args, 'recheck', False)
    num_workers = args.workers if args.workers is not None else (os.cpu_count() or 4)
    config = utils.load_config()

    cache_folder = Path(config.get("cache_folder", "cache log"))
    db_path = cache_folder / "integrity_check.db"
    log_folder = Path(config.get("log_folder", "Logs"))
    log_folder.mkdir(parents=True, exist_ok=True)

    initialize_database(db_path)

    if os.path.isfile(path) and os.path.splitext(path)[1].lower() in utils.AUDIO_EXTENSIONS:
        audio_files = [path]
    elif os.path.isdir(path):
        audio_files = utils.get_audio_files(path)
        if not audio_files:
            print(f"No audio files found in '{path}'.")
            return
    else:
        print(f"'{path}' is not a file or directory.")
        return

    create_log = save_log or (not verbose and not summary)
    if create_log:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        failed_log_filename = log_folder / f"Failed-{timestamp}.txt"
        success_log_filename = log_folder / f"Success-{timestamp}.txt"
        failed_log_file = open(failed_log_filename, 'w', encoding='utf-8')
        success_log_file = open(success_log_filename, 'w', encoding='utf-8')
    else:
        failed_log_file = None
        success_log_file = None

    total_files = len(audio_files)

    if verbose:
        all_results = []
        for file_path in audio_files:
            action, status, message, _, extra = process_file(db_path, file_path, force_recheck)
            if action in ['USE_CACHED', 'UPDATE_MTIME', 'RUN_FFMPEG']:
                all_results.append((status, message, file_path))
                result_line = f"{status} {file_path}" + (f": {message}" if message else "")
                print(result_line)
                if create_log:
                    (success_log_file if status == "PASSED" else failed_log_file).write(result_line + "\n")
            if action == 'UPDATE_MTIME':
                lock_fd = acquire_lock(LOCK_FILE)
                try:
                    conn = sqlite3.connect(db_path, timeout=5)
                    cursor = conn.cursor()
                    table = 'passed_files' if status == 'PASSED' else 'failed_files'
                    cursor.execute(f"UPDATE {table} SET mtime = ? WHERE file_path = ?", (extra, file_path))
                    conn.commit()
                    conn.close()
                finally:
                    release_lock(lock_fd)
            elif action == 'RUN_FFMPEG':
                lock_fd = acquire_lock(LOCK_FILE)
                try:
                    conn = sqlite3.connect(db_path, timeout=5)
                    cursor = conn.cursor()
                    file_path, file_hash, mtime, status, codec = extra
                    if status == 'PASSED':
                        cursor.execute("DELETE FROM failed_files WHERE file_path = ?", (file_path,))
                        table = 'passed_files'
                    else:
                        cursor.execute("DELETE FROM passed_files WHERE file_path = ?", (file_path,))
                        table = 'failed_files'
                    cursor.execute(f'''
                        INSERT OR REPLACE INTO {table} (file_path, file_hash, mtime, status, last_checked, codec)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (file_path, file_hash, mtime, status, datetime.datetime.now().isoformat(), codec))
                    conn.commit()
                    conn.close()
                finally:
                    release_lock(lock_fd)
    else:
        all_results = []
        mtime_updates_passed = []
        mtime_updates_failed = []
        db_updates_passed = []
        db_updates_failed = []
        processed_count = 0

        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(process_file, db_path, file, force_recheck) for file in audio_files]
            with tqdm(total=len(futures), desc="Processing files") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    action, status, message, file_path, extra = result
                    if action == 'USE_CACHED':
                        all_results.append((status, message, file_path))
                    elif action == 'UPDATE_MTIME':
                        stored_status = status
                        current_mtime = extra
                        all_results.append((stored_status, message, file_path))
                        if stored_status == 'PASSED':
                            mtime_updates_passed.append((file_path, current_mtime))
                        else:
                            mtime_updates_failed.append((file_path, current_mtime))
                    elif action == 'RUN_FFMPEG':
                        update_info = extra
                        all_results.append((status, message, file_path))
                        if status == 'PASSED':
                            db_updates_passed.append(update_info)
                        else:
                            db_updates_failed.append(update_info)
                    pbar.update(1)
                    processed_count += 1

                    if processed_count % 100 == 0:
                        lock_fd = acquire_lock(LOCK_FILE)
                        try:
                            conn = sqlite3.connect(db_path, timeout=5)
                            cursor = conn.cursor()
                            if mtime_updates_passed:
                                cursor.executemany("UPDATE passed_files SET mtime = ? WHERE file_path = ?",
                                                   mtime_updates_passed)
                                mtime_updates_passed = []
                            if mtime_updates_failed:
                                cursor.executemany("UPDATE failed_files SET mtime = ? WHERE file_path = ?",
                                                   mtime_updates_failed)
                                mtime_updates_failed = []
                            if db_updates_passed:
                                for file_path, _, _, _ in db_updates_passed:
                                    cursor.execute("DELETE FROM failed_files WHERE file_path = ?", (file_path,))
                                cursor.executemany('''
                                    INSERT OR REPLACE INTO passed_files (file_path, file_hash, mtime, status, last_checked, codec)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', [(fp, fh, mt, st, datetime.datetime.now().isoformat(), codec)
                                      for fp, fh, mt, st, codec in db_updates_passed])
                                db_updates_passed = []
                            if db_updates_failed:
                                for file_path, _, _, _ in db_updates_failed:
                                    cursor.execute("DELETE FROM passed_files WHERE file_path = ?", (file_path,))
                                cursor.executemany('''
                                    INSERT OR REPLACE INTO failed_files (file_path, file_hash, mtime, status, last_checked, codec)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', [(fp, fh, mt, st, datetime.datetime.now().isoformat(), codec)
                                      for fp, fh, mt, st, codec in db_updates_failed])
                                db_updates_failed = []
                            conn.commit()
                            conn.close()
                        finally:
                            release_lock(lock_fd)

        if mtime_updates_passed or mtime_updates_failed or db_updates_passed or db_updates_failed:
            lock_fd = acquire_lock(LOCK_FILE)
            try:
                conn = sqlite3.connect(db_path, timeout=5)
                cursor = conn.cursor()
                if mtime_updates_passed:
                    cursor.executemany("UPDATE passed_files SET mtime = ? WHERE file_path = ?",
                                       mtime_updates_passed)
                if mtime_updates_failed:
                    cursor.executemany("UPDATE failed_files SET mtime = ? WHERE file_path = ?",
                                       mtime_updates_failed)
                if db_updates_passed:
                    for file_path, _, _, _ in db_updates_passed:
                        cursor.execute("DELETE FROM failed_files WHERE file_path = ?", (file_path,))
                    cursor.executemany('''
                        INSERT OR REPLACE INTO passed_files (file_path, file_hash, mtime, status, last_checked, codec)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', [(fp, fh, mt, st, datetime.datetime.now().isoformat(), codec)
                          for fp, fh, mt, st, codec in db_updates_passed])
                if db_updates_failed:
                    for file_path, _, _, _ in db_updates_failed:
                        cursor.execute("DELETE FROM passed_files WHERE file_path = ?", (file_path,))
                    cursor.executemany('''
                        INSERT OR REPLACE INTO failed_files (file_path, file_hash, mtime, status, last_checked, codec)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', [(fp, fh, mt, st, datetime.datetime.now().isoformat(), codec)
                          for fp, fh, mt, st, codec in db_updates_failed])
                conn.commit()
                conn.close()
            finally:
                release_lock(lock_fd)

    cleanup_database(db_path)

    passed_count = sum(1 for status, _, _ in all_results if status == "PASSED")
    failed_count = sum(1 for status, _, _ in all_results if status == "FAILED")

    if create_log and not verbose:
        for status, message, file_path in all_results:
            result_line = f"{status} {file_path}" + (f": {message}" if message else "")
            (success_log_file if status == "PASSED" else failed_log_file).write(result_line + "\n")

    summary_text = f"\nSummary:\nTotal files: {total_files}\nPassed: {passed_count}\nFailed: {failed_count}\n"
    if verbose or summary:
        print(summary_text)
    if create_log:
        failed_log_file.write(summary_text)
        success_log_file.write(summary_text)
        failed_log_file.close()
        success_log_file.close()
        print(f"Check complete. Logs saved to '{failed_log_filename}' and '{success_log_filename}'")
    else:
        print("Check complete.")