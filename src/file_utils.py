import shutil
from pathlib import Path
from typing import Optional

class FileMirror:
    """
    Handles file mirroring and specific file renaming rules (e.g., .m3u to .m3u.bak).
    """
    def __init__(self, output_base: Path):
        self.output_base = output_base

    def mirror_file(self, file_path: Path, base_path: Optional[Path] = None):
        """
        Copies a file to the output directory while maintaining relative structure.
        Renames .m3u files to .m3u.bak.
        """
        if base_path:
            relative_path = file_path.relative_to(base_path)
            target_path = self.output_base / relative_path
        else:
            target_path = self.output_base / file_path.name
        
        # Rename .m3u to .m3u.bak as per requirements
        if target_path.suffix.lower() == ".m3u":
            target_path = target_path.with_suffix(target_path.suffix + ".bak")
            
        target_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[*] Copying as asset: {file_path.name}")
        shutil.copy2(file_path, target_path)
