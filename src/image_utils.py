from io import BytesIO
from PIL import Image

class ImageProcessor:
    """
    Handles image optimization and resizing for album covers.
    """
    def __init__(self, target_size: tuple = (800, 800), max_filesize: int = 2 * 1024 * 1024):
        self.target_size = target_size
        self.max_filesize = max_filesize

    def process_cover(self, data: bytes) -> (bytes, str):
        """
        Processes image data. Resizes and optimizes if the file size exceeds max_filesize.
        Returns (processed_data, mime_type).
        """
        # Return as is if small enough
        if len(data) <= self.max_filesize:
            return data, "image/jpeg" # Default to JPEG for safety, or keep original if known
            
        try:
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
            return out_buf.getvalue(), mime
            
        except Exception as e:
            print(f"    [!] Warning: Image processing failed: {e}. Using original.")
            return data, "image/jpeg"
