import argparse
import utils  # Import from root directory
from .songlink_command import songlink_command

def register_command(subparsers):
    """Register the songlink command."""
    songlink_parser = subparsers.add_parser("songlink", help="Fetch song links from Odesli API")
    
    # Create mutually exclusive group for primary options
    primary_group = songlink_parser.add_mutually_exclusive_group(required=False)
    primary_group.add_argument("--fetch", action="store_true", help="Fetch song links")
    primary_group.add_argument("--export", action="store_true", help="Export saved links")
    primary_group.add_argument("--list", action="store_true", help="List saved links")
    
    # Secondary options that can be combined with primary options
    songlink_parser.add_argument('--url', type=str, help="Single song URL")
    songlink_parser.add_argument('--file', type=utils.path_type, help="Text file containing URLs")
    songlink_parser.add_argument('--country', type=str, help="User country code")
    songlink_parser.add_argument('--songIfSingle', action='store_true', help="Treat singles as songs")
    songlink_parser.add_argument('--select', '-s', nargs='+', help="Services to save (e.g., tidal)")
    songlink_parser.add_argument('--output', '-o', type=str, help="Output file to save links")
    songlink_parser.add_argument('--format', choices=["txt", "csv", "json"], help="Export format (txt/csv/json)")
    songlink_parser.add_argument('--verbose', action='store_true', help="Show detailed information")
    
    songlink_parser.set_defaults(func=songlink_command) 