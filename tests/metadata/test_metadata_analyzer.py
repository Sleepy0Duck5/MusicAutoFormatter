import pytest
from pathlib import Path
from src.metadata.metadata_analyzer import AlbumAnalyzer

def test_get_dominant():
    analyzer = AlbumAnalyzer()
    data = ["Album A", "Album A", "Album B", "  "]
    assert analyzer._get_dominant(data) == "Album A"
    
    assert analyzer._get_dominant([]) is None
    assert analyzer._get_dominant([" ", ""]) is None

def test_analyze_flac(mocker):
    # Mock FLAC
    mock_flac = mocker.patch("src.metadata.metadata_analyzer.FLAC")
    mock_instance = mock_flac.return_value
    mock_instance.get.side_effect = lambda k, default: {
        "album": ["My Album"],
        "artist": ["My Artist"]
    }.get(k, default)
    
    analyzer = AlbumAnalyzer()
    analyzer.analyze([Path("song1.flac"), Path("song2.flac")])
    
    assert analyzer.get_value("TALB") == "My Album"
    assert analyzer.get_value("TPE1") == "My Artist"

def test_analyze_mp3(mocker):
    # Mock ID3
    mock_id3 = mocker.patch("src.metadata.metadata_analyzer.ID3")
    mock_instance = mock_id3.return_value
    
    # Mock TALB, TPE1 responses
    mock_instance.get.side_effect = lambda k, default: {
        "TALB": "Album X",
        "TPE1": "Artist Y"
    }.get(k, default)
    mock_instance.getall.return_value = []
    
    analyzer = AlbumAnalyzer()
    analyzer.analyze([Path("song1.mp3")])
    
    assert analyzer.get_value("TALB") == "Album X"
    assert analyzer.get_value("TPE1") == "Artist Y"

def test_set_value():
    analyzer = AlbumAnalyzer()
    analyzer.set_value("TALB", "New Album")
    assert analyzer.get_value("TALB") == "New Album"
