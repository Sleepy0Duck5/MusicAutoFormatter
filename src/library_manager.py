import os
import re
from pathlib import Path
from collections import Counter
from loguru import logger

class LibraryManager:
    """
    Manages the final structure of the processed music library.
    Handles directory renaming and cleanup based on metadata.
    """
    # Patterns for folders that should be preserved (e.g., multidisc sets)
    # We rename their parents instead of themselves.
    GENERIC_FOLDER_RE = re.compile(r'^(disc|cd|vol|track|volume|part|d)\s?\d+$', re.I)

    def __init__(self, output_dir: Path, metadata_manager):
        self.output_dir = output_dir
        self.metadata_manager = metadata_manager

    def finalize_structure(self):
        """
        Walks the output directory and renames folders to match album titles.
        Respects existing Disc/CD hierarchies.
        """
        logger.info("Finalizing library structure...")
        
        # Bottom-up walk is critical to avoid invalidating parent paths during rename
        for root, dirs, files in os.walk(self.output_dir, topdown=False):
            root_path = Path(root)
            
            # We only care about folders that contain music
            mp3_files = [f for f in files if f.lower().endswith(".mp3")]
            if not mp3_files:
                continue

            # Identify the most frequent album name in this specific folder
            albums = []
            for f in mp3_files:
                try:
                    album = self.metadata_manager.get_album_name(root_path / f)
                    if album and album != "Unknown Album":
                        albums.append(album)
                except Exception:
                    continue
            
            if not albums:
                continue
            
            dominant_album = Counter(albums).most_common(1)[0][0]
            
            # Strategy: Rename the current folder UNLESS it's a generic "Disc X" folder.
            # If it's generic, we try to rename the folder ABOVE IT.
            target_to_rename = root_path
            if self.GENERIC_FOLDER_RE.match(root_path.name):
                target_to_rename = root_path.parent
                
            # Safety checks
            if not target_to_rename.exists():
                continue
            
            new_path = target_to_rename.parent / dominant_album
            if target_to_rename == new_path:
                continue

            # Prevent overwriting existing folders
            if new_path.exists():
                # logger.debug(f"Folder '{dominant_album}' already exists. Skipping rename for '{target_to_rename.name}'.")
                continue
            
            try:
                logger.info(f"Renaming folder: {target_to_rename.name} -> {dominant_album}")
                target_to_rename.rename(new_path)
            except Exception:
                # Silently skip if files are locked or permissions are lacking
                pass
