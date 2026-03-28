from pathlib import Path
from typing import Optional
from loguru import logger
from .metadata_utils import TrackPaddingManager
from .audio_utils import AudioConverter
from .image_utils import ImageProcessor
from .file_utils import FileMirror
from .metadata_processor import MetadataManager
from .scanner_utils import LibraryScanner
from .library_manager import LibraryManager

class MusicFormatter:
    def __init__(self, output_dir: str = "output", bitrate: str = "320k", max_art_size: int = 2 * 1024 * 1024):
        self.output_dir = Path(output_dir)
        if self.output_dir.exists():
            raise FileExistsError(f"[!] Output destination '{output_dir}' already exists. Please remove it or choose a different name.")
        
        self.output_dir.mkdir(parents=True)
        self.padding_manager = TrackPaddingManager(min_padding=2)
        self.converter = AudioConverter(bitrate=bitrate)
        self.image_processor = ImageProcessor(target_size=(800, 800), max_filesize=max_art_size)
        self.mirror = FileMirror(output_base=self.output_dir)
        self.metadata_manager = MetadataManager(self.padding_manager, self.image_processor)
        self.scanner = LibraryScanner(exclude_dirs=[str(self.output_dir.resolve())])
        self.library_manager = LibraryManager(self.output_dir, self.metadata_manager)

    def finalize_library(self):
        """
        Finalizing the library structure using the dedicated LibraryManager.
        """
        self.library_manager.finalize_structure()

    def process_file(self, file_path: Path, base_path: Optional[Path] = None, track_padding: int = 0):
        ext = file_path.suffix.lower()
        music_extensions = [".flac", ".wav", ".mp3"]
        
        if ext in music_extensions:
            self._convert_and_tag(file_path, base_path, track_padding)
        else:
            self.mirror.mirror_file(file_path, base_path)

    def _convert_and_tag(self, file_path: Path, base_path: Optional[Path] = None, track_padding: int = 0):
        logger.info(f"Processing: {file_path.name}")
        
        # 2. Get standardized filename: "01. My Song"
        formatted_name = self.metadata_manager.get_formatted_filename(file_path, track_padding)
        target_filename = formatted_name + ".mp3"

        # 3. Resolve target path preserving original hierarchy
        if base_path:
            relative_dir = file_path.parent.relative_to(base_path)
            target_path = self.output_dir / relative_dir / target_filename
        else:
            target_path = self.output_dir / target_filename
            
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Convert to MP3
        if not self.converter.convert_to_mp3(file_path, target_path):
            logger.error(f"Failed to convert {file_path.name}")
            return

        # 2. Extract and Process Metadata/Album Art
        self.metadata_manager.apply_metadata(file_path, target_path, track_padding)
        logger.success(f"Done: {target_path.name}")


