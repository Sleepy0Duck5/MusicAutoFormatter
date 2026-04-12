import pytest
from pathlib import Path
from src.library.library_manager import LibraryManager

def test_library_manager_finalize_structure(tmp_path, mocker):
    # Setup real directory structure
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    album_dir = output_dir / "Unknown Folder"
    album_dir.mkdir()
    
    # Create some "mp3" files
    (album_dir / "song1.mp3").write_text("fake data")
    (album_dir / "song2.mp3").write_text("fake data")
    
    mock_metadata = mocker.Mock()
    mock_metadata.get_album_name.return_value = "Real Album Name"
    
    manager = LibraryManager(output_dir, mock_metadata)
    manager.finalize_structure()
    
    # Check if the folder was renamed
    assert (output_dir / "Real Album Name").exists()
    assert not album_dir.exists()

def test_generic_folder_match():
    # Test internal regex
    manager = LibraryManager(Path("out"), None)
    assert manager.GENERIC_FOLDER_RE.match("Disc 1")
    assert manager.GENERIC_FOLDER_RE.match("CD 2")
    assert manager.GENERIC_FOLDER_RE.match("vol 1")
    assert manager.GENERIC_FOLDER_RE.match("disc a")
    assert not manager.GENERIC_FOLDER_RE.match("My Awesome Album")
