import argparse
from pathlib import Path
from loguru import logger
from src.formatter import MusicFormatter
from src.logger_config import setup_logger
from src.constants import DEFAULT_BITRATE

def main():
    parser = argparse.ArgumentParser(description="Music Auto Formatter & Tagger")
    parser.add_argument("input", nargs="?", default=".", help="Input directory (default: current)")
    parser.add_argument("-o", "--output", default="output", help="Output directory (default: output)")
    parser.add_argument("-b", "--bitrate", default=DEFAULT_BITRATE, help=f"Target bitrate (default: {DEFAULT_BITRATE})")
    parser.add_argument("--keep-source", action="store_false", dest="delete_source", default=True, help="Keep source files after successful processing")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_base = Path(args.output)
    
    # Setup logger in the base output directory
    setup_logger(output_base)
    
    # If input is a directory, treat it as a single-item batch and put it into 
    # a subdirectory of output, allowing LibraryManager to rename it later.
    if input_path.is_dir():
        final_output = output_base / input_path.name
    else:
        final_output = output_base

    try:
        # Create the formatter orchestrator
        formatter = MusicFormatter(output_dir=str(final_output), bitrate=args.bitrate, delete_source=args.delete_source)
    except FileExistsError as e:
        logger.error(str(e))
        return
    
    # Scan files using the scanner within the orchestrator
    files_to_process = formatter.scanner.scan(input_path)
    
    if not files_to_process:
        logger.warning(f"No files found at '{input_path.resolve()}' to process.")
        return

    logger.info(f"Found {len(files_to_process)} entries. Starting process...")
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
