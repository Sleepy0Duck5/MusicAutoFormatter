from collections import Counter
from pathlib import Path
from loguru import logger
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from .constants import MUSIC_EXTENSIONS

class AlbumAnalyzer:
    """
    Analyzes multiple audio files to find dominant/majority metadata
    (Title, Artist, Year, Genre) for album consolidation.
    """
    def __init__(self):
        self.consolidated = {}

    def analyze(self, files: list[Path]):
        """
        Scans files to determine dominant metadata.
        """
        self.consolidated = {}
        if not files:
            return

        albums, artists, years, genres = [], [], [], []

        for f in files:
            ext = f.suffix.lower()
            if ext not in MUSIC_EXTENSIONS:
                continue
            try:
                if ext == ".flac":
                    audio = FLAC(f)
                    albums.append(audio.get("album", [""])[0])
                    aa = audio.get("albumartist", audio.get("album artist", [""]))[0]
                    artists.append(aa)
                    years.append(audio.get("date", audio.get("year", [""]))[0])
                    genres.append(audio.get("genre", [""])[0])
                elif ext in [".mp3", ".wav"]:
                    try:
                        tags = ID3(f)
                        albums.append(str(tags.get("TALB", "")))
                        artists.append(str(tags.get("TPE2", "")))
                        years.append(str(tags.get("TYER", tags.get("TDRC", ""))))
                        genres.append(str(tags.get("TCON", "")))
                    except Exception:
                        pass
            except Exception:
                continue

        self.consolidated = {
            "TALB": self._get_dominant(albums),
            "TPE2": self._get_dominant(artists),
            "TYER": self._get_dominant(years),
            "TCON": self._get_dominant(genres)
        }
        
        if self.consolidated["TALB"]:
            logger.info(f"Album Analysis: Consolidated metadata found for '{self.consolidated['TALB']}'")

    def _get_dominant(self, data):
        clean = [str(x).strip() for x in data if x and str(x).strip()]
        if not clean:
            return None
        return Counter(clean).most_common(1)[0][0]

    def get_value(self, tag_id: str) -> str:
        return self.consolidated.get(tag_id)
