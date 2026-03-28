import sys
from datetime import datetime
from pathlib import Path
from loguru import logger

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
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO"
    )
    
    # Add file handler with dynamic timestamped name
    # Format: music_auto_formatter_YYYYMMDD_HHMMSS.log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_base / f"music_auto_formatter_{timestamp}.log"
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )
    
    logger.info(f"Logging initialized. Log file: {log_file}")
