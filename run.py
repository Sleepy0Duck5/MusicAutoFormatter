import argparse
from pathlib import Path
from loguru import logger
from src.core.formatter import MusicFormatter
from src.core.logger_config import setup_logger
from src.core.constants import DEFAULT_BITRATE

def main():
    parser = argparse.ArgumentParser(description="Music Auto Formatter & Tagger")
    parser.add_argument("input", nargs="?", default=".", help="Input directory (default: current)")
    parser.add_argument("-o", "--output", default="output", help="Output directory (default: output)")
    parser.add_argument("-b", "--bitrate", default=DEFAULT_BITRATE, help=f"Target bitrate (default: {DEFAULT_BITRATE})")
    parser.add_argument("--keep-source", action="store_false", dest="delete_source", default=True, help="Keep source files after successful processing")
    parser.add_argument("--backup-m3u", action="store_true", default=False, help="Backup .m3u files by renaming to .m3u.bak (default: False)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_base = Path(args.output)
    
    # 1. Paths calculation (without creating folders yet)
    if input_path.is_dir():
        final_output = output_base / input_path.name
    else:
        final_output = output_base

    try:
        # 2. Create orchestrator WITHOUT creating folders
        formatter = MusicFormatter(
            output_dir=str(final_output), 
            bitrate=args.bitrate, 
            delete_source=args.delete_source, 
            backup_m3u=args.backup_m3u,
            create_dir=False
        )
    except Exception as e:
        print(f"Error initializing: {e}")
        return
    
    # 3. Scan files
    files_to_process = formatter.scanner.scan(input_path)
    
    if not files_to_process:
        print(f"Warning: No files found at '{input_path.resolve()}'. Skipping.")
        return

    # 4. We have work to do, so create output dir and setup logger
    try:
        formatter.create_output_dir()
    except FileExistsError as e:
        print(f"Error: {e}")
        return

    setup_logger(output_base)
    logger.info(f"Found {len(files_to_process)} entries. Starting process...")
    
    # 5. Analyze and Process
    formatter.prepare_album(files_to_process)
    
    for f in files_to_process:
        base_dir = input_path if input_path.is_dir() else None
        
        # Calculate padding using the padding manager within the orchestrator
        padding = formatter.padding_manager.get_padding_for_dir(f.parent)
        
        # Process the entry
        formatter.process_file(f, base_path=base_dir, track_padding=padding)

    # 4. Cleanup and Structuring
    formatter.finalize_library(input_path)
    logger.success("Formatting completed successfully.")

if __name__ == "__main__":
    main()
