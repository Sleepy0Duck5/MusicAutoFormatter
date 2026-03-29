import subprocess
from pathlib import Path
from loguru import logger
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from src.core.constants import DEFAULT_BITRATE

class AudioConverter:
    """
    Handles audio format conversion using FFmpeg with integrity checks.
    """
    def __init__(self, bitrate: str = DEFAULT_BITRATE):
        self.bitrate = bitrate

    def convert_to_mp3(self, input_path: Path, output_path: Path) -> bool:
        """
        Converts any audio file to a standardized MP3.
        Uses a temporary file and verifies duration to ensure the output is complete.
        """
        # Use a temporary file to avoid "half-baked" files if the process is interrupted
        temp_output = output_path.with_suffix(".tmp.mp3")
        
        # -y: overwrite
        # -nostdin: prevents ffmpeg from grabbing interactive input in loops
        # -v error: only show actual errors in stderr
        # -vn: skip video/covers processing (handled separately)
        # -map_metadata -1: strip all tags for clean re-tagging
        cmd = [
            "ffmpeg", "-y", "-nostdin",
            "-v", "error",
            "-i", str(input_path),
            "-ab", self.bitrate,
            "-map_metadata", "-1",
            "-vn",
            str(temp_output)
        ]
        
        try:
            logger.debug(f"Converting {input_path.name} to MP3...")
            # Capture stderr to log if something goes wrong
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # 1. Check if file exists and has size
            if not temp_output.exists() or temp_output.stat().st_size == 0:
                logger.error(f"FFmpeg failed to create output for {input_path.name}")
                return False

            # 2. Verify duration integrity (catch truncated files)
            if self.verify_duration(input_path, temp_output):
                # Success! Move to final destination
                if output_path.exists():
                    output_path.unlink()
                temp_output.rename(output_path)
                return True
            else:
                logger.error(f"Integrity check failed: Duration mismatch for {input_path.name}")
                if temp_output.exists():
                    temp_output.unlink()
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed for {input_path.name}: {e.stderr.strip()}")
            if temp_output.exists():
                temp_output.unlink()
            return False
        except FileNotFoundError:
            logger.critical("FFmpeg not found. Please ensure it is installed and in your system PATH.")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error during conversion of {input_path.name}: {e}")
            if temp_output.exists():
                temp_output.unlink()
            return False

    def verify_duration(self, source: Path, target: Path, threshold: float = 0.5) -> bool:
        """
        Compares duration between source and target to ensure no significant data loss.
        Threshold is in seconds.
        """
        try:
            # Get source duration
            src_len = 0
            if source.suffix.lower() == ".flac":
                src_len = FLAC(source).info.length
            elif source.suffix.lower() == ".mp3":
                src_len = MP3(source).info.length
            elif source.suffix.lower() == ".m4a":
                from mutagen.mp4 import MP4
                src_len = MP4(source).info.length
            
            # Get target duration
            tgt_len = 0
            if target.suffix.lower() == ".mp3" or target.suffix.lower().endswith(".tmp.mp3"):
                tgt_len = MP3(target).info.length
            
            # If we can't determine duration (e.g. unknown format), we trust ffmpeg's exit code
            if src_len == 0 or tgt_len == 0:
                logger.warning(f"Could not verify duration for {source.name}. Trusting FFmpeg exit code.")
                return True
            
            diff = abs(src_len - tgt_len)
            if diff > threshold:
                logger.warning(f"Duration difference detected: {diff:.2f}s (Src: {src_len:.2f}s, Tgt: {tgt_len:.2f}s)")
                return False
                
            return True
        except Exception as e:
            logger.debug(f"Duration verification skipped for {source.name}: {e}")
            return True # Don't fail if just the check fails

