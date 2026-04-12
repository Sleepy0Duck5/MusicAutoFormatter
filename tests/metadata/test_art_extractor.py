import pytest
from pathlib import Path
from src.metadata.art_extractor import EmbeddedArtExtractor

def test_extract_flac(mocker):
    # Mock FLAC
    mock_flac = mocker.patch("src.metadata.art_extractor.FLAC")
    mock_instance = mock_flac.return_value
    
    mock_pic = mocker.Mock()
    mock_pic.data = b"image_data"
    mock_pic.mime = "image/flac"
    mock_instance.pictures = [mock_pic]
    
    data, mime = EmbeddedArtExtractor.extract(Path("song.flac"))
    assert data == b"image_data"
    assert mime == "image/flac"

def test_extract_mp3(mocker):
    # Mock ID3
    mock_id3 = mocker.patch("src.metadata.art_extractor.ID3")
    mock_instance = mock_id3.return_value
    
    mock_apic = mocker.Mock()
    mock_apic.data = b"mp3_art"
    mock_apic.mime = "image/jpeg"
    
    # Simulate dictionary-like behavior for tags
    mock_instance.__iter__.return_value = ["APIC:cover"]
    mock_instance.__getitem__.return_value = mock_apic
    
    data, mime = EmbeddedArtExtractor.extract(Path("song.mp3"))
    assert data == b"mp3_art"
    assert mime == "image/jpeg"

def test_extract_none():
    data, mime = EmbeddedArtExtractor.extract(Path("unknown.txt"))
    assert data is None
    assert mime == "image/jpeg"
