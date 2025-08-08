import cv2
from typing import Tuple
from .logging import app_logger
from .image_processing import _take_and_load_screenshot

def save_debug_region(device_id: str, region: Tuple[int, int, int, int], prefix: str):
    """Helper function to save debug images with region highlighting
    
    Args:
        device_id: Device identifier
        region: Tuple of (x1, y1, x2, y2) coordinates
        prefix: Prefix for saved debug image filenames
    """
    try:
        img = _take_and_load_screenshot()
        if img is None:
            return
            
        x1, y1, x2, y2 = region
        
        # Save cropped region
        region_img = img[y1:y2, x1:x2]
        cv2.imwrite(f'tmp/debug_{prefix}.png', region_img)
        
        # Save full image with region highlighted
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.imwrite(f'tmp/debug_{prefix}_full.png', img)
        
    except Exception as e:
        app_logger.error(f"Error saving debug images: {e}") 