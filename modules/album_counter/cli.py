import os
import utils
from .counters import count_albums, count_songs, calculate_size
from ..logo_utils import print_album_counter_logo

def count_command(args):
    """Handle the 'count' command to count albums, songs, or calculate sizes."""
    if not args.option:
        print_album_counter_logo()
        print("\nAvailable options for 'count' command:")
        print("-" * 50)
        print("album  - Count unique albums in the specified directories")
        print("song   - Count total number of audio files")
        print("size   - Calculate total size of audio files")
        print("\nExample usage:")
        print("  audio_tool.py count album /path/to/music")
        print("  audio_tool.py count song /path/to/music")
        print("  audio_tool.py count size /path/to/music")
        print("\nOptions:")
        print("  --no-db     Do not save album metadata to database (only for 'album' option)")
        print("  --workers N Number of worker processes for parallel processing")
        return

    if not utils.is_ffprobe_installed():
        print("Error: ffprobe is not installed or not in your PATH.")
        return

    directories = args.directories
    num_workers = args.workers if args.workers is not None else (os.cpu_count() or 4)
    save_to_db = not args.no_db  # Save to DB by default unless --no-db is specified

    if args.option == "album":
        count_albums(directories, num_workers, save_to_db)
    elif args.option == "song":
        count_songs(directories, num_workers)
    elif args.option == "size":
        calculate_size(directories, num_workers)
    else:
        print("Invalid option. Use 'album', 'song', or 'size'.")

def register_command(subparsers):
    """Register the 'count' command with the CLI subparsers."""
    count_parser = subparsers.add_parser("count", help="Count albums, songs, or calculate sizes based on metadata")
    count_parser.add_argument("option", nargs='?', choices=["album", "song", "size"], help="Choose what to count: albums, songs, or sizes")
    count_parser.add_argument("directories", nargs='*', type=utils.directory_path, help="One or more directories to process")
    count_parser.add_argument("--no-db", action="store_true", help="Do not save album metadata to database (only for 'album' option)")
    count_parser.add_argument("--workers", type=int, help="Number of worker processes for parallel processing")
    count_parser.set_defaults(func=count_command)
