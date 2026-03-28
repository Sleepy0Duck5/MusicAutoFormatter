import subprocess
from pathlib import Path
from typing import Optional

class AudioConverter:
    """
    Handles audio format conversion using FFmpeg.
    """
    def __init__(self, bitrate: str = "320k"):
        self.bitrate = bitrate

    def convert_to_mp3(self, input_path: Path, output_path: Path) -> bool:
        """
        Converts any audio file supported by FFmpeg to a standardized MP3.
        Strips all existing metadata during the process to allow for clean re-tagging.
        """
        # -y to overwrite (we handle existence check at directory level)
        # -map_metadata -1 to strip original tags
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-ab", self.bitrate,
            "-map_metadata", "-1",
            str(output_path)
        ]
        
        try:
            print(f"    [i] Converting {input_path.name} to MP3...")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError as e:
            print(f"    [!] FFmpeg error during conversion of {input_path.name}: {e}")
            return False
        except FileNotFoundError:
            print("    [!] FFmpeg not found. Please ensure it is installed and in your system PATH.")
            return False
