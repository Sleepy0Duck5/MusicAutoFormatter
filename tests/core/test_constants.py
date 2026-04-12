from src.core import constants

def test_constants_presence():
    assert constants.DEFAULT_BITRATE == "320k"
    assert ".mp3" in constants.MUSIC_EXTENSIONS
    assert constants.DEFAULT_TARGET_IMAGE_SIZE == (800, 800)
    assert constants.LASTFM_API_ENDPOINT.startswith("https://")
