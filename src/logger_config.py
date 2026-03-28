import sys
from pathlib import Path
from loguru import logger

def setup_logger(output_dir: Path):
    """
    Configures loguru to log to both console and a file in the output directory.
    """
    # Remove default handler
    logger.remove()
    
    # Ensure output directory exists before creating log file
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Add console handler with clean format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO"
    )
    
    # Add file handler
    log_file = output_dir / "formatting.log"
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )
    
    logger.info(f"Logging initialized. Log file: {log_file}")
