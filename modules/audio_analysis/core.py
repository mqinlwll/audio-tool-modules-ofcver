import subprocess
import json
from pathlib import Path
import sqlite3
import datetime
import utils  # Import from root directory

def analyze_single_file(file_path: str) -> tuple:
    """Analyze metadata of a single audio file using ffprobe."""
    try:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]
        result = subprocess.check_output(cmd, universal_newlines=True)
        data = json.loads(result)
        stream = data["streams"][0]

        codec = stream.get("codec_name", "N/A")
        sample_rate = stream.get("sample_rate", "N/A")
        channels = stream.get("channels", "N/A")
        bit_depth = stream.get("bits_per_raw_sample", "N/A")
        bit_rate = data["format"].get("bit_rate", "N/A")
        duration = data["format"].get("duration", "N/A")
        size = data["format"].get("size", "N/A")

        warnings = []
        if Path(file_path).suffix.lower() == ".m4a":
            if "aac" in codec.lower():
                warnings.append("AAC (lossy) codec detected.")
            elif "alac" in codec.lower():
                warnings.append("ALAC (lossless) codec detected.")
            else:
                warnings.append(f"Unknown codec: {codec}")
        elif Path(file_path).suffix.lower() in [".opus", ".mp3"]:
            warnings.append(f"Lossy codec: {codec}")
        if bit_depth != "N/A" and int(bit_depth) < 16:
            warnings.append("Low bit depth may indicate lossy encoding.")
        if sample_rate != "N/A" and int(sample_rate) < 44100:
            warnings.append("Low sample rate may indicate lossy encoding.")

        return {
            "file_path": file_path,
            "codec": codec,
            "sample_rate": sample_rate,
            "channels": channels,
            "bit_depth": bit_depth,
            "bit_rate": bit_rate,
            "duration": duration,
            "size": size,
            "warnings": warnings,
            "analyzed_at": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "file_path": file_path,
            "error": str(e),
            "analyzed_at": datetime.datetime.now().isoformat()
        }

def save_to_database(analysis_results: list, db_path: Path):
    """Save analysis results to SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audio_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        codec TEXT,
        sample_rate TEXT,
        channels TEXT,
        bit_depth TEXT,
        bit_rate TEXT,
        duration TEXT,
        size TEXT,
        warnings TEXT,
        error TEXT,
        analyzed_at TEXT
    )
    """)

    # Insert or update results
    for result in analysis_results:
        cursor.execute("""
        INSERT OR REPLACE INTO audio_analysis 
        (file_path, codec, sample_rate, channels, bit_depth, bit_rate, duration, size, warnings, error, analyzed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["file_path"],
            result.get("codec", "N/A"),
            result.get("sample_rate", "N/A"),
            result.get("channels", "N/A"),
            result.get("bit_depth", "N/A"),
            result.get("bit_rate", "N/A"),
            result.get("duration", "N/A"),
            result.get("size", "N/A"),
            json.dumps(result.get("warnings", [])),
            result.get("error", None),
            result["analyzed_at"]
        ))

    conn.commit()
    conn.close() 