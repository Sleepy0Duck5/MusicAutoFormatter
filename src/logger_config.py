import sys
from datetime import datetime
from pathlib import Path
from loguru import logger
from .constants import (
    LOG_COMPRESSION,
    LOG_FILENAME_PREFIX,
    LOG_FORMAT_CONSOLE,
    LOG_FORMAT_FILE,
    LOG_RETENTION,
    LOG_ROTATION,
)

def setup_logger(output_dir: Path):
    """
    Configures loguru to log to both console and a file in the output directory.
    Using a dynamic timestamp for the filename.
    """
    # Remove default handler
    logger.remove()
    
    # Ensure output directory exists before creating log file
    output_base = output_dir.resolve()
    output_base.mkdir(parents=True, exist_ok=True)
    
    # Add console handler with clean format
    logger.add(
        sys.stderr,
        format=LOG_FORMAT_CONSOLE,
        level="INFO"
    )
    
    # Add file handler with dynamic timestamped name
    # Format: music_auto_formatter_YYYYMMDD_HHMMSS.log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_base / f"{LOG_FILENAME_PREFIX}_{timestamp}.log"
    
    logger.add(
        log_file,
        format=LOG_FORMAT_FILE,
        level="DEBUG",
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression=LOG_COMPRESSION
    )
    
    logger.info(f"Logging initialized. Log file: {log_file}")
