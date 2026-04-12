import pytest
from pathlib import Path
from src.processing.file_utils import FileMirror

def test_mirror_file_basic(mocker):
    # Mock dependencies
    mock_copy = mocker.patch("shutil.copy2")
    mocker.patch("src.processing.file_utils.Path.mkdir")
    
    output_base = Path("C:/output")
    mirror = FileMirror(output_base)
    
    source_file = Path("C:/input/song.mp3")
    success = mirror.mirror_file(source_file)
    
    assert success is True
    mock_copy.assert_called_once_with(source_file, output_base / "song.mp3")

def test_mirror_file_with_target_dir(mocker):
    mock_copy = mocker.patch("shutil.copy2")
    mocker.patch("src.processing.file_utils.Path.mkdir")
    
    output_base = Path("C:/output")
    mirror = FileMirror(output_base)
    
    source_file = Path("C:/input/song.mp3")
    target_dir = Path("D:/another_output")
    success = mirror.mirror_file(source_file, target_dir=target_dir)
    
    assert success is True
    mock_copy.assert_called_once_with(source_file, target_dir / "song.mp3")

def test_mirror_file_m3u_backup(mocker):
    mock_copy = mocker.patch("shutil.copy2")
    mocker.patch("src.processing.file_utils.Path.mkdir")
    
    output_base = Path("C:/output")
    mirror = FileMirror(output_base, backup_m3u=True)
    
    source_file = Path("C:/input/playlist.m3u")
    success = mirror.mirror_file(source_file)
    
    assert success is True
    # Should be playlist.m3u.bak
    mock_copy.assert_called_once_with(source_file, output_base / "playlist.m3u.bak")

def test_mirror_file_failure(mocker):
    mocker.patch("shutil.copy2", side_effect=Exception("Disk full"))
    mocker.patch("pathlib.Path.mkdir")
    
    output_base = Path("C:/output")
    mirror = FileMirror(output_base)
    
    source_file = Path("C:/input/song.mp3")
    success = mirror.mirror_file(source_file)
    
    assert success is False
