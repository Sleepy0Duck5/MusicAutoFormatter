"""
Central repository for constants used across the MusicAutoFormatter project.
"""

# Audio Configuration
DEFAULT_BITRATE = "320k"
MUSIC_EXTENSIONS = [".flac", ".wav", ".mp3"]

# Image Configuration
DEFAULT_TARGET_IMAGE_SIZE = (800, 800)
DEFAULT_MAX_ART_SIZE = 2 * 1024 * 1024 # 2MB
COVER_SEARCH_NAMES = ["cover", "folder", "front", "album"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]

# Metadata Configuration
DEFAULT_TRACK_PADDING = 2
UNKNOWN_ALBUM = "Unknown Album"

# Logging Configuration
LOG_ROTATION = "10 MB"
LOG_RETENTION = "1 week"
LOG_COMPRESSION = "zip"
LOG_FILENAME_PREFIX = "music_auto_formatter"
LOG_FORMAT_CONSOLE = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
LOG_FORMAT_FILE = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"

# Library Management
# Folders matching this pattern will be handled specially (e.g., skip rename of the folder itself, rename parent instead)
GENERIC_FOLDER_REGEX = r"^(disc|cd|vol|track|volume|part|d|side)\s?(\d+|[a-z])$"
