import pytest
from pathlib import Path
from src.metadata.metadata_utils import TrackPaddingManager

def test_apply_padding():
    tpm = TrackPaddingManager(min_padding=2)
    assert tpm.apply_padding("1", 2) == "01"
    assert tpm.apply_padding("10", 2) == "10"
    assert tpm.apply_padding("1/12", 2) == "01"
    assert tpm.apply_padding("invalid", 2) == "invalid"
    assert tpm.apply_padding(None, 2) is None

def test_get_padding_for_dir(mocker):
    # Mock directory contents
    mock_dir = mocker.Mock(spec=Path)
    
    f1 = mocker.Mock(spec=Path)
    f1.is_file.return_value = True
    f1.suffix = ".mp3"
    
    mock_dir.iterdir.return_value = [f1]
    
    # Mock ID3 for f1
    mock_id3 = mocker.patch("src.metadata.metadata_utils.ID3")
    mock_instance = mock_id3.return_value
    mock_instance.get.return_value = "105" # Max track 105 -> padding 3
    
    tpm = TrackPaddingManager(min_padding=2)
    padding = tpm.get_padding_for_dir(mock_dir)
    
    assert padding == 3
    # Check cache
    assert mock_dir in tpm.padding_cache
    assert tpm.get_padding_for_dir(mock_dir) == 3
