import pytest
from pathlib import Path
from src.metadata.cover_finder import CoverArtFinder

def test_find_exact_match(tmp_path):
    # Create a real temporary file
    album_dir = tmp_path / "album"
    album_dir.mkdir()
    cover_file = album_dir / "cover.jpg"
    cover_file.write_bytes(b"exact_cover_data")
    
    song_file = album_dir / "song.mp3"
    
    finder = CoverArtFinder()
    data, mime = finder.find(song_file)
    
    assert data == b"exact_cover_data"
    assert mime == "image/jpeg"

def test_find_fuzzy_match(tmp_path):
    album_dir = tmp_path / "album"
    album_dir.mkdir()
    cover_file = album_dir / "front_cover.png"
    cover_file.write_bytes(b"fuzzy_cover_data")
    
    song_file = album_dir / "song.mp3"
    
    finder = CoverArtFinder()
    data, mime = finder.find(song_file)
    
    assert data == b"fuzzy_cover_data"
    assert mime == "image/png"

def test_find_not_found(tmp_path):
    album_dir = tmp_path / "album"
    album_dir.mkdir()
    song_file = album_dir / "song.mp3"
    
    finder = CoverArtFinder()
    data, mime = finder.find(song_file)
    
    assert data is None
