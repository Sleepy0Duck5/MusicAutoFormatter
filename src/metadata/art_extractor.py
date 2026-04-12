from pathlib import Path
from typing import Optional, Tuple
from mutagen.id3 import ID3
from mutagen.flac import FLAC

class EmbeddedArtExtractor:
    """
    Utility class to extract embedded album art from various audio formats.
    """

    @staticmethod
    def extract(path: Path) -> Tuple[Optional[bytes], str]:
        """
        Detects the format and extracts the embedded album art.
        Returns (art_data, mime_type).
        """
        ext = path.suffix.lower()
        if ext == ".flac":
            return EmbeddedArtExtractor._get_flac_art(path)
        elif ext in [".mp3", ".wav"]:
            return EmbeddedArtExtractor._get_id3_art(path)
        elif ext == ".m4a":
            return EmbeddedArtExtractor._get_m4a_art(path)
        return None, "image/jpeg"

    @staticmethod
    def _get_flac_art(path: Path) -> Tuple[Optional[bytes], str]:
        try:
            audio = FLAC(path)
            if audio.pictures:
                return audio.pictures[0].data, audio.pictures[0].mime
        except Exception:
            pass
        return None, "image/jpeg"

    @staticmethod
    def _get_id3_art(path: Path) -> Tuple[Optional[bytes], str]:
        try:
            tags = ID3(path)
            for frame_id in tags:
                if frame_id.startswith("APIC"):
                    return tags[frame_id].data, tags[frame_id].mime
        except Exception:
            pass
        return None, "image/jpeg"

    @staticmethod
    def _get_m4a_art(path: Path) -> Tuple[Optional[bytes], str]:
        try:
            from mutagen.mp4 import MP4, MP4Cover
            audio = MP4(path)
            if "covr" in audio and audio["covr"]:
                cover = audio["covr"][0]
                mime = "image/png" if getattr(cover, "imageformat", None) == MP4Cover.FORMAT_PNG else "image/jpeg"
                return bytes(cover), mime
        except Exception:
            pass
        return None, "image/jpeg"
