from colorama import Fore
from .fetch import fetch_links
from .display import print_links
from ..logo_utils import print_songlink_logo

def songlink_command(args):
    """Handle the songlink command."""
    if not args.url and not args.file:
        print_songlink_logo()
        print("\nAvailable options for 'songlink' command:")
        print("-" * 50)
        print("Usage: audio_tool.py songlink [primary_option] [secondary_options]")
        print("\nPrimary options (mutually exclusive):")
        print("  --fetch              Fetch song links")
        print("    Required options (one of):")
        print("        --url URL      Single song URL to fetch links for")
        print("        --file FILE    Text file containing URLs (one per line)")
        print("    Secondary options:")
        print("        --country CODE User country code")
        print("        --songIfSingle Treat singles as songs")
        print("        --select, -s SVC Services to save (e.g., tidal)")
        print("        --output, -o FILE Output file to save links")
        print("        --format FORMAT Export format (txt/csv/json)")
        print("        --verbose      Show detailed information")
        print("\n  --export            Export saved links")
        print("    Secondary options:")
        print("        --output, -o FILE Output file to save links")
        print("        --format FORMAT Export format (txt/csv/json)")
        print("\n  --list              List saved links")
        print("    Secondary options:")
        print("        --output, -o FILE Output file to save links")
        print("        --format FORMAT Export format (txt/csv/json)")
        print("\nExample usage:")
        print("  audio_tool.py songlink --fetch --url https://open.spotify.com/track/...")
        print("  audio_tool.py songlink --fetch --file urls.txt --select spotify tidal")
        print("  audio_tool.py songlink --fetch --url https://open.spotify.com/track/... --output links.txt")
        print("  audio_tool.py songlink --export --format csv")
        print("  audio_tool.py songlink --list --format json")
        return

    selected_services = {s.strip().lower().replace(' ', '_') for s in args.select} if args.select else None
    output_file = open(args.output, 'w') if args.output else None

    try:
        urls = []
        if args.file:
            with open(args.file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        else:
            urls = [args.url]

        for url in urls:
            links = fetch_links(url, args.country, args.songIfSingle)
            if not links:
                print(f"{Fore.YELLOW}No links found for {url}")
                continue

            filtered_links = print_links(url, links, selected_services)

            if output_file and filtered_links:
                for info in filtered_links.values():
                    output_file.write(f"{info['url']}\n")

    finally:
        if output_file:
            output_file.close()