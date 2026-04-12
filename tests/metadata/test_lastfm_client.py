import pytest
from src.metadata.lastfm_client import LastFmClient

@pytest.fixture
def mock_httpx(mocker):
    mock_client = mocker.Mock()
    mocker.patch("httpx.Client", return_value=mock_client)
    # mock_client.__enter__.return_value = mock_client
    return mock_client

def test_get_album_art_no_key():
    client = LastFmClient(api_key=None)
    data, mime, art, alb = client.get_album_art("Artist", "Album")
    assert data is None

def test_get_album_art_cached():
    client = LastFmClient(api_key="test")
    client.cache[("artist", "album")] = (b"data", "image/png", "Art", "Alb")
    
    data, mime, art, alb = client.get_album_art("Artist", "Album")
    assert data == b"data"
    assert mime == "image/png"

def test_fetch_album_info_success(mocker):
    # Use MagicMock for context manager support
    mock_client_instance = mocker.MagicMock()
    mocker.patch("src.metadata.lastfm_client.httpx.Client", return_value=mock_client_instance)
    mock_client_instance.__enter__.return_value = mock_client_instance
    
    # ... rest remains similar but ensured
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "album": {
            "artist": "Official Artist",
            "name": "Official Album",
            "image": [{"size": "large", "#text": "http://example.com/img.jpg"}]
        }
    }
    mock_response.status_code = 200
    
    mock_img_response = mocker.Mock()
    mock_img_response.content = b"image_content"
    mock_img_response.headers = {"Content-Type": "image/jpeg"}
    
    # First call for json, second call for image download
    mock_client_instance.get.side_effect = [mock_response, mock_img_response]
    
    client = LastFmClient(api_key="test")
    data, mime, art, alb = client._fetch_album_info("Artist", "Album")
    
    assert data == b"image_content"
    assert art == "Official Artist"
    assert alb == "Official Album"

def test_search_album_success(mocker):
    mock_client_instance = mocker.MagicMock()
    mocker.patch("src.metadata.lastfm_client.httpx.Client", return_value=mock_client_instance)
    mock_client_instance.__enter__.return_value = mock_client_instance
    
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "results": {
            "albummatches": {
                "album": [{"artist": "Search Artist", "name": "Search Album"}]
            }
        }
    }
    mock_client_instance.get.return_value = mock_response
    
    client = LastFmClient(api_key="test")
    artist, album = client._search_album("Artist", "Album")
    
    assert artist == "Search Artist"
    assert album == "Search Album"
