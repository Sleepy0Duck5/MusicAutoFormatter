from pathlib import Path
from typing import Optional
import mutagen
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TPE2, TALB, TYER, TCON, ID3NoHeaderError
from mutagen.flac import FLAC

from .constants import UNKNOWN_ALBUM
from .metadata_analyzer import AlbumAnalyzer
from .cover_finder import CoverArtFinder

class MetadataManager:
    """
    Orchestrates metadata extraction, consolidation, and application.
    Delegates analysis to AlbumAnalyzer and image search to CoverArtFinder.
    """
    # Mapper between Vorbis (FLAC) keys and ID3 frames
    VORBIS_TO_ID3 = {
        "title": TIT2,
        "artist": TPE1,
        "albumartist": TPE2,
        "album artist": TPE2,
        "album": TALB,
        "date": TYER,
        "year": TYER,
        "genre": TCON,
        "tracknumber": lambda text: mutagen.id3.TRCK(encoding=3, text=text),
        "discnumber": lambda text: mutagen.id3.TPOS(encoding=3, text=text),
        "composer": lambda text: mutagen.id3.TCOM(encoding=3, text=text),
        "comment": lambda text: mutagen.id3.COMM(encoding=3, lang="eng", desc="", text=text),
    }

    def __init__(self, padding_manager, image_processor):
        self.padding_manager = padding_manager
        self.image_processor = image_processor
        self.analyzer = AlbumAnalyzer()
        self.cover_finder = CoverArtFinder()

    def analyze_album(self, files: list[Path]):
        """Delegates album-wide analysis to the specialized analyzer."""
        self.analyzer.analyze(files)

    def get_formatted_filename(self, source_path: Path, track_padding: int = 0) -> str:
        """Extracts track and title to form a standardized filename like '01. My Song'."""
        track = ""
        title = ""
        ext = source_path.suffix.lower()

        try:
            if ext == ".flac":
                audio = FLAC(source_path)
                track = audio.get("tracknumber", [""])[0]
                title = audio.get("title", [""])[0]
            elif ext in [".mp3", ".wav"]:
                try:
                    tags = ID3(source_path)
                    track = str(tags.get("TRCK", ""))
                    title = str(tags.get("TIT2", ""))
                except Exception:
                    pass

            if not track:
                audio = mutagen.File(source_path)
                if audio and hasattr(audio, 'tags') and audio.tags:
                    # Fallback generic metadata extraction if needed
                    pass

            if track:
                track = self.padding_manager.apply_padding(track, track_padding)
            
            if not title:
                title = source_path.stem
            
            # Sanitization
            clean_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()
            
            return f"{track}. {clean_title}" if track else clean_title
            
        except Exception:
            return source_path.stem

    def get_album_name(self, source_path: Path) -> str:
        """Extracts and sanitizes the album name from tags."""
        ext = source_path.suffix.lower()
        album = ""

        try:
            if ext == ".flac":
                audio = FLAC(source_path)
                album = audio.get("album", [""])[0]
            elif ext in [".mp3", ".wav"]:
                try:
                    tags = ID3(source_path)
                    album = str(tags.get("TALB", ""))
                except Exception:
                    pass
        except Exception:
            pass
            
        album = album if album else UNKNOWN_ALBUM
        return "".join(c for c in album if c not in r'\/:*?"<>|').strip()

    def apply_metadata(self, source_path: Path, target_path: Path, track_padding: int = 0):
        """Copies and standardizes metadata from source to target MP3."""
        try:
            target_tags = ID3(target_path)
        except ID3NoHeaderError:
            target_tags = ID3()
        
        target_tags.delall("APIC")
        art_data, mime_type = None, "image/jpeg"

        # 1. Extract from Source
        ext = source_path.suffix.lower()
        if ext == ".flac":
            art_data, mime_type = self._apply_flac_tags(source_path, target_tags, track_padding)
        elif ext in [".wav", ".mp3"]:
            art_data, mime_type = self._apply_id3_tags(source_path, target_tags, track_padding)

        # 2. Cover Art Logic
        if not art_data:
            art_data, mime_type = self.cover_finder.find(source_path)

        if art_data:
            art_data, mime_type = self.image_processor.process_cover(art_data)
            target_tags.add(APIC(encoding=3, mime=mime_type, type=3, desc='Cover', data=art_data))
        
        # 3. Finalization & Consolidation
        if "TIT2" not in target_tags:
            target_tags.add(TIT2(encoding=3, text=source_path.stem))

        self._enforce_consolidated_meta(target_tags)
        target_tags.save(target_path, v2_version=3)

    def _apply_flac_tags(self, path: Path, target_tags: ID3, padding: int) -> (Optional[bytes], str):
        audio = FLAC(path)
        for key, values in audio.items():
            key_lower = key.lower()
            if key_lower in self.VORBIS_TO_ID3:
                handler = self.VORBIS_TO_ID3[key_lower]
                for val in values:
                    if key_lower == "tracknumber" and padding > 0:
                        val = self.padding_manager.apply_padding(val, padding)
                    
                    if callable(handler) and not isinstance(handler, type):
                        target_tags.add(handler(val))
                    else:
                        target_tags.add(handler(encoding=3, text=[val]))
        
        if audio.pictures:
            return audio.pictures[0].data, audio.pictures[0].mime
        return None, "image/jpeg"

    def _apply_id3_tags(self, path: Path, target_tags: ID3, padding: int) -> (Optional[bytes], str):
        art_data, mime = None, "image/jpeg"
        try:
            source_tags = ID3(path)
            for frame_id, frame in source_tags.items():
                if frame_id.startswith("APIC"):
                    art_data, mime = frame.data, frame.mime
                    continue
                
                if frame_id == "TRCK" and padding > 0:
                    raw_val = str(frame.text[0])
                    frame.text = [self.padding_manager.apply_padding(raw_val, padding)]
                target_tags.add(frame)
        except Exception:
            pass
        return art_data, mime

    def _enforce_consolidated_meta(self, target_tags: ID3):
        """Standardizes Album, Artist, Year, Genre based on analysis."""
        mapping = {"TALB": TALB, "TPE2": TPE2, "TYER": TYER, "TCON": TCON}
        for frame_id, cls in mapping.items():
            val = self.analyzer.get_value(frame_id)
            if val:
                target_tags.add(cls(encoding=3, text=val))
