from .cli import register_command
import os
import concurrent.futures
from tqdm import tqdm
import mutagen
import sqlite3
import datetime
from pathlib import Path

# This file can be minimal since the registration is handled in cli.py
# It's kept for consistency with structure where audio_tool.py expects a file named after the folder

def count_albums(directory: str, save_to_db: bool = True, num_workers: int = None) -> None:
    """Count unique albums in a directory."""
    audio_files = utils.get_audio_files(directory)
    if not audio_files:
        print(f"No audio files found in '{directory}'")
        return

    print(f"\nFound {len(audio_files)} audio files")
    print("Processing files:", end='', flush=True)

    # Use ProcessPoolExecutor for parallel processing
    num_workers = num_workers if num_workers is not None else (os.cpu_count() or 4)
    albums = {}
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(get_album_info, file) for file in audio_files]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing files"):
            try:
                album_info = future.result()
                if album_info:
                    album_key = (album_info['album'], album_info['artist'])
                    if album_key not in albums:
                        albums[album_key] = {
                            'album': album_info['album'],
                            'artist': album_info['artist'],
                            'tracks': set(),
                            'discs': set(),
                            'total_tracks': 0,
                            'total_discs': 0
                        }
                    albums[album_key]['tracks'].add(album_info.get('track', 0))
                    albums[album_key]['discs'].add(album_info.get('disc', 1))
            except Exception as e:
                print(f"\nError processing file: {e}")

    # Calculate totals and sort albums
    for album_info in albums.values():
        album_info['total_tracks'] = len(album_info['tracks'])
        album_info['total_discs'] = len(album_info['discs'])
        del album_info['tracks']
        del album_info['discs']
    
    sorted_albums = sorted(albums.values(), key=lambda x: (x['artist'], x['album']))

    # Print results
    print("\nUnique Albums:")
    print("-" * 80)
    for album in sorted_albums:
        print(f"\nAlbum: {album['album']}")
        print(f"Artist: {album['artist']}")
        print(f"Total Tracks: {album['total_tracks']}")
        print(f"Total Discs: {album['total_discs']}")
    print("-" * 80)

    # Save to database if requested
    if save_to_db and sorted_albums:
        save_album_metadata(sorted_albums)

def get_album_info(file_path: str) -> dict:
    """Get album information from an audio file."""
    try:
        audio = mutagen.File(file_path)
        if audio is None:
            return None

        # Extract metadata
        tags = audio.tags
        if not tags:
            return None

        # Get basic metadata
        album = str(tags.get('album', ['Unknown Album'])[0])
        artist = str(tags.get('artist', ['Unknown Artist'])[0])
        
        # Get track and disc information
        track = int(tags.get('tracknumber', ['0'])[0].split('/')[0])
        disc = int(tags.get('discnumber', ['1'])[0].split('/')[0])
        
        return {
            'album': album,
            'artist': artist,
            'track': track,
            'disc': disc
        }
    except Exception:
        return None

def save_album_metadata(albums: list) -> None:
    """Save album metadata to database."""
    try:
        config = utils.load_config()
        cache_folder = Path(config.get("cache_folder", "cache log"))
        db_path = cache_folder / "album_metadata.db"
        
        # Initialize database
        init_db_with_wal(db_path, ALBUM_METADATA_SCHEMA)
        
        # Save to database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for album in albums:
                cursor.execute("""
                    INSERT OR REPLACE INTO album_metadata 
                    (album, artist, total_tracks, total_discs, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    album['album'],
                    album['artist'],
                    album['total_tracks'],
                    album['total_discs'],
                    datetime.datetime.now().isoformat()
                ))
            conn.commit()
        print(f"\nAlbum metadata saved to database: {db_path}")
    except Exception as e:
        print(f"Error saving album metadata: {e}")
