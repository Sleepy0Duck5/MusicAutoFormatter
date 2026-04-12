import pytest
import subprocess
from pathlib import Path
from src.processing.audio_utils import AudioConverter

def test_convert_to_mp3_success(mocker):
    # Mock dependencies
    mock_run = mocker.patch("subprocess.run")
    mocker.patch("src.processing.audio_utils.Path.exists", side_effect=lambda: True)
    mock_stat = mocker.patch("src.processing.audio_utils.Path.stat")
    mock_stat.return_value.st_size = 1000
    
    mocker.patch("src.processing.audio_utils.Path.rename")
    mocker.patch("src.processing.audio_utils.Path.unlink")
    
    # Mock verify_duration to always return True
    mocker.patch.object(AudioConverter, "verify_duration", return_value=True)
    
    converter = AudioConverter(bitrate="192k")
    success = converter.convert_to_mp3(Path("in.flac"), Path("out.mp3"))
    
    assert success is True
    # Check if cmd had correct bitrate
    cmd = mock_run.call_args[0][0]
    assert "192k" in cmd

def test_convert_to_mp3_ffmpeg_fail(mocker):
    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg", stderr="Error msg"))
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.unlink")
    
    converter = AudioConverter()
    success = converter.convert_to_mp3(Path("in.flac"), Path("out.mp3"))
    
    assert success is False

def test_verify_duration(mocker):
    # Mock FLAC and MP3
    mock_flac = mocker.patch("src.processing.audio_utils.FLAC")
    mock_flac.return_value.info.length = 100.5
    
    mock_mp3 = mocker.patch("src.processing.audio_utils.MP3")
    mock_mp3.return_value.info.length = 100.4
    
    converter = AudioConverter()
    assert converter.verify_duration(Path("s.flac"), Path("t.mp3"), threshold=0.5) is True
    
    mock_mp3.return_value.info.length = 99.0
    assert converter.verify_duration(Path("s.flac"), Path("t.mp3"), threshold=0.5) is False
