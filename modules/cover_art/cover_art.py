import os
from pathlib import Path
import concurrent.futures
from tqdm import tqdm
import utils  # Import from root directory
from ..logo_utils import print_cover_art_logo

# Base cover art filenames
BASE_COVER_NAMES = ['cover.jpg', 'cover.jpeg', 'cover.png', 'folder.jpg', 'folder.png']

def rename_file(src: str, dst: str):
    """Rename a file from src to dst."""
    os.rename(src, dst)

def get_files_to_rename(path: str, hide: bool) -> list:
    """Identify cover art files to rename based on hide/show action."""
    files_to_rename = []
    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if hide:
                if file in BASE_COVER_NAMES:
                    new_name = os.path.join(root, "." + file)
                    if not os.path.exists(new_name):
                        files_to_rename.append((file_path, new_name))
            else:
                if file.startswith(".") and file[1:] in BASE_COVER_NAMES:
                    new_name = os.path.join(root, file[1:])
                    if not os.path.exists(new_name):
                        files_to_rename.append((file_path, new_name))
    return files_to_rename

def process_cover_art(args):
    """Process cover art files in the specified directory."""
    if not args.path or not any([args.hide, args.show, args.scan]):
        print_cover_art_logo()
        print("\nAvailable options for 'cover-art' command:")
        print("-" * 50)
        print("Usage: audio_tool.py cover-art [primary_option] [secondary_options] <directory>")
        print("\nPrimary options (mutually exclusive):")
        print("  --hide               Hide cover art by adding a dot prefix")
        print("    Secondary options:")
        print("        --verbose      Show detailed information")
        print("        --workers N    Number of worker processes for parallel processing")
        print("        --dry-run      Show what would be done without making changes")
        print("\n  --show              Show cover art by removing dot prefix")
        print("    Secondary options:")
        print("        --verbose      Show detailed information")
        print("        --workers N    Number of worker processes for parallel processing")
        print("        --dry-run      Show what would be done without making changes")
        print("\n  --scan              Scan for cover art files without modifying")
        print("    Secondary options:")
        print("        --verbose      Show detailed information")
        print("        --workers N    Number of worker processes for parallel processing")
        print("        --dry-run      Show what would be done without making changes")
        print("\nExample usage:")
        print("  audio_tool.py cover-art --hide /path/to/music")
        print("  audio_tool.py cover-art --show --verbose /path/to/music")
        print("  audio_tool.py cover-art --scan --dry-run /path/to/music")
        return

    # Process cover art files
    if args.hide:
        hide_cover_art(args.path)
    elif args.show:
        show_cover_art(args.path)
    elif args.scan:
        scan_cover_art(args.path)

def hide_cover_art(path: str):
    """Hide cover art files by adding a dot prefix."""
    files_to_rename = get_files_to_rename(path, True)
    if not files_to_rename:
        print("No cover art files found to hide.")
        return
        
    print(f"\nHiding {len(files_to_rename)} cover art files...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(rename_file, src, dst) for src, dst in files_to_rename]
        for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            pass
    print("Cover art files hidden successfully.")

def show_cover_art(path: str):
    """Show hidden cover art files by removing the dot prefix."""
    files_to_rename = get_files_to_rename(path, False)
    if not files_to_rename:
        print("No hidden cover art files found to show.")
        return
        
    print(f"\nShowing {len(files_to_rename)} hidden cover art files...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(rename_file, src, dst) for src, dst in files_to_rename]
        for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            pass
    print("Cover art files shown successfully.")

def scan_cover_art(path: str):
    """Scan for cover art files without modifying."""
    files_to_rename = get_files_to_rename(path, False)
    if not files_to_rename:
        print("No cover art files found to scan.")
        return
        
    print(f"\nScanning {len(files_to_rename)} cover art files...")
    for src, _ in files_to_rename:
        print(f"Found cover art file: {src}")
    print("Scan completed.")

def register_command(subparsers):
    """Register the cover art command."""
    cover_parser = subparsers.add_parser("cover-art", help="Hide or show cover art files")
    
    # Create mutually exclusive group for primary options
    primary_group = cover_parser.add_mutually_exclusive_group(required=False)
    primary_group.add_argument("--hide", action="store_true", help="Hide cover art by adding a dot prefix")
    primary_group.add_argument("--show", action="store_true", help="Show cover art by removing dot prefix")
    primary_group.add_argument("--scan", action="store_true", help="Scan for cover art files without modifying")
    
    # Secondary options that can be combined with primary options
    cover_parser.add_argument("path", nargs='?', type=utils.directory_path, help="Directory to process")
    cover_parser.add_argument("--verbose", action="store_true", help="Show detailed information")
    cover_parser.add_argument("--workers", type=int, help="Number of worker processes for parallel processing")
    cover_parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    cover_parser.set_defaults(func=process_cover_art)

def cover_art(args):
    """Handle the cover art command."""
    if not args.path:
        print_cover_art_logo()
        print("\nAvailable options for 'cover-art' command:")
        print("-" * 50)
        print("Usage: audio_tool.py cover-art [options] <directory>")
        print("\nOptions:")
        print("  --hide      Hide cover art by adding a dot prefix")
        print("  --show      Show cover art by removing dot prefix")
        print("  --scan      Scan for cover art files without modifying")
        print("\nExample usage:")
        print("  audio_tool.py cover-art --hide /path/to/music")
        print("  audio_tool.py cover-art --show /path/to/music")
        print("  audio_tool.py cover-art --scan /path/to/music")
        return
    # ... rest of the function ...
