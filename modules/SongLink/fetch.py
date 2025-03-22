import requests
import json
from colorama import Fore
from .normalize import normalize_service_names

def fetch_links(url, country=None, song_if_single=False):
    """Fetch song links from the Odesli API."""
    base_url = "https://api.song.link/v1-alpha.1/links"
    params = {'url': url}
    if country:
        params['userCountry'] = country
    if song_if_single:
        params['songIfSingle'] = 'true'

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if 'linksByPlatform' not in data:
            return None
        return normalize_service_names(data['linksByPlatform'])
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"{Fore.RED}Error fetching links for {url}: {str(e)}")
        return None