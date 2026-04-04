import httpx
from loguru import logger
from typing import Optional
import re
from src.core.constants import LASTFM_API_ENDPOINT

class LastFmClient:
    """
    Client for interacting with the Last.fm API to retrieve album art.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = LASTFM_API_ENDPOINT
        self.cache = {} # Cache for (artist, album) -> (image_data, mime_type)

    def get_album_art(self, artist: str, album: str) -> (Optional[bytes], str):
        """
        Fetches album art for the given artist and album.
        Returns a tuple of (image_data, mime_type).
        """
        if not self.api_key:
            logger.warning("Last.fm API Key is not set. Skipping online art search.")
            return None, "image/jpeg"

        if not artist or not album:
            logger.debug(f"Missing artist ({artist}) or album ({album}) for Last.fm lookup.")
            return None, "image/jpeg"

        # 1. Check Cache
        cache_key = (artist.lower().strip(), album.lower().strip())
        if cache_key in self.cache:
            logger.debug(f"Using cached Last.fm result for '{artist} - {album}'")
            return self.cache[cache_key]

        # Search Strategy: Try multiple variations to increase match rate
        # 1. Original: "My Album_ Title"
        # 2. Underscore to Colon: "My Album: Title"
        # 3. Underscore to Space: "My Album  Title"
        # 4. Strip extra info after parenthesis/bracket: "(Original Soundtrack)" -> ""
        
        search_names = [album]
        
        if "_" in album:
            search_names.append(album.replace("_", ":"))
            search_names.append(album.replace("_", " "))
        
        # Add a version with everything in parentheses removed (e.g., "(Original Soundtrack)")
        # This often matches better on Last.fm for OST releases.
        stripped_album = re.sub(r'\s*\(.*?\)\s*', '', album).strip()
        if stripped_album != album:
            search_names.append(stripped_album)
            # Try stripped with colon replacement too
            if "_" in stripped_album:
                search_names.append(stripped_album.replace("_", ":"))

        # Deduplicate while preserving order
        unique_names = []
        for name in search_names:
            if name not in unique_names:
                unique_names.append(name)

        for attempt, current_album in enumerate(unique_names):
            logger.debug(f"Searching Last.fm (Attempt {attempt+1}): {artist} - {current_album}")
            data, mime = self._fetch_album_info(artist, current_album)
            if data:
                self.cache[cache_key] = (data, mime)
                return data, mime

        # 3. Global Search Fallback
        # If direct lookups failed, try searching for the album to find the official name/artist
        logger.debug(f"Direct lookups failed. Attempting global search for '{artist} - {album}'")
        official_artist, official_album = self._search_album(artist, album)
        if official_artist and official_album:
            # Avoid infinite loop if search returned the exact same thing we already tried
            if (official_artist.lower() != artist.lower() or official_album.lower() != album.strip().lower()):
                logger.debug(f"Found candidate match via search: {official_artist} - {official_album}")
                data, mime = self._fetch_album_info(official_artist, official_album)
                if data:
                    self.cache[cache_key] = (data, mime)
                    return data, mime
        
        # Cache failure to prevent redundant calls
        self.cache[cache_key] = (None, "image/jpeg")
        logger.debug(f"All online search attempts failed for '{artist} - {album}'")
        return None, "image/jpeg"

    def _search_album(self, artist: str, album: str) -> (Optional[str], Optional[str]):
        """
        Performs a global search for the album to find the official artist and album name.
        """
        params = {
            "method": "album.search",
            "api_key": self.api_key,
            "album": f"{artist} {album}",
            "limit": 5,
            "format": "json"
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", {}).get("albummatches", {}).get("album", [])
                if not results:
                    return None, None
                
                # Take the first result as the best match
                match = results[0]
                return match.get("artist"), match.get("name")
        except Exception as e:
            logger.debug(f"Last.fm search failed: {e}")
            return None, None

    def _fetch_album_info(self, artist: str, album: str) -> (Optional[bytes], str):
        params = {
            "method": "album.getInfo",
            "api_key": self.api_key,
            "artist": artist,
            "album": album,
            "format": "json"
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

                if "album" not in data or "image" not in data["album"]:
                    return None, "image/jpeg"

                images = data["album"]["image"]
                image_url = None
                # Preference: mega > extralarge > large
                for size in ["mega", "extralarge", "large"]:
                    for img in images:
                        if img.get("size") == size and img.get("#text"):
                            image_url = img["#text"]
                            break
                    if image_url:
                        break

                if not image_url or "default_album_medium.png" in image_url:
                    return None, "image/jpeg"

                # Attempt to get original resolution using Last.fm URL "trick"
                # Pattern: /i/u/{size}/ -> /i/u/_/
                # e.g., /i/u/300x300/abc.png -> /i/u/_/abc.png
                hi_res_url = re.sub(r'/i/u/[^/]+/', '/i/u/_/', image_url)
                download_url = image_url
                
                if hi_res_url != image_url:
                    try:
                        # Quickly check if hi-res version exists (200 OK)
                        logger.debug(f"Attempting high-resolution upgrade: {hi_res_url}")
                        head_response = client.head(hi_res_url, follow_redirects=True)
                        if head_response.status_code == 200:
                            download_url = hi_res_url
                    except Exception:
                        pass

                # Download the image
                logger.debug(f"Found match! Downloading: {download_url}")
                img_response = client.get(download_url)
                img_response.raise_for_status()
                
                content_type = img_response.headers.get("Content-Type", "image/jpeg")
                return img_response.content, content_type

        except Exception:
            pass

        return None, "image/jpeg"
