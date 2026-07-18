from paddleocr import PaddleOCR
import re

class PlateReader:
    """Runs high-performance text extraction directly inside RAM matrix pools."""
    def __init__(self):
        # Force PaddleOCR to operate entirely on CPU configurations without GPU memory locks
        self.ocr = PaddleOCR(use_angle_cls=False, lang='en', use_gpu=False, show_log=False)

    def extract_plate(self, image_frame):
        try:
            # Analyze raw frame buffer pixels directly out of volatile memory
            result = self.ocr.ocr(image_frame, cls=False)
            if not result or not result[0]:
                return None

            for line in result[0]:
                text_string = line[1][0] # Grab the actual text string prediction
                
                # Sanitize characters: force uppercase, strip special characters and spaces
                clean_text = re.sub(r'[^A-Z0-9]', '', text_string.upper().strip())
                
                # Filter validation: Ensure the character string fits normal plate layouts (4-9 chars)
                if 4 <= len(clean_text) <= 9:
                    return clean_text
        except Exception as e:
            print(f"❌ PaddleOCR runtime inference exception: {e}")
        return None
