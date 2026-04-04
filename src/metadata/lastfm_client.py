import httpx
from loguru import logger
from typing import Optional
from src.core.constants import LASTFM_API_ENDPOINT

class LastFmClient:
    """
    Client for interacting with the Last.fm API to retrieve album art.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = LASTFM_API_ENDPOINT

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
                    logger.debug(f"No artwork found on Last.fm for '{artist} - {album}'")
                    return None, "image/jpeg"

                images = data["album"]["image"]
                # Preference: mega > extralarge > large
                # Sizes are typically [small, medium, large, extralarge, mega]
                image_url = None
                for size in ["mega", "extralarge", "large"]:
                    for img in images:
                        if img.get("size") == size and img.get("#text"):
                            image_url = img["#text"]
                            break
                    if image_url:
                        break

                if not image_url:
                    logger.debug(f"Found album on Last.fm but no high-quality image URL for '{artist} - {album}'")
                    return None, "image/jpeg"

                # Download the image
                logger.info(f"Downloading album art from Last.fm: {image_url}")
                img_response = client.get(image_url)
                img_response.raise_for_status()
                
                content_type = img_response.headers.get("Content-Type", "image/jpeg")
                return img_response.content, content_type

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Album '{artist} - {album}' not found on Last.fm")
            else:
                logger.error(f"Last.fm API error: {e}")
        except Exception as e:
            logger.error(f"Error fetching album art from Last.fm: {e}")

        return None, "image/jpeg"
