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
    def __init__(self, output_dir: str = "output", bitrate: str = "320k", max_art_size: int = 2 * 1024 * 1024, delete_source: bool = True):
        self.output_dir = Path(output_dir)
        if self.output_dir.exists():
            raise FileExistsError(f"[!] Output destination '{output_dir}' already exists. Please remove it or choose a different name.")
        
        self.output_dir.mkdir(parents=True)
        self.delete_source = delete_source
        self.padding_manager = TrackPaddingManager(min_padding=2)
        self.converter = AudioConverter(bitrate=bitrate)
        self.image_processor = ImageProcessor(target_size=(800, 800), max_filesize=max_art_size)
        self.mirror = FileMirror(output_base=self.output_dir)
        self.metadata_manager = MetadataManager(self.padding_manager, self.image_processor)
        self.scanner = LibraryScanner(exclude_dirs=[str(self.output_dir.resolve())])
        self.library_manager = LibraryManager(self.output_dir, self.metadata_manager)

    def finalize_library(self, source_path: Optional[Path] = None):
        """
        Finalizing the library structure and cleaning up empty source folders.
        """
        self.library_manager.finalize_structure()
        
        if source_path and self.delete_source:
            self._cleanup_source_dir(source_path)

    def _cleanup_source_dir(self, directory: Path):
        """
        Recursively removes empty directories in the source path.
        """
        if not directory.is_dir():
            return

        # Bottom-up approach to remove nested empty directories first
        for item in list(directory.iterdir()):
            if item.is_dir():
                self._cleanup_source_dir(item)
        
        # After processing subdirectories, check if this one is now empty
        try:
            if not any(directory.iterdir()):
                logger.warning(f"Removing empty source directory: {directory.name}")
                directory.rmdir()
        except Exception as e:
            logger.debug(f"Could not remove directory {directory}: {e}")

    def process_file(self, file_path: Path, base_path: Optional[Path] = None, track_padding: int = 0):
        ext = file_path.suffix.lower()
        music_extensions = [".flac", ".wav", ".mp3"]
        
        success = False
        if ext in music_extensions:
            success = self._convert_and_tag(file_path, base_path, track_padding)
        else:
            success = self.mirror.mirror_file(file_path, base_path)
            
        if success and self.delete_source:
            try:
                logger.warning(f"Deleting source file: {file_path.name}")
                file_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete source file {file_path.name}: {e}")

    def _convert_and_tag(self, file_path: Path, base_path: Optional[Path] = None, track_padding: int = 0) -> bool:
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
            return False

        # 2. Extract and Process Metadata/Album Art
        self.metadata_manager.apply_metadata(file_path, target_path, track_padding)
        logger.success(f"Done: {target_path.name}")
        return True


