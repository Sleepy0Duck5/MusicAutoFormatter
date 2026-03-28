import os
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Optional
from io import BytesIO

import mutagen
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TPE2, TALB, TYER, TCON, ID3NoHeaderError
from mutagen.flac import FLAC
from PIL import Image

class MusicFormatter:
    def __init__(self, output_dir: str = "output", bitrate: str = "320k", max_art_size: int = 2 * 1024 * 1024):
        self.output_dir = Path(output_dir)
        if self.output_dir.exists():
            raise FileExistsError(f"[!] Output destination '{output_dir}' already exists. Please remove it or choose a different name.")
        
        self.bitrate = bitrate
        self.max_art_size = max_art_size
        self.output_dir.mkdir(parents=True)

    def copy_file(self, file_path: Path, base_path: Optional[Path] = None):
        print(f"[*] Copying: {file_path.name}")
        if base_path:
            relative_path = file_path.relative_to(base_path)
            target_path = self.output_dir / relative_path
        else:
            target_path = self.output_dir / file_path.name
        
        # Rename .m3u to .m3u.bak
        if target_path.suffix.lower() == ".m3u":
            target_path = target_path.with_suffix(target_path.suffix + ".bak")
            
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target_path)

    def process_file(self, file_path: Path, base_path: Optional[Path] = None):
        ext = file_path.suffix.lower()
        music_extensions = [".flac", ".wav", ".mp3"]
        
        if ext in music_extensions:
            self._convert_and_tag(file_path, base_path)
        else:
            self.copy_file(file_path, base_path)

    def _convert_and_tag(self, file_path: Path, base_path: Optional[Path] = None):
        print(f"[*] Processing: {file_path.name}")
        
        if base_path:
            relative_path = file_path.relative_to(base_path)
            target_path = self.output_dir / relative_path.with_suffix(".mp3")
        else:
            target_path = self.output_dir / (file_path.stem + ".mp3")
            
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Convert to MP3
        if not self._convert_to_mp3(file_path, target_path):
            print(f"[!] Failed to convert {file_path.name}")
            return

        # 2. Extract and Process Metadata/Album Art
        self._apply_metadata(file_path, target_path)
        print(f"[+] Done: {target_path.name}")

    def _convert_to_mp3(self, input_path: Path, output_path: Path) -> bool:
        # Use ffmpeg for conversion
        # -y to overwrite existing output
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-ab", self.bitrate,
            "-map_metadata", "-1", # Strip metadata during ffmpeg, we'll rewrite with mutagen
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!] ffmpeg error: {e}")
            return False

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

    def _apply_metadata(self, source_path: Path, target_path: Path):
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
            # Map Vorbis comments to ID3
            for key, values in source_audio.items():
                key_lower = key.lower()
                if key_lower in self.VORBIS_TO_ID3:
                    frame_handler = self.VORBIS_TO_ID3[key_lower]
                    for val in values:
                        if callable(frame_handler) and not isinstance(frame_handler, type):
                            # Lambda or custom function
                            target_tags.add(frame_handler(val))
                        else:
                            # Frame class
                            target_tags.add(frame_handler(encoding=3, text=[val]))
            
            if source_audio.pictures:
                art_data = source_audio.pictures[0].data
                mime_type = source_audio.pictures[0].mime
        
        elif ext == ".mp3":
            try:
                source_tags = ID3(source_path)
                # Copy all frames except APIC
                for frame_id, frame in source_tags.items():
                    if not frame_id.startswith("APIC"):
                        target_tags.add(frame)
                
                # Extract art
                for frame in source_tags.values():
                    if isinstance(frame, APIC):
                        art_data = frame.data
                        mime_type = frame.mime
                        break
            except ID3NoHeaderError:
                pass

        # Try external cover if missing
        if not art_data:
            art_data, mime_type = self._find_external_cover(source_path)

        # Process Album Art
        if art_data:
            if len(art_data) > self.max_art_size:
                print(f"    [i] Album art too large ({len(art_data)/1024/1024:.2f}MB). Resizing...")
                art_data = self._resize_image(art_data)
                mime_type = "image/png"
            
            target_tags.add(APIC(
                encoding=3,
                mime=mime_type,
                type=3,
                desc='Cover',
                data=art_data
            ))
        
        # Ensure at least TIT2 exists from filename if missing
        if "TIT2" not in target_tags:
            target_tags.add(TIT2(encoding=3, text=source_path.stem))

        target_tags.save(target_path, v2_version=3)

    def _find_external_cover(self, source_path: Path) -> (Optional[bytes], str):
        cover_names = ["cover", "folder", "front", "album"]
        extensions = [".jpg", ".jpeg", ".png"]
        
        # Search in current and parent directory
        for directory in [source_path.parent, source_path.parent.parent]:
            if not directory or directory == Path("."): continue
            
            for name in cover_names:
                for ext in extensions:
                    cover_path = directory / f"{name}{ext}"
                    if cover_path.exists():
                        mime = "image/png" if ext == ".png" else "image/jpeg"
                        return cover_path.read_bytes(), mime
        return None, "image/jpeg"

    def _resize_image(self, data: bytes) -> bytes:
        img = Image.open(BytesIO(data))
        # Ensure it's RGB for JPEG if needed, or just Keep PNG transparency
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
            
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        out_buf = BytesIO()
        # Save as PNG to maintain quality as requested, but user said 1MB target.
        # If PNG still too big, we could use quality JPEG.
        img.save(out_buf, format="PNG", optimize=True)
        return out_buf.getvalue()

def main():
    parser = argparse.ArgumentParser(description="Music Auto Formatter & Tagger")
    parser.add_argument("input", nargs="?", default=".", help="Input directory (default: current)")
    parser.add_argument("-o", "--output", default="output", help="Output directory (default: output)")
    parser.add_argument("-b", "--bitrate", default="320k", help="Target bitrate (default: 320k)")
    
    args = parser.parse_args()
    
    try:
        formatter = MusicFormatter(output_dir=args.output, bitrate=args.bitrate)
    except FileExistsError as e:
        print(e)
        return
    
    input_path = Path(args.input)
    extensions = [".flac", ".wav", ".mp3"]
    
    files_to_process = []
    if input_path.is_dir():
        # rglob('*') finds all files and dirs
        for f in input_path.rglob("*"):
            if f.is_file():
                # Skip files inside the output directory if it's already there
                if args.output in str(f.resolve()):
                    continue
                files_to_process.append(f)
    elif input_path.is_file():
        files_to_process = [input_path]
    
    if not files_to_process:
        print("[-] No audio files found to process.")
        return

    print(f"[*] Found {len(files_to_process)} files. Starting...")
    for f in files_to_process:
        base_dir = input_path if input_path.is_dir() else None
        formatter.process_file(f, base_path=base_dir)

if __name__ == "__main__":
    main()
