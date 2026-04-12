from collections import Counter
from pathlib import Path
from loguru import logger
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from src.core.constants import MUSIC_EXTENSIONS

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

        albums, artists, album_artists, years, genres, composers, comments, disc_numbers = [], [], [], [], [], [], [], []

        for f in files:
            ext = f.suffix.lower()
            if ext not in MUSIC_EXTENSIONS:
                continue
            try:
                if ext == ".flac":
                    audio = FLAC(f)
                    albums.append(audio.get("album", [""])[0])
                    artists.append(audio.get("artist", [""])[0])
                    aa = audio.get("albumartist", audio.get("album artist", [""]))[0]
                    album_artists.append(aa)
                    years.append(audio.get("date", audio.get("year", [""]))[0])
                    genres.append(audio.get("genre", [""])[0])
                    composers.append(audio.get("composer", [""])[0])
                    comments.append(audio.get("comment", [""])[0])
                    disc_numbers.append(audio.get("discnumber", [""])[0])
                elif ext in [".mp3", ".wav"]:
                    try:
                        tags = ID3(f)
                        albums.append(str(tags.get("TALB", "")))
                        artists.append(str(tags.get("TPE1", "")))
                        album_artists.append(str(tags.get("TPE2", "")))
                        years.append(str(tags.get("TYER", tags.get("TDRC", ""))))
                        genres.append(str(tags.get("TCON", "")))
                        composers.append(str(tags.get("TCOM", "")))
                        # Handle COMM with potential descriptions/langs
                        comm = ""
                        for frame in tags.getall("COMM"):
                            comm = str(frame.text[0])
                            break
                        comments.append(comm)
                        disc_numbers.append(str(tags.get("TPOS", "")))
                    except Exception:
                        pass
                elif ext == ".m4a":
                    try:
                        from mutagen.mp4 import MP4
                        audio = MP4(f)
                        albums.append(audio.get("\xa9alb", [""])[0])
                        artists.append(audio.get("\xa9ART", [""])[0])
                        album_artists.append(audio.get("aART", [""])[0])
                        years.append(audio.get("\xa9day", [""])[0])
                        genres.append(audio.get("\xa9gen", [""])[0])
                        composers.append(audio.get("\xa9wrt", [""])[0])
                        comments.append(audio.get("\xa9cmt", [""])[0])
                        disc_numbers.append(str(audio.get("disk", [[0]])[0][0]))
                    except Exception:
                        pass
            except Exception:
                continue

        self.consolidated = {
            "TALB": self._get_dominant(albums),
            "TPE1": self._get_dominant(artists),
            "TPE2": self._get_dominant(album_artists),
            "TYER": self._get_dominant(years),
            "TCON": self._get_dominant(genres),
            "TCOM": self._get_dominant(composers),
            "COMM": self._get_dominant(comments),
            "TPOS": self._get_dominant(disc_numbers)
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

    def set_value(self, tag_id: str, value: str):
        """Manually updates a consolidated value (e.g., from online search)."""
        if value:
            self.consolidated[tag_id] = value
