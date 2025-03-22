from pathlib import Path
import fcntl

LOCK_FILE = Path("database.lock")

def acquire_lock(lock_file: Path):
    """Acquire an exclusive lock on a file for process coordination."""
    lock_fd = open(lock_file, 'w')
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    return lock_fd

def release_lock(lock_fd):
    """Release the lock and close the file descriptor."""
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    lock_fd.close()