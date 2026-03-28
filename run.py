import argparse
from pathlib import Path
from src.formatter import MusicFormatter

def main():
    parser = argparse.ArgumentParser(description="Music Auto Formatter & Tagger")
    parser.add_argument("input", nargs="?", default=".", help="Input directory (default: current)")
    parser.add_argument("-o", "--output", default="output", help="Output directory (default: output)")
    parser.add_argument("-b", "--bitrate", default="320k", help="Target bitrate (default: 320k)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_base = Path(args.output)
    
    # If input is a directory, treat it as a single-item batch and put it into 
    # a subdirectory of output, allowing LibraryManager to rename it later.
    if input_path.is_dir():
        final_output = output_base / input_path.name
    else:
        final_output = output_base

    try:
        # Create the formatter orchestrator
        formatter = MusicFormatter(output_dir=str(final_output), bitrate=args.bitrate)
    except FileExistsError as e:
        print(f"[!] {e}")
        return
    # Scan files using the scanner within the orchestrator
    files_to_process = formatter.scanner.scan(input_path)
    
    if not files_to_process:
        print(f"[-] No files found at '{input_path.resolve()}' to process.")
        return

    print(f"[*] Found {len(files_to_process)} entries. Starting batch process...")
    for f in files_to_process:
        base_dir = input_path if input_path.is_dir() else None
        
        # Calculate padding using the padding manager within the orchestrator
        padding = formatter.padding_manager.get_padding_for_dir(f.parent)
        
        # Process the entry
        formatter.process_file(f, base_path=base_dir, track_padding=padding)

    # 4. Cleanup and Structuring
    formatter.finalize_library()

if __name__ == "__main__":
    main()
