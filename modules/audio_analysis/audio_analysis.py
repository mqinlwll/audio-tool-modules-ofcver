import subprocess
import json
from pathlib import Path
import concurrent.futures
from tqdm import tqdm
import datetime
import os
import csv
import utils  # Import from root directory
from .schema import init_audio_analysis_db, save_analysis_to_db, get_analysis_from_db
from modules.album_counter.metadata import extract_metadata
from ..logo_utils import print_audio_analysis_logo

def analyze_single_file(file_path: str) -> dict:
    """Analyze metadata of a single audio file using ffprobe."""
    try:
        # Get metadata first
        metadata = extract_metadata(file_path)
        if "error" in metadata:
            return {"error": f"Failed to extract metadata: {metadata['error']}", "file_path": file_path}

        # Get audio analysis data
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]
        result = subprocess.check_output(cmd, universal_newlines=True)
        data = json.loads(result)
        stream = data["streams"][0]

        # Extract technical details
        codec = stream.get("codec_name", "N/A")
        sample_rate = int(stream.get("sample_rate", 0)) if stream.get("sample_rate") else 0
        channels = int(stream.get("channels", 0)) if stream.get("channels") else 0
        bit_depth = int(stream.get("bits_per_raw_sample", 0)) if stream.get("bits_per_raw_sample") else 0
        bit_rate = int(data["format"].get("bit_rate", 0)) if data["format"].get("bit_rate") else 0

        # Combine metadata and technical details
        analysis_data = {
            "title": metadata.get("title", "Unknown"),
            "album": metadata.get("album", "Unknown"),
            "artist": metadata.get("artist", "Unknown"),
            "album_artist": metadata.get("album_artist", "Unknown"),
            "isrc": metadata.get("isrc", "Unknown"),
            "upc": metadata.get("upc", "Unknown"),
            "codec": codec,
            "sample_rate": sample_rate,
            "bit_depth": bit_depth,
            "bit_rate": bit_rate,
            "channels": channels,
            "file_path": file_path  # Keep file path for display but don't store in DB
        }

        # Format display text
        channel_info = "Mono" if channels == 1 else "Stereo" if channels == 2 else f"{channels} channels" if channels else "N/A"
        analysis_text = f"Analyzing: {file_path}\n"
        analysis_text += f"  Title: {analysis_data['title']}\n"
        analysis_text += f"  Album: {analysis_data['album']}\n"
        analysis_text += f"  Artist: {analysis_data['artist']}\n"
        analysis_text += f"  Album Artist: {analysis_data['album_artist']}\n"
        analysis_text += f"  ISRC: {analysis_data['isrc']}\n" if analysis_data['isrc'] != "Unknown" else ""
        analysis_text += f"  UPC: {analysis_data['upc']}\n" if analysis_data['upc'] != "Unknown" else ""
        analysis_text += f"  Bitrate: {bit_rate} bps\n" if bit_rate else "  Bitrate: N/A\n"
        analysis_text += f"  Sample Rate: {sample_rate} Hz\n" if sample_rate else "  Sample Rate: N/A\n"
        analysis_text += f"  Bit Depth: {bit_depth} bits\n" if bit_depth else "  Bit Depth: N/A\n"
        analysis_text += f"  Channels: {channel_info}\n"
        analysis_text += f"  Codec: {codec}\n"

        # Add warnings and info
        if Path(file_path).suffix.lower() == ".m4a":
            if "aac" in codec.lower():
                analysis_text += "  [INFO] AAC (lossy) codec detected.\n"
            elif "alac" in codec.lower():
                analysis_text += "  [INFO] ALAC (lossless) codec detected.\n"
            else:
                analysis_text += f"  [WARNING] Unknown codec: {codec}\n"
        elif Path(file_path).suffix.lower() in [".opus", ".mp3"]:
            analysis_text += f"  [INFO] Lossy codec: {codec}\n"
        if bit_depth and bit_depth < 16:
            analysis_text += "  [WARNING] Low bit depth may indicate lossy encoding.\n"
        if sample_rate and sample_rate < 44100:
            analysis_text += "  [WARNING] Low sample rate may indicate lossy encoding.\n"
        analysis_text += "\n"

        analysis_data["display_text"] = analysis_text
        return analysis_data

    except Exception as e:
        return {"error": str(e), "file_path": file_path, "display_text": f"Analyzing: {file_path}\n  [ERROR] Failed to analyze: {e}\n\n"}

def export_to_csv(data: list, output_file: Path):
    """Export analysis data to CSV file."""
    if not data:
        print("No data to export.")
        return

    fieldnames = ['title', 'album', 'artist', 'album_artist', 'isrc', 'upc', 'codec', 
                 'sample_rate', 'bit_depth', 'bit_rate', 'channels', 'first_analyzed', 'last_updated']
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Data exported to CSV: {output_file}")

def export_to_json(data: list, output_file: Path):
    """Export analysis data to JSON file."""
    if not data:
        print("No data to export.")
        return

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Data exported to JSON: {output_file}")

def analyze_audio(args):
    """Handle the audio analysis command."""
    if not args.path:
        print_audio_analysis_logo()
        print("\nAvailable options for 'info' command:")
        print("-" * 50)
        print("Usage: audio_tool.py info [options] <file_or_directory>")
        print("\nOptions:")
        print("  -o, --output FILE  Export results to CSV or JSON file")
        print("  --verbose          Print results to console (no parallelism)")
        print("  --workers N        Number of worker processes for parallel analysis")
        print("  --no-db           Do not save analysis data to database")
        print("\nExample usage:")
        print("  audio_tool.py info /path/to/music")
        print("  audio_tool.py info /path/to/music --output results.csv")
        print("  audio_tool.py info /path/to/music --verbose")
        return

    if not utils.is_ffprobe_installed():
        print("Error: ffprobe is not installed or not in your PATH.")
        return

    path = args.path
    output = args.output
    verbose = args.verbose
    num_workers = args.workers if args.workers is not None else (os.cpu_count() or 4)
    save_to_db = not args.no_db  # Save to DB by default unless --no-db is specified

    # Get configuration for database path
    config = utils.load_config()
    cache_folder = Path(config.get("cache_folder", "cache log"))
    db_path = cache_folder / "audio_analysis.db"

    # Determine files to analyze
    if os.path.isfile(path) and os.path.splitext(path)[1].lower() in utils.AUDIO_EXTENSIONS:
        audio_files = [Path(path)]
    elif os.path.isdir(path):
        audio_files = [file for ext in utils.AUDIO_EXTENSIONS for file in Path(path).rglob(f"*{ext}")]
        if not audio_files:
            print(f"No audio files found in '{path}'.")
            return
    else:
        print(f"'{path}' is not a file or directory.")
        return

    # Initialize database if saving to DB
    if save_to_db:
        init_audio_analysis_db(db_path)

    if verbose:
        # Sequential analysis with console output
        for audio_file in audio_files:
            result = analyze_single_file(str(audio_file))
            print(result["display_text"])
            if "error" not in result and save_to_db:
                save_analysis_to_db(result, db_path)
    else:
        # Parallel analysis
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(analyze_single_file, str(file)) for file in audio_files]
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Analyzing audio"):
                result = future.result()
                if "error" not in result and save_to_db:
                    save_analysis_to_db(result, db_path)
    
    if save_to_db:
        print(f"Analysis data saved to database: {db_path}")

    # Export data if requested
    if output:
        output_path = Path(output)
        if output_path.suffix.lower() == '.csv':
            data = get_analysis_from_db(db_path) if save_to_db else []
            export_to_csv(data, output_path)
        elif output_path.suffix.lower() == '.json':
            data = get_analysis_from_db(db_path) if save_to_db else []
            export_to_json(data, output_path)
        else:
            print(f"Unsupported output format: {output_path.suffix}")

def register_command(subparsers):
    """Register the 'info' command with the subparsers."""
    info_parser = subparsers.add_parser("info", help="Analyze audio file metadata")
    
    # Create mutually exclusive group for primary options
    primary_group = info_parser.add_mutually_exclusive_group(required=False)
    primary_group.add_argument("--analyze", action="store_true", help="Analyze audio files")
    primary_group.add_argument("--export", action="store_true", help="Export analysis results")
    
    # Secondary options that can be combined with primary options
    info_parser.add_argument("path", nargs='?', type=utils.path_type, help="File or directory to analyze")
    info_parser.add_argument("-o", "--output", help="Export results to CSV or JSON file")
    info_parser.add_argument("--verbose", action="store_true", help="Print results to console (no parallelism)")
    info_parser.add_argument("--workers", type=int, help="Number of worker processes for parallel analysis")
    info_parser.add_argument("--no-db", action="store_true", help="Do not save analysis data to database")
    info_parser.add_argument("--format", choices=["csv", "json"], help="Export format (csv/json)")
    
    info_parser.set_defaults(func=analyze_audio)
