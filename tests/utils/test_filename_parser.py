import pytest
from src.utils.filename_parser import FilenameParser

def test_get_common_prefix():
    filenames = ["01. song1.mp3", "01. song2.mp3", "01. song3.mp3"]
    # os.path.commonprefix returns "01. song", but our logic should handle it
    # Actually os.path.commonprefix is character by character
    assert FilenameParser.get_common_prefix(filenames) == "01. song"
    
    # Test digits at the end of prefix
    filenames2 = ["Artist - 01 - Song.mp3", "Artist - 02 - Song.mp3"]
    # common prefix is "Artist - 0"
    # Logic should backtrack to "Artist - "
    assert FilenameParser.get_common_prefix(filenames2) == "Artist - "

def test_parse_track_and_title():
    # Normal cases
    assert FilenameParser.parse_track_and_title("01. Title") == ("01", "Title")
    assert FilenameParser.parse_track_and_title("02 - Title") == ("02", "Title")
    assert FilenameParser.parse_track_and_title("03_Title") == ("03", "Title")
    assert FilenameParser.parse_track_and_title("04 Title") == ("04", "Title")
    
    # No track
    assert FilenameParser.parse_track_and_title("Title Only") == (None, "Title Only")
    
    # Empty title
    assert FilenameParser.parse_track_and_title("05") == ("05", None)

def test_process_filenames():
    filenames = ["prefix_01_song1.mp3", "prefix_02_song2.flac"]
    results = FilenameParser.process_filenames(filenames)
    assert results == [("01", "song1"), ("02", "song2")]

def test_parse_with_template():
    template = "%track% - %title%"
    assert FilenameParser.parse_with_template("01 - My Song.mp3", template) == ("01", "My Song")
    
    template2 = "[%track%] %title%"
    assert FilenameParser.parse_with_template("[12] Another Song.flac", template2) == ("12", "Another Song")

def test_template_to_regex():
    # Private method testing if needed, or just through parse_with_template
    regex = FilenameParser._template_to_regex("%track%%sep%%title%")
    assert "track" in regex
    assert "title" in regex
