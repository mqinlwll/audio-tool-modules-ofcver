# Audio Tool Suite

A comprehensive suite of tools for audio file analysis, management, and processing.

## Table of Contents
1. [For Non-Coders](#for-non-coders)
   - [Overview](#overview)
   - [Features](#features)
   - [Installation](#installation)
   - [Usage Guide](#usage-guide)
2. [For Developers](#for-developers)
   - [Architecture](#architecture)
   - [Module Workflows](#module-workflows)
   - [Development Setup](#development-setup)
   - [Contributing](#contributing)

## For Non-Coders

### Overview
This tool suite helps you analyze and manage your audio files. It can:
- Analyze audio file quality and metadata
- Check audio file integrity
- Manage album artwork
- Track song links
- Count and organize albums
- Export analysis results

### Features
- **Audio Analysis**: Get detailed information about your audio files
- **Integrity Checking**: Ensure your audio files are not corrupted
- **Cover Art Management**: Handle album artwork
- **Song Link Tracking**: Keep track of song links across platforms
- **Album Organization**: Count and organize your music collection
- **Export Options**: Save analysis results in CSV or JSON format

### Installation

1. Install system dependencies:
```bash
# For Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg ffprobe

# For macOS (using Homebrew)
brew install ffmpeg
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Usage Guide

#### Basic Audio Analysis
```bash
python3.12 audio_tool.py info --analyze "/path/to/your/music"
```

#### Export Analysis Results
```bash
# Export to CSV
python3.12 audio_tool.py info --export --output results.csv

# Export to JSON
python3.12 audio_tool.py info --export --output results.json
```

#### Advanced Options
- `--verbose`: Show detailed analysis information
- `--workers N`: Use multiple processors for faster analysis
- `--no-db`: Skip saving results to database

## For Developers

### Architecture

```
audio_tool/
├── modules/
│   ├── audio_analysis/     # Audio file analysis
│   ├── integrity_check/    # File integrity verification
│   ├── cover_art/         # Album artwork management
│   ├── SongLink/          # Song link tracking
│   ├── album_counter/     # Album organization
│   └── database_utils.py  # Database operations
├── cache log/             # Cache and database storage
└── audio_tool.py          # Main entry point
```

### Module Workflows

#### 1. Audio Analysis Module
```
Input Audio File
     │
     ▼
┌─────────────┐
│ Check Cache │
└─────┬───────┘
      │
      ▼
   Cache Hit? ──Yes──> Return Cached Data
      │
      No
      │
      ▼
Extract Metadata
      │
      ▼
Analyze Technical Details
      │
      ▼
Save to Database
      │
      ▼
Return Results
```

**Caching Strategy:**
- Uses SQLite database with WAL mode
- Tracks file modifications and hashes
- Prevents re-processing of unchanged files
- Updates cache every 24 hours

#### 2. Integrity Check Module
```
Input File
    │
    ▼
Check Database
    │
    ▼
Verified? ──Yes──> Return Status
    │
    No
    │
    ▼
Calculate Hash
    │
    ▼
Verify File
    │
    ▼
Update Database
    │
    ▼
Return Results
```

#### 3. Cover Art Module
```
Input Album
    │
    ▼
Check Cache
    │
    ▼
Exists? ──Yes──> Return Cached Art
    │
    No
    │
    ▼
Search Sources
    │
    ▼
Download Art
    │
    ▼
Save to Cache
    │
    ▼
Return Art
```

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd audio-tool
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
```

4. Set up pre-commit hooks:
```bash
pre-commit install
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests:
```bash
python -m pytest
```
5. Submit a pull request

## Database Schema

### File Tracking
```sql
CREATE TABLE file_tracking (
    file_path TEXT PRIMARY KEY,
    last_modified TEXT,
    file_hash TEXT,
    last_processed TEXT
);
```

### Audio Analysis
```sql
CREATE TABLE audio_analysis (
    file_path TEXT PRIMARY KEY,
    title TEXT,
    album TEXT,
    artist TEXT,
    album_artist TEXT,
    isrc TEXT,
    upc TEXT,
    codec TEXT,
    sample_rate INTEGER,
    bit_depth INTEGER,
    bit_rate INTEGER,
    channels INTEGER,
    first_analyzed TEXT,
    last_updated TEXT
);
```

## Performance Optimization

1. **Parallel Processing**
   - Uses ProcessPoolExecutor for parallel analysis
   - Configurable number of workers
   - Default: Number of CPU cores or 4

2. **Caching Strategy**
   - File-based caching with SQLite
   - WAL mode for concurrent access
   - Hash-based change detection
   - 24-hour cache expiration

3. **Database Optimization**
   - WAL mode for better concurrency
   - Normal synchronous mode
   - Memory-based temp store
   - Busy timeout handling

## Error Handling

1. **File Processing**
   - Graceful handling of missing files
   - Corrupt file detection
   - Permission error handling

2. **Database Operations**
   - Connection retry mechanism
   - Transaction rollback on failure
   - Deadlock prevention

3. **External Dependencies**
   - FFmpeg/FFprobe availability check
   - Network request timeout handling
   - Resource cleanup
