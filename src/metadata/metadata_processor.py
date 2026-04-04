from pathlib import Path
from typing import Optional
import mutagen
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TPE2, TALB, TYER, TCON, ID3NoHeaderError
from mutagen.flac import FLAC

from src.core.constants import UNKNOWN_ALBUM, COVER_SEARCH_NAMES, IMAGE_EXTENSIONS
from src.metadata.metadata_analyzer import AlbumAnalyzer
from src.metadata.cover_finder import CoverArtFinder
from src.metadata.lastfm_client import LastFmClient

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

    def __init__(self, padding_manager, image_processor, lastfm_client: Optional[LastFmClient] = None):
        self.padding_manager = padding_manager
        self.image_processor = image_processor
        self.lastfm_client = lastfm_client or LastFmClient()
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
            elif ext == ".m4a":
                try:
                    from mutagen.mp4 import MP4
                    audio = MP4(source_path)
                    trkn = audio.get("trkn", [[0]])[0][0]
                    track = str(trkn) if trkn > 0 else ""
                    title = audio.get("\xa9nam", [""])[0]
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
            elif ext == ".m4a":
                try:
                    from mutagen.mp4 import MP4
                    audio = MP4(source_path)
                    album = audio.get("\xa9alb", [""])[0]
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
        elif ext == ".m4a":
            art_data, mime_type = self._apply_m4a_tags(source_path, target_tags, track_padding)

        # 2. Cover Art Logic
        if not art_data:
            art_data, mime_type = self.cover_finder.find(source_path)

        # 2.1 Online Lookup (Metadata Enrichment & Art Fallback)
        if self.lastfm_client:
            artist = self.analyzer.get_value("TPE2")
            album = self.analyzer.get_value("TALB")
            
            if artist and album:
                # We check Last.fm if:
                # 1. We don't have album art yet (Fallback)
                # 2. OR the album name looks like it needs normalization (e.g., contains '_')
                needs_art = not art_data
                needs_normalization = "_" in album or self.analyzer.get_value("TALB_ORIGINAL") != album
                
                if needs_art or needs_normalization:
                    l_data, l_mime, off_art, off_alb = self.lastfm_client.get_album_art(artist, album)
                    
                    # Store official names to restore special characters in tags
                    if off_art:
                        self.analyzer.set_value("TPE2", off_art)
                    if off_alb:
                        self.analyzer.set_value("TALB", off_alb)
                    
                    # Only use l_data if we don't have art from local source
                    if needs_art and l_data:
                        art_data, mime_type = l_data, l_mime

        if art_data:
            art_data, mime_type = self.image_processor.process_cover(art_data)
            target_tags.add(APIC(encoding=3, mime=mime_type, type=3, desc='Cover', data=art_data))
            # Save a local cover file if none exists in the output directory
            self._save_local_cover(target_path.parent, art_data, mime_type)
        
        # 3. Finalization & Consolidation
        if "TIT2" not in target_tags:
            target_tags.add(TIT2(encoding=3, text=source_path.stem))

        self._enforce_consolidated_meta(target_tags)
        target_tags.save(target_path, v2_version=3)

    def _save_local_cover(self, directory: Path, data: bytes, mime: str):
        """
        Saves the processed album art to the local directory as 'cover.jpg' or 'cover.png'.
        Only saves if no common cover art file (cover, folder, front) already exists.
        """
        try:
            # Check for existing cover-like files using global constants
            for f in directory.iterdir():
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                    if any(kw in f.stem.lower() for kw in COVER_SEARCH_NAMES):
                        return # Already exists, skipping

            # Determine extension
            ext = ".png" if mime == "image/png" else ".jpg"
            target_file = directory / f"cover{ext}"
            
            from loguru import logger
            logger.info(f"Saving found album art as local asset: {target_file.name}")
            target_file.write_bytes(data)
        except Exception:
            pass

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

    def _apply_m4a_tags(self, path: Path, target_tags: ID3, padding: int) -> (Optional[bytes], str):
        art_data, mime = None, "image/jpeg"
        try:
            from mutagen.mp4 import MP4, MP4Cover
            from mutagen.id3 import TIT2, TPE1, TPE2, TALB, TYER, TCON, TRCK
            audio = MP4(path)
            
            mp4_to_id3 = {
                "\xa9nam": TIT2,
                "\xa9ART": TPE1,
                "aART": TPE2,
                "\xa9alb": TALB,
                "\xa9day": TYER,
                "\xa9gen": TCON
            }
            
            for mp4_key, id3_frame in mp4_to_id3.items():
                if mp4_key in audio:
                    val = str(audio[mp4_key][0])
                    target_tags.add(id3_frame(encoding=3, text=[val]))
                    
            if "trkn" in audio:
                trkn = audio["trkn"][0][0]
                if trkn > 0:
                    track_str = str(trkn)
                    if padding > 0:
                        track_str = self.padding_manager.apply_padding(track_str, padding)
                    target_tags.add(TRCK(encoding=3, text=[track_str]))
                    
            if "covr" in audio and audio["covr"]:
                cover = audio["covr"][0]
                art_data = bytes(cover)
                mime = "image/png" if getattr(cover, "imageformat", None) == MP4Cover.FORMAT_PNG else "image/jpeg"
        except Exception as e:
            pass
        return art_data, mime

    def _enforce_consolidated_meta(self, target_tags: ID3):
        """Standardizes Album, Artist, Year, Genre based on analysis."""
        mapping = {"TALB": TALB, "TPE2": TPE2, "TYER": TYER, "TCON": TCON}
        for frame_id, cls in mapping.items():
            val = self.analyzer.get_value(frame_id)
            if val:
                target_tags.add(cls(encoding=3, text=val))
