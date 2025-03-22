import subprocess
from typing import Tuple

def normalize_codec(codec: str) -> Tuple[str, str]:
    """Normalize codec names to a standard format and categorize them.
    Returns a tuple of (normalized_codec, codec_type) where codec_type is 'lossless' or 'lossy'
    """
    codec = codec.lower().strip()
    
    # Comprehensive codec mapping with categorization
    codec_map = {
        # MP3 variations
        'mpeg layer 3': ('mp3', 'lossy'),
        'mpeg-1 layer 3': ('mp3', 'lossy'),
        'mpeg-2 layer 3': ('mp3', 'lossy'),
        'mp3': ('mp3', 'lossy'),
        'mp3float': ('mp3', 'lossy'),
        
        # AAC variations
        'aac': ('aac', 'lossy'),
        'aac-lc': ('aac', 'lossy'),
        'aac-ld': ('aac', 'lossy'),
        'aac-he': ('aac', 'lossy'),
        'aac-hev2': ('aac', 'lossy'),
        'aac_latm': ('aac', 'lossy'),
        
        # Vorbis/OGG
        'vorbis': ('ogg', 'lossy'),
        'libvorbis': ('ogg', 'lossy'),
        'ogg': ('ogg', 'lossy'),
        
        # Opus
        'opus': ('opus', 'lossy'),
        'libopus': ('opus', 'lossy'),
        
        # FLAC
        'flac': ('flac', 'lossless'),
        'libflac': ('flac', 'lossless'),
        
        # ALAC
        'alac': ('alac', 'lossless'),
        'apl': ('alac', 'lossless'),
        
        # WavPack
        'wavpack': ('wv', 'lossless'),
        'wv': ('wv', 'lossless'),
        
        # WAV/PCM
        'wav': ('wav', 'lossless'),
        'pcm': ('pcm', 'lossless'),
        'pcm_s16le': ('pcm', 'lossless'),
        'pcm_s24le': ('pcm', 'lossless'),
        'pcm_s32le': ('pcm', 'lossless'),
        'pcm_f32le': ('pcm', 'lossless'),
        
        # Other formats
        'ape': ('ape', 'lossless'),
        'wma': ('wma', 'lossy'),
        'wmav1': ('wma', 'lossy'),
        'wmav2': ('wma', 'lossy'),
        'ac3': ('ac3', 'lossy'),
        'eac3': ('eac3', 'lossy'),
        'dts': ('dts', 'lossy'),
        'truehd': ('truehd', 'lossless')
    }
    
    # Return normalized codec and type, default to (original, 'unknown')
    return codec_map.get(codec, (codec, 'unknown'))

def get_codec(file_path: str) -> str:
    """Get the codec of an audio file using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a:0', 
             '-show_entries', 'stream=codec_name', 
             '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
            capture_output=True, text=True, timeout=10
        )
        codec = result.stdout.strip() if result.stdout else "unknown"
        normalized_codec, _ = normalize_codec(codec)
        return normalized_codec
    except Exception:
        return "unknown"

def check_single_file(file_path: str) -> tuple:
    """Check the integrity of a single audio file using FFmpeg with timeout."""
    try:
        # First check integrity
        result = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', file_path, '-f', 'null', '-'],
            capture_output=True, text=True, timeout=30
        )
        
        # Get codec information
        codec = get_codec(file_path)
        
        status = "PASSED" if not result.stderr else "FAILED"
        message = "" if not result.stderr else result.stderr.strip()
        return status, message, file_path, codec
    except subprocess.TimeoutExpired:
        return "FAILED", "FFmpeg timed out", file_path, "unknown"
    except Exception as e:
        return "FAILED", str(e), file_path, "unknown"