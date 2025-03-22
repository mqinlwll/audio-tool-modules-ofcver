import subprocess
import sys

def get_codec(file_path: str) -> str:
    """Determine the codec of an audio file using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "csv=p=0", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        codec_name = result.stdout.strip()
        return codec_name if codec_name else "Unknown"
    except Exception as e:
        print(f"Error determining codec for {file_path}: {e}", file=sys.stderr)
        return "Unknown"
