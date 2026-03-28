import argparse
import sys
from pathlib import Path
from loguru import logger
from src.formatter import MusicFormatter
from src.logger_config import setup_logger
from src.constants import DEFAULT_BITRATE

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
    
    # Setup logger in the base output directory
    setup_logger(output_base)
    
    if not input_base.is_dir():
        logger.error(f"Input path '{input_base}' is not a directory.")
        sys.exit(1)

    # Gather all subdirectories in the input path (each being an individual album)
    album_dirs = [d for d in input_base.iterdir() if d.is_dir()]
    album_dirs.sort()

    if not album_dirs:
        logger.warning(f"No album directories found in '{input_base.resolve()}'.")
        return

    logger.info(f"Found {len(album_dirs)} album directories.")
    logger.debug(f"Base output path: {output_base.resolve()}")

    for album_dir in album_dirs:
        # Define output directory for this specific album
        album_output = output_base / album_dir.name
        
        logger.info(f"Starting process for album: {album_dir.name}")

        try:
            # 1. Create formatter for this album
            formatter = MusicFormatter(output_dir=str(album_output), bitrate=args.bitrate, delete_source=args.delete_source, backup_m3u=args.backup_m3u)
            
            # 2. Scan files in this album folder
            files_to_process = formatter.scanner.scan(album_dir)
            
            if not files_to_process:
                logger.warning(f"No valid music files found in '{album_dir.name}'. Skipping.")
                continue
            
            logger.info(f"Items to process in album: {len(files_to_process)}")
            
            # 3. Process each file
            for f in files_to_process:
                padding = formatter.padding_manager.get_padding_for_dir(f.parent)
                formatter.process_file(f, base_path=album_dir, track_padding=padding)

            # 4. Finalize
            formatter.finalize_library(album_dir)
            logger.success(f"Successfully completed album: {album_dir.name}")

        except FileExistsError:
            logger.warning(f"Output folder '{album_output.name}' already exists. Skipping.")
        except Exception as e:
            logger.exception(f"Error processing '{album_dir.name}': {e}")
            continue

    logger.info("Batch processing finished.")

if __name__ == "__main__":
    main()
