import pytest
from pathlib import Path
from src.library.scanner_utils import LibraryScanner

def test_scan_single_file(mocker):
    mock_file = mocker.Mock(spec=Path)
    mock_file.is_file.return_value = True
    
    scanner = LibraryScanner()
    result = scanner.scan(mock_file)
    assert result == [mock_file]

def test_scan_directory(mocker):
    # Setup mock file structure
    mock_dir = mocker.Mock(spec=Path)
    mock_dir.is_file.return_value = False
    mock_dir.is_dir.return_value = True
    
    f1 = mocker.Mock(spec=Path)
    f1.is_file.return_value = True
    f1.resolve.return_value = "/root/album/song1.mp3"
    
    f2 = mocker.Mock(spec=Path)
    f2.is_file.return_value = True
    f2.resolve.return_value = "/root/album/song2.mp3"
    
    mock_dir.rglob.return_value = [f1, f2]
    
    scanner = LibraryScanner()
    result = scanner.scan(mock_dir)
    assert result == [f1, f2]

def test_scan_with_exclude(mocker):
    mock_dir = mocker.Mock(spec=Path)
    mock_dir.is_file.return_value = False
    mock_dir.is_dir.return_value = True
    
    f_ok = mocker.Mock(spec=Path)
    f_ok.is_file.return_value = True
    f_ok.resolve.return_value = "/root/album/song.mp3"
    
    f_excluded = mocker.Mock(spec=Path)
    f_excluded.is_file.return_value = True
    f_excluded.resolve.return_value = "/root/output/song.mp3"
    
    mock_dir.rglob.return_value = [f_ok, f_excluded]
    
    scanner = LibraryScanner(exclude_dirs=["/root/output"])
    result = scanner.scan(mock_dir)
    assert result == [f_ok]
