import argparse
import sys
from pathlib import Path
from loguru import logger
from src.core.formatter import MusicFormatter
from src.core.logger_config import setup_logger
from src.core.constants import DEFAULT_BITRATE

def main():
    parser = argparse.ArgumentParser(description="Batch Music Auto Formatter for Multiple Albums")
    parser.add_argument("input", help="Parent directory containing multiple album folders")
    parser.add_argument("-o", "--output", default="output", help="Base output directory (default: output)")
    parser.add_argument("-b", "--bitrate", default=DEFAULT_BITRATE, help=f"Target bitrate (default: {DEFAULT_BITRATE})")
    parser.add_argument("--keep-source", action="store_false", dest="delete_source", default=True, help="Keep source files after successful processing")
    parser.add_argument("--backup-m3u", action="store_true", default=False, help="Backup .m3u files by renaming to .m3u.bak (default: False)")
    
    args = parser.parse_args()
    
    input_base = Path(args.input)
    output_base = Path(args.output)
    
    logger_setup = False
    
    if not input_base.is_dir():
        print(f"Error: Input path '{input_base}' is not a directory.")
        return

    # Gather all subdirectories in the input path (each being an individual album)
    album_dirs = [d for d in input_base.iterdir() if d.is_dir()]
    album_dirs.sort()

    if not album_dirs:
        print(f"Warning: No album directories found in '{input_base.resolve()}'. Skipping.")
        return

    for album_dir in album_dirs:
        # Define output directory for this specific album
        album_output = output_base / album_dir.name
        
        try:
            # 1. Create formatter for this album WITHOUT creating folder
            formatter = MusicFormatter(
                output_dir=str(album_output), 
                bitrate=args.bitrate, 
                delete_source=args.delete_source, 
                backup_m3u=args.backup_m3u,
                create_dir=False
            )
            
            # 2. Scan files in this album folder
            files_to_process = formatter.scanner.scan(album_dir)
            
            if not files_to_process:
                if not logger_setup:
                    print(f"Skipping empty: {album_dir.name}")
                else:
                    logger.warning(f"No valid music files found in '{album_dir.name}'. Skipping.")
                continue
            
            # 3. Setup logger and output dir if first time having work
            if not logger_setup:
                setup_logger(output_base)
                logger_setup = True
                logger.info(f"Starting batch processing from: {input_base}")
                logger.info(f"Found {len(album_dirs)} directories in total.")

            logger.info(f"Processing album: {album_dir.name} ({len(files_to_process)} items)")
            
            try:
                formatter.create_output_dir()
            except FileExistsError:
                logger.warning(f"Output folder '{album_output.name}' already exists. Skipping.")
                continue

            # 4. Analyze and process
            formatter.prepare_album(files_to_process)
            
            for f in files_to_process:
                padding = formatter.padding_manager.get_padding_for_dir(f.parent)
                formatter.process_file(f, base_path=album_dir, track_padding=padding)

            # 5. Finalize
            formatter.finalize_library(album_dir)
            logger.success(f"Successfully completed album: {album_dir.name}")

        except Exception as e:
            if logger_setup:
                logger.exception(f"Error processing '{album_dir.name}': {e}")
            else:
                print(f"Error processing '{album_dir.name}': {e}")
            continue

    if logger_setup:
        logger.info("Batch processing finished.")
    else:
        print("Batch processing finished (no files were processed).")

if __name__ == "__main__":
    main()
