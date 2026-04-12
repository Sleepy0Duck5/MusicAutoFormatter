import os
from dotenv import load_dotenv
from src.core.constants import METADATA_SYNC_DIR_NAME

class AppConfig:
    """
    Handles dynamic application settings loaded from environment variables (.env).
    """
    _instance = None

    def __init__(self):
        load_dotenv()
        self.lastfm_api_key = os.getenv("LASTFM_API_KEY")
        self.metadata_sync_dir_name = os.getenv("METADATA_SYNC_DIR_NAME", METADATA_SYNC_DIR_NAME)

    @classmethod
    def get_instance(cls) -> "AppConfig":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

# Global config instance for easy access
config = AppConfig.get_instance()
