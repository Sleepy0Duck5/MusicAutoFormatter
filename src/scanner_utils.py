from pathlib import Path
from typing import List

class LibraryScanner:
    """
    Scans a directory for music and other files while applying filtering rules.
    """
    def __init__(self, exclude_dirs: List[str] = None):
        self.exclude_dirs = exclude_dirs or []

    def scan(self, input_path: Path) -> List[Path]:
        """
        Recursively scans the input path. If a file is provided, returns that file.
        Returns a list of Path objects for all found files.
        """
        if input_path.is_file():
            return [input_path]
            
        if not input_path.is_dir():
            return []
            
        found_files = []
        # rglob('*') finds all files and dirs recursively
        for f in input_path.rglob("*"):
            if not f.is_file():
                continue
                
            # Skip files in excluded directories (like the output directory)
            should_skip = False
            for exclude in self.exclude_dirs:
                if exclude in str(f.resolve()):
                    should_skip = True
                    break
            
            if not should_skip:
                found_files.append(f)
                
        return found_files
