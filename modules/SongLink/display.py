from colorama import Fore, Style
from .normalize import normalize_service_name

def print_links(url, links, selected_services=None):
    """Print the fetched links to the console with formatting."""
    print(Style.BRIGHT + f"\nResults for URL: {url}")
    print(Style.BRIGHT + "Available Links:")
    print("-" * 40)

    filtered_links = links
    if selected_services:
        filtered_links = {k: v for k, v in links.items() if k in selected_services}

    for service, info in filtered_links.items():
        normalized_service = normalize_service_name(service)
        print(f"{normalized_service}: {info['url']}")

    print("-" * 40)
    return filtered_links