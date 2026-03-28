from pathlib import Path
from mutagen.id3 import ID3
from mutagen.flac import FLAC

class TrackPaddingManager:
    """
    Manages track number padding calculation for audio libraries.
    """
    def __init__(self, min_padding: int = 2):
        self.min_padding = min_padding
        self.padding_cache = {}

    def get_padding_for_dir(self, directory: Path) -> int:
        """
        Scans a directory for music files and calculates the required padding length
        based on the maximum track number found.
        """
        if directory in self.padding_cache:
            return self.padding_cache[directory]

        max_track = 0
        music_extensions = [".flac", ".wav", ".mp3"]
        
        try:
            for f in directory.iterdir():
                if not f.is_file() or f.suffix.lower() not in music_extensions:
                    continue
                
                try:
                    ext = f.suffix.lower()
                    track_val = ""
                    if ext == ".flac":
                        audio = FLAC(f)
                        track_val = audio.get("tracknumber", ["0"])[0]
                    elif ext in [".mp3", ".wav"]:
                        audio = ID3(f)
                        track_val = str(audio.get("TRCK", "0"))
                    
                    if track_val:
                        # Handle "1/12" type track numbers
                        num = int(track_val.split('/')[0])
                        if num > max_track:
                            max_track = num
                except Exception:
                    continue
        except Exception:
            # Handle cases where folder might be inaccessible
            pass
        
        padding = self.min_padding
        if max_track > 0:
            padding = max(self.min_padding, len(str(max_track)))
            
        self.padding_cache[directory] = padding
        return padding

    def apply_padding(self, track_val: str, padding: int) -> str:
        """
        Applies padding to a track number string.
        """
        if not track_val or padding <= 0:
            return track_val
            
        try:
            # Strip total (1/12 -> 1)
            num_only = track_val.split('/')[0]
            return str(int(num_only)).zfill(padding)
        except (ValueError, TypeError):
            return track_val
