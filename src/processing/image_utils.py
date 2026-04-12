from io import BytesIO
from PIL import Image
from loguru import logger
from src.core.constants import DEFAULT_MAX_ART_SIZE, DEFAULT_TARGET_IMAGE_SIZE

class ImageProcessor:
    """
    Handles image optimization and resizing for album covers.
    """
    def __init__(self, target_size: tuple = DEFAULT_TARGET_IMAGE_SIZE, max_filesize: int = DEFAULT_MAX_ART_SIZE):
        self.target_size = target_size
        self.max_filesize = max_filesize

    def process_cover(self, data: bytes) -> (bytes, str):
        """
        Processes image data. Standardizes everything to JPEG/PNG for player compatibility.
        Resizes and optimizes if the file size exceeds max_filesize.
        """
        try:
            img = Image.open(BytesIO(data))
            
            original_format = img.format
            
            # 1. Check if we need optimization (either format mismatch or size limit)
            # WebP, JFIF, or over-sized files should be re-saved.
            needs_resave = (original_format not in ("JPEG", "PNG")) or (len(data) > self.max_filesize)
            
            if not needs_resave:
                logger.debug(f"Cover art ({len(data)} bytes) is within limits and compatible.")
                target_mime = "image/png" if original_format == "PNG" else "image/jpeg"
                return data, target_mime

            # 2. Determine target format and MIME
            # If it's a PNG or has transparency, keep it as PNG.
            if img.mode in ("RGBA", "P", "LA") or original_format == "PNG":
                target_format = "PNG"
                target_mime = "image/png"
                img = img.convert("RGBA")
            else:
                target_format = "JPEG"
                target_mime = "image/jpeg"
                img = img.convert("RGB")
                
            # 3. Optimize and resize
            logger.info(f"Processing cover art ({len(data)} bytes)... Target: {target_format}")
            img.thumbnail(self.target_size, Image.Resampling.LANCZOS)
            
            out_buf = BytesIO()
            img.save(out_buf, format=target_format, optimize=True)
            processed_data = out_buf.getvalue()
            
            logger.info(f"Optimization complete. New size: {len(processed_data)} bytes.")
            return processed_data, target_mime
            
        except Exception as e:
            logger.warning(f"Image processing failed: {e}. Falling back to default.")
            return data, "image/jpeg"
