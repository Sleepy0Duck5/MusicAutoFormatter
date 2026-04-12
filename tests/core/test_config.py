import os
import pytest
from src.core.config import AppConfig

def test_app_config_singleton():
    config1 = AppConfig.get_instance()
    config2 = AppConfig.get_instance()
    assert config1 is config2

def test_app_config_env_vars(mocker):
    # Mock environment variables
    mocker.patch.dict(os.environ, {
        "LASTFM_API_KEY": "test_key",
        "METADATA_SYNC_DIR_NAME": "custom_sync"
    })
    
    # We need to create a new instance to test env var loading
    # since _instance might already be set from module import
    AppConfig._instance = None
    config = AppConfig.get_instance()
    
    assert config.lastfm_api_key == "test_key"
    assert config.metadata_sync_dir_name == "custom_sync"

def test_app_config_default_sync_dir(mocker):
    # Mock environment to remove the var
    if "METADATA_SYNC_DIR_NAME" in os.environ:
        mocker.patch.dict(os.environ, {"METADATA_SYNC_DIR_NAME": ""}, clear=False)
        # Actually it's better to use del
        del os.environ["METADATA_SYNC_DIR_NAME"]
    
    AppConfig._instance = None
    config = AppConfig.get_instance()
    
    from src.core.constants import METADATA_SYNC_DIR_NAME
    assert config.metadata_sync_dir_name == METADATA_SYNC_DIR_NAME
