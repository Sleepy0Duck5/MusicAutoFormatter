import pytest
from io import BytesIO
from src.processing.image_utils import ImageProcessor

def test_process_cover_no_change(mocker):
    # Create a real 1x1 JPEG
    from PIL import Image as PILImage
    from io import BytesIO
    img = PILImage.new("RGB", (1, 1), color="red")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    data = buf.getvalue()
    
    # We don't even need to mock Image.open if we use real data,
    # but we want to be isolated, so we'll mock it to return what Pillow would.
    # Actually, let's just let it run for real data.
    
    proc = ImageProcessor(max_filesize=1000)
    result_data, mime = proc.process_cover(data)
    
    assert result_data == data
    assert mime == "image/jpeg"

def test_process_cover_optimize(mocker):
    # Mock Image.open in src.processing.image_utils
    mock_img = mocker.Mock()
    mock_img.mode = "RGBA"
    mock_img.format = "WEBP"
    mocker.patch("src.processing.image_utils.Image.open", return_value=mock_img)
    
    # Mock img.convert, img.thumbnail, img.save
    mock_converted = mocker.Mock()
    mock_img.convert.return_value = mock_converted
    
    def mock_save(buf, format, optimize):
        buf.write(b"optimized_data")
        
    mock_converted.save.side_effect = mock_save
    
    proc = ImageProcessor()
    data = b"some_data"
    result_data, mime = proc.process_cover(data)
    
    assert result_data == b"optimized_data"
    assert mime == "image/png"
    assert mock_converted.thumbnail.called

def test_process_cover_failure(mocker):
    mocker.patch("src.processing.image_utils.Image.open", side_effect=Exception("Corrupt image"))
    
    proc = ImageProcessor()
    data = b"corrupt"
    result_data, mime = proc.process_cover(data)
    
    assert result_data == data
    assert mime == "image/jpeg"
