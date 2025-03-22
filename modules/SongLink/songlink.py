import argparse
import utils  # Import from root directory
from .songlink_command import songlink_command
from ..logo_utils import print_songlink_logo

def register_command(subparsers):
    """Register the songlink command."""
    songlink_parser = subparsers.add_parser("songlink", help="Fetch song links from Odesli API")
    group = songlink_parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--url', type=str, help="Single song URL")
    group.add_argument('--file', type=utils.path_type, help="Text file containing URLs")

    songlink_parser.add_argument('--country', type=str, help="User country code")
    songlink_parser.add_argument('--songIfSingle', action='store_true', help="Treat singles as songs")
    songlink_parser.add_argument('--select', '-s', nargs='+', help="Services to save (e.g., tidal)")
    songlink_parser.add_argument('--output', '-o', type=str, help="Output file to save links")
    songlink_parser.set_defaults(func=songlink_command)

def songlink_command(args):
    """Handle the songlink command."""
    if not args.url and not args.file:
        print_songlink_logo()
        print("\nAvailable options for 'songlink' command:")
        print("-" * 50)
        print("Usage: audio_tool.py songlink [options]")
        print("\nRequired options (one of):")
        print("  --url URL           Single song URL to fetch links for")
        print("  --file FILE         Text file containing URLs (one per line)")
        print("\nOptional options:")
        print("  --country CODE      User country code")
        print("  --songIfSingle      Treat singles as songs")
        print("  --select, -s SVC    Services to save (e.g., tidal)")
        print("  --output, -o FILE   Output file to save links")
        print("\nExample usage:")
        print("  audio_tool.py songlink --url https://open.spotify.com/track/...")
        print("  audio_tool.py songlink --file urls.txt --select spotify tidal")
        print("  audio_tool.py songlink --url https://open.spotify.com/track/... --output links.txt")
        return

    # Process song links
    if args.url:
        links = fetch_links(args.url, args.country, args.songIfSingle)
        if links:
            print_links(args.url, links, args.select)
    elif args.file:
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        for url in urls:
            links = fetch_links(url, args.country, args.songIfSingle)
            if links:
                print_links(url, links, args.select)