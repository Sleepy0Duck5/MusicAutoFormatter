import pytest
from pathlib import Path
from src.core.formatter import MusicFormatter

@pytest.fixture
def mock_formatter_deps(mocker):
    # Mocking all dependencies of MusicFormatter to isolate it
    mocker.patch("src.core.formatter.Path.mkdir")
    mocker.patch("src.core.formatter.Path.exists", return_value=False)
    mocker.patch("src.core.formatter.AudioConverter")
    mocker.patch("src.core.formatter.ImageProcessor")
    mocker.patch("src.core.formatter.LastFmClient")
    mocker.patch("src.core.formatter.FileMirror")
    mocker.patch("src.core.formatter.MetadataManager")
    mocker.patch("src.core.formatter.LibraryScanner")
    mocker.patch("src.core.formatter.LibraryManager")
    mocker.patch("src.core.formatter.TrackPaddingManager")

def test_music_formatter_init(mock_formatter_deps):
    formatter = MusicFormatter(output_dir="test_out", create_dir=True)
    assert formatter.output_dir == Path("test_out")
    assert formatter.delete_source is True

def test_music_formatter_output_exists(mocker):
    mocker.patch("src.core.formatter.Path.exists", return_value=True)
    with pytest.raises(FileExistsError):
        MusicFormatter(output_dir="existing_dir", create_dir=True)

def test_find_base_file(mock_formatter_deps, mocker):
    # Mock config
    mock_config = mocker.patch("src.core.formatter.config")
    mock_config.metadata_sync_dir_name = "metadata sync"
    
    formatter = MusicFormatter(output_dir="test_out", create_dir=False)
    
    files = [
        Path("album/song1.mp3"),
        Path("album/metadata sync/reference.flac"), # This is the base file
        Path("album/cover.jpg")
    ]
    
    base_file = formatter._find_base_file(files)
    assert base_file == Path("album/metadata sync/reference.flac")

def test_delete_source_files(mock_formatter_deps, mocker):
    # Mock Path methods in core.formatter
    mock_path_exists = mocker.patch("src.core.formatter.Path.exists", return_value=True)
    mock_path_unlink = mocker.patch("src.core.formatter.Path.unlink")
    
    formatter = MusicFormatter(output_dir="test_out", create_dir=False)
    files = [Path("f1.mp3"), Path("f2.mp3")]
    
    formatter.delete_source_files(files)
    
    assert mock_path_unlink.call_count == 2

def test_cleanup_source_dir(mock_formatter_deps, mocker):
    mock_dir = mocker.Mock(spec=Path)
    mock_dir.is_dir.return_value = True
    mock_dir.iterdir.return_value = [] # Empty dir
    
    formatter = MusicFormatter(output_dir="test_out", create_dir=False)
    formatter._cleanup_source_dir(mock_dir)
    
    mock_dir.rmdir.assert_called_once()
