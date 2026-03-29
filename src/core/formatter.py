from pathlib import Path
from typing import Optional
from loguru import logger
from src.metadata.metadata_utils import TrackPaddingManager
from src.processing.audio_utils import AudioConverter
from src.processing.image_utils import ImageProcessor
from src.processing.file_utils import FileMirror
from src.metadata.metadata_processor import MetadataManager
from src.library.scanner_utils import LibraryScanner
from src.library.library_manager import LibraryManager
from src.core.constants import (
    DEFAULT_BITRATE,
    DEFAULT_MAX_ART_SIZE,
    DEFAULT_TARGET_IMAGE_SIZE,
    DEFAULT_TRACK_PADDING,
    MUSIC_EXTENSIONS,
)

class MusicFormatter:
    def __init__(self, output_dir: str = "output", bitrate: str = DEFAULT_BITRATE, max_art_size: int = DEFAULT_MAX_ART_SIZE, delete_source: bool = True, backup_m3u: bool = False, create_dir: bool = True, use_folder_as_album: bool = False):
        self.output_dir = Path(output_dir)
        self.use_folder_as_album = use_folder_as_album
        if create_dir:
            if self.output_dir.exists():
                raise FileExistsError(f"[!] Output destination '{output_dir}' already exists. Please remove it or choose a different name.")
            self.output_dir.mkdir(parents=True)
        self.delete_source = delete_source
        self.padding_manager = TrackPaddingManager(min_padding=DEFAULT_TRACK_PADDING)
        self.converter = AudioConverter(bitrate=bitrate)
        self.image_processor = ImageProcessor(target_size=DEFAULT_TARGET_IMAGE_SIZE, max_filesize=max_art_size)
        self.mirror = FileMirror(output_base=self.output_dir, backup_m3u=backup_m3u)
        self.metadata_manager = MetadataManager(self.padding_manager, self.image_processor)
        self.scanner = LibraryScanner(exclude_dirs=[str(self.output_dir.resolve())])
        self.library_manager = LibraryManager(self.output_dir, self.metadata_manager)

    def create_output_dir(self):
        """
        Manually creates the output directory. Performs existence check first.
        """
        if self.output_dir.exists():
            raise FileExistsError(f"Output directory '{self.output_dir}' already exists.")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_album(self, files: list[Path]):
        """
        Gathers album-wide metadata and checks for potential output directory collisions.
        """
        self.metadata_manager.analyze_album(files)
        
        # Override album tag if requested
        if self.use_folder_as_album:
            self.metadata_manager.analyzer.consolidated["TALB"] = self.output_dir.name
            
        # Check for early collision: if the final album folder already exists
        dominant_album = self.metadata_manager.analyzer.get_value("TALB")
        if dominant_album:
            # Sanitize name just like LibraryManager does
            clean_album = "".join(c for c in dominant_album if c not in r'\/:*?"<>|').strip()
            final_path = self.output_dir.parent / clean_album
            
            # If the calculated final path exists and it's not our current output_dir, it's a conflict
            if final_path.exists() and final_path.resolve() != self.output_dir.resolve():
                logger.error(f"Naming collision detected: '{clean_album}' already exists.")
                raise FileExistsError(
                    f"[!] The resulting album folder '{clean_album}' already exists in the output directory. "
                    "Please remove it or rename the source to avoid overwriting."
                )

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
        
        target_dir = self.output_dir
        if base_path:
            relative_dir = file_path.parent.relative_to(base_path)
            # If forcing custom album name, strip the original album's folder level 
            # while preserving structural folders like 'Disc 1'.
            if self.use_folder_as_album and len(relative_dir.parts) > 0:
                first_part = relative_dir.parts[0]
                if not self.library_manager.GENERIC_FOLDER_RE.match(first_part):
                    relative_dir = Path(*relative_dir.parts[1:]) if len(relative_dir.parts) > 1 else Path("")
                    
            target_dir = self.output_dir / relative_dir
        
        success = False
        if ext in MUSIC_EXTENSIONS:
            success = self._convert_and_tag(file_path, target_dir, track_padding)
        else:
            success = self.mirror.mirror_file(file_path, target_dir)
            
        return success

    def delete_source_files(self, files: list[Path]):
        """
        Bulk deletes a list of source files. Usually called after verifying 
        that all files in a batch were processed successfully.
        """
        for file_path in files:
            try:
                if file_path.exists():
                    logger.warning(f"Deleting source file: {file_path.name}")
                    file_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete source file {file_path.name}: {e}")

    def _convert_and_tag(self, file_path: Path, target_dir: Optional[Path] = None, track_padding: int = 0) -> bool:
        logger.info(f"Processing: {file_path.name}")
        
        # 2. Get standardized filename: "01. My Song"
        formatted_name = self.metadata_manager.get_formatted_filename(file_path, track_padding)
        target_filename = formatted_name + ".mp3"

        # 3. Resolve target path preserving original hierarchy
        if target_dir:
            target_path = target_dir / target_filename
        else:
            target_path = self.output_dir / target_filename
            
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Convert to MP3
        if not self.converter.convert_to_mp3(file_path, target_path):
            logger.error(f"Failed to convert {file_path.name}")
            return False

        # 2. Extract and Process Metadata/Album Art
        try:
            self.metadata_manager.apply_metadata(file_path, target_path, track_padding)
            logger.success(f"Done: {target_path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply metadata for {file_path.name}: {e}")
            return False


