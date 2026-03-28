from pathlib import Path
from typing import Optional, Any
import mutagen
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TPE2, TALB, TYER, TCON, ID3NoHeaderError
from mutagen.flac import FLAC
from loguru import logger

class MetadataManager:
    """
    Handles robust metadata cloning and translation between audio formats.
    """
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

    def get_formatted_filename(self, source_path: Path, track_padding: int = 0) -> str:
        """
        Extracts track and title to form a filename like "01. My Song".
        Fallback to original filename if tags are missing.
        """
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
                # If tags empty, try generic File (for RIFF tags etc.)
                audio = mutagen.File(source_path)
                if audio and audio.tags:
                    # Generic mapping is hard, fallback to stem if no luck
                    pass

            if track:
                track = self.padding_manager.apply_padding(track, track_padding)
            
            if not title:
                title = source_path.stem
            
            # Clean for forbidden characters in filenames
            # Remove / \ : * ? " < > |
            clean_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()
            
            if track:
                return f"{track}. {clean_title}"
            return clean_title
            
        except Exception:
            return source_path.stem

    def get_album_name(self, source_path: Path) -> str:
        """
        Extracts the album name from tags.
        Fallback to "Unknown Album" if not found.
        """
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
            
        if not album:
            return "Unknown Album"
            
        # Clean for forbidden characters in folder names
        return "".join(c for c in album if c not in r'\/:*?"<>|').strip()

    def apply_metadata(self, source_path: Path, target_path: Path, track_padding: int = 0):
        """
        Copies metadata from source to target, applying padding and image optimization.
        """
        try:
            target_tags = ID3(target_path)
        except ID3NoHeaderError:
            target_tags = ID3()
        
        target_tags.delall("APIC")
        art_data = None
        mime_type = "image/jpeg"

        ext = source_path.suffix.lower()
        if ext == ".flac":
            source_audio = FLAC(source_path)
            for key, values in source_audio.items():
                key_lower = key.lower()
                if key_lower in self.VORBIS_TO_ID3:
                    frame_handler = self.VORBIS_TO_ID3[key_lower]
                    for val in values:
                        if key_lower == "tracknumber" and track_padding > 0:
                            val = self.padding_manager.apply_padding(val, track_padding)
                        
                        if callable(frame_handler) and not isinstance(frame_handler, type):
                            target_tags.add(frame_handler(val))
                        else:
                            target_tags.add(frame_handler(encoding=3, text=[val]))
            
            if source_audio.pictures:
                art_data = source_audio.pictures[0].data
                mime_type = source_audio.pictures[0].mime
        
        elif ext == ".wav":
            try:
                # WAV can contain ID3 tags
                source_tags = ID3(source_path)
                for frame_id, frame in source_tags.items():
                    if not frame_id.startswith("APIC"):
                        if frame_id == "TRCK" and track_padding > 0:
                            raw_val = str(frame.text[0])
                            frame.text = [self.padding_manager.apply_padding(raw_val, track_padding)]
                        target_tags.add(frame)
                
                for frame in source_tags.values():
                    if isinstance(frame, APIC):
                        art_data = frame.data
                        mime_type = frame.mime
                        break
            except Exception:
                # If no ID3, or generic mutagen.File support
                try:
                    audio = mutagen.File(source_path)
                    if audio and audio.tags:
                        # Some WAVs might have RIFF tags or others, 
                        # but ID3v2 is standard in many players.
                        pass 
                except Exception:
                    pass
        
        elif ext == ".mp3":
            try:
                source_tags = ID3(source_path)
                for frame_id, frame in source_tags.items():
                    if not frame_id.startswith("APIC"):
                        if frame_id == "TRCK" and track_padding > 0:
                            raw_val = str(frame.text[0])
                            frame.text = [self.padding_manager.apply_padding(raw_val, track_padding)]
                        target_tags.add(frame)
                
                for frame in source_tags.values():
                    if isinstance(frame, APIC):
                        art_data = frame.data
                        mime_type = frame.mime
                        break
            except ID3NoHeaderError:
                pass

        # External cover search and image processing is handled via manager dependencies
        if not art_data:
            art_data, mime_type = self._find_external_cover(source_path)

        if art_data:
            art_data, mime_type = self.image_processor.process_cover(art_data)
            target_tags.add(APIC(
                encoding=3,
                mime=mime_type,
                type=3,
                desc='Cover',
                data=art_data
            ))
        
        if "TIT2" not in target_tags:
            target_tags.add(TIT2(encoding=3, text=source_path.stem))

        target_tags.save(target_path, v2_version=3)

    def _find_external_cover(self, source_path: Path) -> (Optional[bytes], str):
        cover_names = ["cover", "folder", "front", "album"]
        extensions = [".jpg", ".jpeg", ".png"]
        
        for directory in [source_path.parent, source_path.parent.parent]:
            if not directory or directory == Path("."): continue
            
            for name in cover_names:
                for ext in extensions:
                    cover_path = directory / f"{name}{ext}"
                    if cover_path.exists():
                        logger.debug(f"Found external cover art: {cover_path.name}")
                        mime = "image/png" if ext == ".png" else "image/jpeg"
                        return cover_path.read_bytes(), mime
        return None, "image/jpeg"
