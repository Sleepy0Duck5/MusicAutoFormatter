import pytest
from pathlib import Path
from src.core.logger_config import setup_logger

def test_setup_logger(mocker):
    # Mock loguru.logger
    mock_remove = mocker.patch("loguru.logger.remove")
    mock_add = mocker.patch("loguru.logger.add")
    mock_info = mocker.patch("loguru.logger.info")
    
    # Mock Path methods in logger_config
    mocker.patch("src.core.logger_config.Path.mkdir")
    mocker.patch("src.core.logger_config.Path.resolve", return_value=Path("C:/output"))
    
    output_dir = Path("C:/output")
    setup_logger(output_dir)
    
    # Assert logger was cleared
    mock_remove.assert_called_once()
    
    # Assert logger.add was called for console and file (at least 2 calls)
    assert mock_add.call_count >= 2
    
    # Check if first call was to sys.stderr (console)
    # The first argument of the first call
    import sys
    assert mock_add.call_args_list[0][0][0] == sys.stderr
    
    # Check if second call was to a log file path
    log_file_arg = mock_add.call_args_list[1][0][0]
    assert isinstance(log_file_arg, Path)
    assert "music_auto_formatter_" in log_file_arg.name
    assert log_file_arg.suffix == ".log"
    
    # Assert successful log message
    mock_info.assert_called()
