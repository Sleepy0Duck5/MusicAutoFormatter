import pytest
from pathlib import Path
from src.metadata.metadata_processor import MetadataManager

@pytest.fixture
def mock_managers(mocker):
    pm = mocker.Mock()
    ip = mocker.Mock()
    lfc = mocker.Mock()
    return pm, ip, lfc

def test_metadata_manager_init(mock_managers):
    pm, ip, lfc = mock_managers
    mgr = MetadataManager(pm, ip, lfc)
    assert mgr.is_base_sync_mode is False
    assert mgr.analyzer is not None

def test_set_base_sync_mode(mock_managers, mocker):
    pm, ip, lfc = mock_managers
    mgr = MetadataManager(pm, ip, lfc)
    
    # Mock dependencies
    mocker.patch("src.metadata.metadata_processor.EmbeddedArtExtractor.extract", return_value=(b"art", "im/jpeg"))
    mocker.patch("src.metadata.metadata_processor.SyncConfig.load", return_value=mocker.Mock(template=None))
    mocker.patch("src.metadata.metadata_processor.FilenameParser.process_filenames", return_value=[("01", "Song A")])
    
    base_file = Path("album/metadata sync/base.flac")
    target_files = [Path("album/target.mp3")]
    
    mgr.set_base_sync_mode(base_file, target_files)
    
    assert mgr.is_base_sync_mode is True
    assert mgr.base_art_data == b"art"
    assert mgr.file_to_metadata[target_files[0]] == {"track": "01", "title": "Song A"}

def test_get_formatted_filename_base_sync(mock_managers, mocker):
    pm, ip, lfc = mock_managers
    mgr = MetadataManager(pm, ip, lfc)
    mgr.is_base_sync_mode = True
    
    f_path = Path("album/song.mp3")
    mgr.file_to_metadata[f_path] = {"track": "1", "title": "Real Title"}
    
    pm.apply_padding.return_value = "01"
    
    result = mgr.get_formatted_filename(f_path, track_padding=2)
    assert result == "01. Real Title"

def test_get_album_name_flac(mock_managers, mocker):
    pm, ip, lfc = mock_managers
    mgr = MetadataManager(pm, ip, lfc)
    
    mock_flac = mocker.patch("src.metadata.metadata_processor.FLAC")
    mock_instance = mock_flac.return_value
    mock_instance.get.return_value = ["Awesome Album"]
    
    name = mgr.get_album_name(Path("song.flac"))
    assert name == "Awesome Album"
