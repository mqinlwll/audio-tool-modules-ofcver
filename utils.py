import os
import shutil
import yaml
from pathlib import Path
import argparse

# Supported audio file extensions
AUDIO_EXTENSIONS = ['.flac', '.wav', '.m4a', '.mp3', '.ogg', '.opus', '.ape', '.wv', '.wma']

# Configuration file path
CONFIG_FILE = Path("audio-script-config.yaml")

def load_config():
    """Load configuration from YAML file or create a default one if it doesn't exist."""
    default_config = {
        "cache_folder": "cache log",
        "database": {
            "path": "cache log",
            "auto_create": True
        },
        "export": {
            "folder": "exports",
            "formats": ["csv", "json"],
            "auto_create": True
        },
        "analysis": {
            "workers": 4,
            "verbose": False
        }
    }

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
            # Ensure default keys exist
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
    else:
        config = default_config
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Ensure cache directory exists
    cache_dir = Path(config["cache_folder"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure export directory exists if auto_create is enabled
    if config["export"].get("auto_create", True):
        export_dir = Path(config["export"]["folder"])
        export_dir.mkdir(parents=True, exist_ok=True)
    
    return config

def get_audio_files(directory: str) -> list:
    """Recursively find audio files in a directory."""
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in AUDIO_EXTENSIONS:
                audio_files.append(os.path.join(root, file))
    return audio_files

def is_ffmpeg_installed() -> bool:
    """Check if FFmpeg is installed and available in PATH."""
    return shutil.which('ffmpeg') is not None

def is_ffprobe_installed() -> bool:
    """Check if ffprobe is installed and available in PATH."""
    return shutil.which('ffprobe') is not None

def directory_path(path: str) -> str:
    """Custom argparse type to validate directory paths."""
    if os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(f"'{path}' is not a directory")

def path_type(path: str) -> str:
    """Custom argparse type to validate existing paths (file or directory)."""
    if os.path.exists(path):
        return path
    raise argparse.ArgumentTypeError(f"'{path}' does not exist")
