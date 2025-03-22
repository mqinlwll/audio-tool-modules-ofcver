"""Module containing ASCII art logos for each command."""
from colorama import Fore, Style

def print_integrity_check_logo():
    logo = f"""{Fore.CYAN}
    ╔══════════════════════════════════════════╗
    ║          INTEGRITY CHECKER               ║
    ║     Verify audio file integrity and      ║
    ║     generate MD5 hashes for tracking     ║
    ╚══════════════════════════════════════════╝{Style.RESET_ALL}"""
    print(logo)

def print_audio_analysis_logo():
    logo = f"""{Fore.GREEN}
    ╔══════════════════════════════════════════╗
    ║           AUDIO ANALYZER                 ║
    ║     Analyze audio files for codec,       ║
    ║     bitrate, sample rate, and quality    ║
    ╚══════════════════════════════════════════╝{Style.RESET_ALL}"""
    print(logo)

def print_cover_art_logo():
    logo = f"""{Fore.MAGENTA}
    ╔══════════════════════════════════════════╗
    ║               COVER ART                  ║
    ║     Manage album artwork visibility      ║
    ║     and organization in music folders    ║
    ╚══════════════════════════════════════════╝{Style.RESET_ALL}"""
    print(logo)

def print_album_counter_logo():
    logo = f"""{Fore.YELLOW}
    ╔══════════════════════════════════════════╗
    ║           ALBUM COUNTER                  ║
    ║     Count albums, songs, and calculate   ║
    ║     total size of music collections      ║
    ╚══════════════════════════════════════════╝{Style.RESET_ALL}"""
    print(logo)

def print_database_check_logo():
    logo = f"""{Fore.BLUE}
    ╔══════════════════════════════════════════╗
    ║            DATABASE CHECK                ║
    ║     Monitor and manage database health,  ║
    ║     export data, and update schemas      ║
    ╚══════════════════════════════════════════╝{Style.RESET_ALL}"""
    print(logo)

def print_songlink_logo():
    logo = f"""{Fore.RED}
    ╔══════════════════════════════════════════╗
    ║           SONG LINKER                    ║
    ║     Fetch streaming links for songs      ║
    ║     across multiple music platforms      ║
    ╚══════════════════════════════════════════╝{Style.RESET_ALL}"""
    print(logo) 