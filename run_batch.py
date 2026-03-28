import argparse
import sys
from pathlib import Path
from src.formatter import MusicFormatter

def main():
    parser = argparse.ArgumentParser(description="Batch Music Auto Formatter for Multiple Albums")
    parser.add_argument("input", help="Parent directory containing multiple album folders")
    parser.add_argument("-o", "--output", default="output", help="Base output directory (default: output)")
    parser.add_argument("-b", "--bitrate", default="320k", help="Target bitrate (default: 320k)")
    
    args = parser.parse_args()
    
    input_base = Path(args.input)
    output_base = Path(args.output)
    
    if not input_base.is_dir():
        print(f"[!] Input path '{input_base}' is not a directory.")
        sys.exit(1)

    # Gather all subdirectories in the input path (each being an individual album)
    album_dirs = [d for d in input_base.iterdir() if d.is_dir()]
    album_dirs.sort()

    if not album_dirs:
        print(f"[-] No album directories found in '{input_base.resolve()}'.")
        return

    print(f"[*] Found {len(album_dirs)} album directories.")
    print(f"[*] Base output path: {output_base.resolve()}")

    for album_dir in album_dirs:
        # Define output directory for this specific album
        album_output = output_base / album_dir.name
        
        print(f"\n" + "=" * 60)
        print(f"[>>>] Processing: {album_dir.name}")
        print("=" * 60)

        try:
            # 1. Create formatter for this album
            # MusicFormatter creates the output dir or raises FileExistsError
            formatter = MusicFormatter(output_dir=str(album_output), bitrate=args.bitrate)
            
            # 2. Scan files in this album folder
            files_to_process = formatter.scanner.scan(album_dir)
            
            if not files_to_process:
                print(f"[-] No valid music files found in '{album_dir.name}'. Skipping.")
                continue
            
            print(f"[*] Items to process: {len(files_to_process)}")
            
            # 3. Process each file
            for f in files_to_process:
                padding = formatter.padding_manager.get_padding_for_dir(f.parent)
                # base_path is album_dir to preserve internal structure (e.g. Disc 1)
                formatter.process_file(f, base_path=album_dir, track_padding=padding)

            # 4. Finalize (renaming folders within the album output if applicable)
            formatter.finalize_library()
            print(f"\n[SUCCESS] Completed: {album_dir.name}")

        except FileExistsError:
            print(f"[!] Warning: Output folder '{album_output.name}' already exists. Skipping.")
        except Exception as e:
            print(f"[!] Error processing '{album_dir.name}': {e}")
            continue

    print(f"\n" + "-" * 60)
    print("[*] Batch processing finished.")

if __name__ == "__main__":
    main()
