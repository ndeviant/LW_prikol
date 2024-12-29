"""Image processing utilities"""

import cv2
import numpy as np
import time
from typing import Optional, Tuple
from .logging import app_logger
from .device import take_screenshot
from .config import CONFIG
import os

def find_template(
    device_id: str,
    template_path: str,
    threshold: float = None
) -> Optional[Tuple[int, int]]:
    """Find template in image and return center coordinates"""
    try:
        # Take screenshot first
        if not take_screenshot(device_id):
            app_logger.error("Failed to take screenshot")
            return None
            
        # Read images
        img = cv2.imread('tmp/screen.png')
        template = cv2.imread(template_path)
        
        if img is None or template is None:
            app_logger.error("Failed to load images")
            return None
            
        # Match template
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Check confidence threshold
        if threshold is None:
            threshold = CONFIG['match_threshold']
            
        if max_val < threshold:
            return None
            
        # Get template dimensions
        h, w = template.shape[:2]
        
        # Calculate center point
        center_x = max_loc[0] + w//2
        center_y = max_loc[1] + h//2
        
        return (center_x, center_y)
        
    except Exception as e:
        app_logger.error(f"Error finding template: {e}")
        return None
    
def find_all_templates(
    device_id: str,
    template_path: str,
    threshold: float = None,
    search_region: Tuple[int, int, int, int] = None
) -> list[Tuple[int, int]]:
    """Find all template matches in image and return center coordinates"""
    try:
        template = cv2.imread(template_path)
        if template is None:
            return []
            
        h, w = template.shape[:2]
        
        if not take_screenshot(device_id):
            return []
            
        img = cv2.imread('tmp/screen.png')
        if img is None:
            return []
            
        # Draw search region on debug image
        debug_img = img.copy()
        if search_region:
            x1, y1, x2, y2 = search_region
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            img_region = img[y1:y2, x1:x2]
        else:
            img_region = img
            
        result = cv2.matchTemplate(img_region, template, cv2.TM_CCOEFF_NORMED)
        
        if threshold is None:
            threshold = CONFIG['match_threshold']
            
        matches = []
        result_copy = result.copy()
        
        while True:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_copy)
            if max_val < threshold:
                break
                
            # Store match with confidence
            center_x = max_loc[0] + w//2
            center_y = max_loc[1] + h//2
            matches.append((center_x, center_y, max_val))
            
            # Suppress region
            x1_sup = max(0, max_loc[0] - w//2)
            y1_sup = max(0, max_loc[1] - h//2)
            x2_sup = min(result_copy.shape[1], max_loc[0] + w//2)
            y2_sup = min(result_copy.shape[0], max_loc[1] + h//2)
            result_copy[y1_sup:y2_sup, x1_sup:x2_sup] = 0
        
        # Adjust coordinates and draw matches
        template_name = os.path.basename(template_path)
        adjusted_matches = []
        
        for x, y, conf in matches:
            if search_region:
                x += search_region[0]
                y += search_region[1]
            adjusted_matches.append((x, y))
            
            # Draw match rectangle and confidence
            rect_x = x - w//2
            rect_y = y - h//2
            cv2.rectangle(debug_img, (rect_x, rect_y), (rect_x + w, rect_y + h), (0, 255, 0), 2)
            cv2.putText(debug_img, f"{conf:.3f}", (rect_x, rect_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Save debug image
        cv2.imwrite(f'tmp/debug_template_{template_name}.png', debug_img)
        
        app_logger.debug(f"Found {len(matches)} matches for {template_name} with threshold {threshold}")
        return adjusted_matches
        
    except Exception as e:
        app_logger.error(f"Error finding templates: {e}")
        return []
    
def wait_for_image(
    device_id: str,
    template_path: str,
    timeout: float = 120.0,
    threshold: float = None,
    interval: float = 1.0
) -> Optional[Tuple[int, int]]:
    """Wait for template to appear in screenshot"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        coords = find_template(device_id, template_path, threshold)
        if coords:
            return coords
        time.sleep(interval)
    return None
