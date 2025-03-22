from colorama import Fore, Style

def normalize_service_names(links):
    """Normalize service names to lowercase with underscores."""
    return {service.lower().replace(" ", "_"): info for service, info in links.items()}

def normalize_service_name(service):
    """Apply color and formatting to service names."""
    service_colors = {
        "spotify": Fore.GREEN,
        "itunes": Fore.CYAN,
        "apple_music": Fore.RED,
        "youtube": Fore.YELLOW,
        "youtube_music": Fore.YELLOW + Style.BRIGHT,
        "google": Fore.BLUE,
        "google_store": Fore.BLUE,
        "pandora": Fore.MAGENTA,
        "deezer": Fore.BLUE,
        "tidal": Fore.MAGENTA,
        "amazon_store": Fore.YELLOW,
        "amazon_music": Fore.YELLOW,
        "soundcloud": Fore.CYAN,
        "napster": Fore.YELLOW,
        "yandex": Fore.LIGHTYELLOW_EX,
        "spinrilla": Fore.GREEN,
        "audius": Fore.LIGHTCYAN_EX,
        "anghami": Fore.LIGHTYELLOW_EX,
        "boomplay": Fore.GREEN,
        "audiomack": Fore.GREEN,
    }
    color = service_colors.get(service, Fore.WHITE)
    return color + service.replace("_", " ").title() + Style.RESET_ALL