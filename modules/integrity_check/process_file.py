from pathlib import Path
from .determine_action import determine_action
from .check_file import check_single_file

def process_file(db_path: Path, file_path: str, force_recheck: bool = False) -> tuple:
    """Process a file with coordinated database access."""
    action, stored_status, current_hash, current_mtime = determine_action(db_path, file_path, force_recheck)
    if action == 'USE_CACHED':
        return ('USE_CACHED', stored_status, "Cached result", file_path, None)
    elif action == 'UPDATE_MTIME':
        return ('UPDATE_MTIME', stored_status, "Cached result (hash matches)", file_path, current_mtime)
    elif action == 'RUN_FFMPEG':
        status, message, _, codec = check_single_file(file_path)
        update_info = (file_path, current_hash, current_mtime, status, codec)
        return ('RUN_FFMPEG', status, message, file_path, update_info)
    else:
        return ('ERROR', "Unknown action", file_path, None)