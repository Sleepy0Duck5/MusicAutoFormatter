from pathlib import Path
from typing import Optional
from loguru import logger
from .constants import COVER_SEARCH_NAMES, IMAGE_EXTENSIONS

class CoverArtFinder:
    """
    Finds external album cover art using exact and fuzzy matching.
    """
    def find(self, source_path: Path) -> (Optional[bytes], str):
        """
        Searches in source directory and its parent for cover art.
        """
        directories = [source_path.parent, source_path.parent.parent]
        
        # 1. Exact matches (High priority)
        for directory in directories:
            if not directory or directory == Path("."):
                continue
            
            for name in COVER_SEARCH_NAMES:
                for ext in IMAGE_EXTENSIONS:
                    cover_path = directory / f"{name}{ext}"
                    if cover_path.exists():
                        logger.debug(f"Found external cover art (exact): {cover_path.name}")
                        mime = "image/png" if ext == ".png" else "image/jpeg"
                        return cover_path.read_bytes(), mime

        # 2. Fuzzy matches (Low priority - keywords in filename)
        for directory in directories:
            if not directory or directory == Path("."):
                continue
            
            try:
                for item in directory.iterdir():
                    if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                        lower_name = item.stem.lower()
                        if any(kw in lower_name for kw in COVER_SEARCH_NAMES):
                            logger.debug(f"Found external cover art (fuzzy): {item.name}")
                            mime = "image/png" if item.suffix.lower() == ".png" else "image/jpeg"
                            return item.read_bytes(), mime
            except Exception:
                pass

        return None, "image/jpeg"
