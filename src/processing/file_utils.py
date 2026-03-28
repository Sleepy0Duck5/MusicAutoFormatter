import shutil
from pathlib import Path
from typing import Optional
from loguru import logger

class FileMirror:
    """
    Handles file mirroring and specific file renaming rules (e.g., .m3u to .m3u.bak).
    """
    def __init__(self, output_base: Path, backup_m3u: bool = False):
        self.output_base = output_base
        self.backup_m3u = backup_m3u

    def mirror_file(self, file_path: Path, target_dir: Optional[Path] = None) -> bool:
        """
        Copies a file to the target directory.
        Optionally renames .m3u files to .m3u.bak.
        """
        try:
            if target_dir:
                target_path = target_dir / file_path.name
            else:
                target_path = self.output_base / file_path.name
            
            # Optionally rename .m3u to .m3u.bak
            if self.backup_m3u and target_path.suffix.lower() == ".m3u":
                target_path = target_path.with_suffix(target_path.suffix + ".bak")
                
            target_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Copying as asset: {file_path.name}")
            shutil.copy2(file_path, target_path)
            return True
        except Exception as e:
            logger.error(f"Failed to mirror file {file_path.name}: {e}")
            return False
