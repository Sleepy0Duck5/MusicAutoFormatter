import json
import pytest
from pathlib import Path
from src.metadata.sync_config import SyncConfig

def test_sync_config_load_no_file(mocker):
    mocker.patch("pathlib.Path.exists", return_value=False)
    config = SyncConfig.load(Path("some_dir"))
    assert config.template is None

def test_sync_config_load_success(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    
    mock_data = {
        "input": {"file_name": "%track% - %title%"},
        "output": {"fallback_title": "Track %track%"}
    }
    
    # Mock open and json.load
    mocker.patch("builtins.open", mocker.mock_open(read_data=json.dumps(mock_data)))
    
    config = SyncConfig.load(Path("some_dir"))
    assert config.template == "%track% - %title%"
    assert config.fallback_template == "Track %track%"

def test_apply_fallback():
    config = SyncConfig(fallback_template="Song %track%")
    # If title exists, use it
    assert config.apply_fallback("01", "My Title") == "My Title"
    # If title missing, use fallback
    assert config.apply_fallback("02", None) == "Song 02"
    # If both missing, return None
    config2 = SyncConfig()
    assert config2.apply_fallback("03", None) is None
