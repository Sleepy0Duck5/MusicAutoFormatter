from io import BytesIO
from PIL import Image
from loguru import logger
from .constants import DEFAULT_MAX_ART_SIZE, DEFAULT_TARGET_IMAGE_SIZE

class ImageProcessor:
    """
    Handles image optimization and resizing for album covers.
    """
    def __init__(self, target_size: tuple = DEFAULT_TARGET_IMAGE_SIZE, max_filesize: int = DEFAULT_MAX_ART_SIZE):
        self.target_size = target_size
        self.max_filesize = max_filesize

    def process_cover(self, data: bytes) -> (bytes, str):
        """
        Processes image data. Resizes and optimizes if the file size exceeds max_filesize.
        Returns (processed_data, mime_type).
        """
        # Return as is if small enough
        if len(data) <= self.max_filesize:
            logger.debug(f"Cover art size ({len(data)} bytes) within limits. Skipping optimization.")
            return data, "image/jpeg" 
            
        try:
            logger.info(f"Cover art ({len(data)} bytes) exceeds limit. Optimizing and resizing to {self.target_size}...")
            img = Image.open(BytesIO(data))
            
            # Ensure proper mode for PNG (RGBA) or JPEG (RGB)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
                fmt = "PNG"
                mime = "image/png"
            else:
                img = img.convert("RGB")
                fmt = "JPEG"
                mime = "image/jpeg"
                
            # Resize
            img.thumbnail(self.target_size, Image.Resampling.LANCZOS)
            
            # Save to buffer
            out_buf = BytesIO()
            img.save(out_buf, format=fmt, optimize=True)
            processed_data = out_buf.getvalue()
            logger.info(f"Optimization complete. New size: {len(processed_data)} bytes.")
            return processed_data, mime
            
        except Exception as e:
            logger.warning(f"Image processing failed: {e}. Using original.")
            return data, "image/jpeg"
