import os
from pathlib import Path
import concurrent.futures
from tqdm import tqdm
import utils
from .metadata import extract_metadata
from .metadata_db import save_metadata_to_db, get_unique_albums_from_db

def find_unique_albums(audio_files: list, save_to_db: bool = False, db_path: Path = None) -> tuple:
    """Find unique albums in the given list of audio files."""
    metadata_list = []
    unique_albums = set()

    # Process files in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(extract_metadata, file) for file in audio_files]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing files"):
            metadata = future.result()
            if "error" not in metadata:
                metadata_list.append(metadata)
                album_key = (
                    metadata.get('album', 'Unknown'),
                    metadata.get('artist', 'Unknown'),
                    metadata.get('album_artist', 'Unknown')
                )
                unique_albums.add(album_key)

    # Save metadata to database if requested
    if save_to_db and db_path:
        save_metadata_to_db(metadata_list, db_path)

    # Convert unique_albums set to list of dictionaries
    unique_albums_list = [
        {
            'album': album[0],
            'artist': album[1],
            'album_artist': album[2]
        }
        for album in unique_albums
    ]

    return unique_albums_list, metadata_list

def count_albums(directories: list, num_workers: int = None, save_to_db: bool = False):
    """Count unique albums in the given directories."""
    # Get configuration for database path
    if save_to_db:
        config = utils.load_config()
        cache_folder = Path(config.get("cache_folder", "cache log"))
        db_path = cache_folder / "album_metadata.db"
    else:
        db_path = None

    # Find all audio files
    all_files = []
    for directory in directories:
        all_files.extend(utils.get_audio_files(directory))

    if not all_files:
        print("No audio files found.")
        return

    print(f"\nFound {len(all_files)} audio files")

    # Find unique albums
    unique_albums, all_metadata = find_unique_albums(all_files, save_to_db, db_path)

    print(f"Found {len(unique_albums)} unique albums\n")
    print("Unique Albums:\n")
    for album in sorted(unique_albums, key=lambda x: (x['album'], x['artist'])):
        print(f"Album: {album['album']}")
        print(f"Artist: {album['artist']}")
        if album.get('album_artist') and album['album_artist'] != album['artist']:
            print(f"Album Artist: {album['album_artist']}")
        print()

def count_songs(directories: list, num_workers: int = None):
    """Count total songs in the given directories."""
    total_songs = 0
    for directory in directories:
        audio_files = utils.get_audio_files(directory)
        total_songs += len(audio_files)
    print(f"Found {total_songs} audio files")

def calculate_size(directories: list, num_workers: int = None):
    """Calculate total size of audio files in the given directories."""
    total_size = 0
    for directory in directories:
        audio_files = utils.get_audio_files(directory)
        for file in audio_files:
            total_size += os.path.getsize(file)
    
    # Convert to appropriate unit
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(total_size)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    print(f"Total size: {size:.2f} {units[unit_index]}")
