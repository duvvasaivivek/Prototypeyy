import easyocr
import base64
import cv2
import numpy as np
from typing import List
from models.schemas import ElementInfo

class OCREngine:
    def __init__(self):
        # Initialize reader (will download weights on first run)
        # Using en for english. GPU=True to leverage hardware acceleration if available.
        self.reader = easyocr.Reader(['en'], gpu=True)
        print("[OCR] EasyOCR Engine Initialized (GPU Enabled)")

    def extract_elements_from_base64(self, base64_img: str) -> List[ElementInfo]:
        """
        Takes a base64 image string, performs OCR, and returns a list of virtual ElementInfo objects.
        """
        if not base64_img:
            return []
            
        # Strip header if present
        if "," in base64_img:
            base64_img = base64_img.split(",")[1]
            
        try:
            # Decode base64 to OpenCV image
            img_bytes = base64.b64decode(base64_img)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                print("[OCR] Failed to decode image")
                return []
                
            # Perform OCR
            results = self.reader.readtext(img)
            
            ocr_elements = []
            for i, (bbox, text, prob) in enumerate(results):
                # Bbox from easyocr is a list of 4 points: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                # Convert to [x, y, width, height]
                x = int(bbox[0][0])
                y = int(bbox[0][1])
                w = int(bbox[1][0] - bbox[0][0])
                h = int(bbox[2][1] - bbox[1][1])
                
                # We only want relatively confident text to avoid junk
                if prob > 0.4:
                    ocr_el = ElementInfo(
                        id=f"ocr_text_{i}",
                        tag="ocr_text",
                        text=text,
                        bbox=[x, y, w, h]
                    )
                    ocr_elements.append(ocr_el)
                    
            print(f"[OCR] Extracted {len(ocr_elements)} text regions from image.")
            return ocr_elements
            
        except Exception as e:
            print(f"[OCR] Error processing image: {e}")
            return []

ocr_engine = OCREngine()
