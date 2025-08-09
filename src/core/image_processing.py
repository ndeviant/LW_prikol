"""Image processing utilities"""

import cv2
import numpy as np
import time
from typing import Callable, Optional, Tuple
import os
import concurrent.futures 

from .logging import app_logger
from .config import CONFIG

file_save_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

def _load_template(template_name: str) -> Tuple[Optional[np.ndarray], Optional[dict]]:
    """Load template and its config"""
    env = CONFIG["env"]
    template_config = CONFIG.get(f"templates.{template_name}")
        
    if not template_config:
        app_logger.error(f"Template {template_name} not found in config")
        return None, None
    
    template_path = template_config['path'].format(env=env)

    # Look for a file in {env} folder, if missing use {default}
    if not os.path.exists(f"config/{template_path}"):
        env = "default"
        template_path = template_config['path'].format(env=env)
        
    template = cv2.imread(f"config/{template_path}")
    if template is None:
        app_logger.error(f"Failed to load template: config/{template_path}")
        return None, None
        
    return template, template_config

def _take_and_load_screenshot() -> Optional[np.ndarray]:
    from src.game.device import controls
    """Take and load a screenshot"""
    return controls.take_screenshot()

def find_template(
    template_name: str,
    make_new_screen: bool = True,
) -> Optional[Tuple[int, int]]:
    """Find template in image and return center coordinates"""
    from src.game.device import controls

    try:
        app_logger.debug(f"Looking for template: {template_name}")
        
        template, template_config = _load_template(template_name)
        if template is None:
            app_logger.debug(f"Failed to load template: {template_name}")
            return None
            
        app_logger.debug(f"Template loaded successfully. Shape: {template.shape}")
        h, w = template.shape[:2]

        # Take screenshot first
        if make_new_screen:
            img = controls.take_screenshot()
        else:
            img = cv2.imread('tmp/screen.png')

        if img is None:
            app_logger.debug("Failed to load screenshot")
            return None
            
        app_logger.debug(f"Screenshot loaded successfully. Shape: {img.shape}")
        
        # Match template
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Get threshold from template config or use default
        threshold = template_config.get('threshold', CONFIG['match_threshold'])
        app_logger.debug(f"Match values - Max: {max_val:.4f}, Min: {min_val:.4f}, Threshold: {threshold}")
        app_logger.debug(f"Match location - Max: {max_loc}, Min: {min_loc}")

        # Get template dimensions and calculate center point
        center_x = max_loc[0] + w//2
        center_y = max_loc[1] + h//2
        
        # Fix the threshold comparison
        if max_val < threshold:  # Remove the incorrect "threshold - -0.16"
            app_logger.debug(f"Match value {max_val:.4f} below threshold {threshold}")
            _save_debug_image(img, template_name, [(center_x, center_y, max_val, False)], None)
            return None
            
        app_logger.debug(f"Match value {max_val:.4f} EXCEEDS threshold {threshold} !")
        
        _save_debug_image(img, template_name, [(center_x, center_y, max_val, True)], None)
        
        app_logger.debug(f"Found match at center point: ({center_x}, {center_y})")
        return (center_x, center_y)
        
    except Exception as e:
        app_logger.error(f"Error finding template {template_name}: {e}")
        return None
    
def find_all_templates(
    template_name: str,
    search_region: Tuple[int, int, int, int] = None,
    get_file_name = None
) -> list[Tuple[int, int]]:
    """Find all template matches in image and return center coordinates"""
    try:
        template, template_config = _load_template(template_name)
        if template is None:
            return []
            
        h, w = template.shape[:2]
        
        img = _take_and_load_screenshot()
        if img is None:
            return []
            
        # Get region to search
        if search_region:
            x1, y1, x2, y2 = search_region
            img_region = img[y1:y2, x1:x2]
        else:
            img_region = img
            
        result = cv2.matchTemplate(img_region, template, cv2.TM_CCOEFF_NORMED)
        threshold = template_config.get('threshold', CONFIG['match_threshold'])
            
        matches = []
        failed_matches = []
        result_copy = result.copy()
        
        while True:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_copy)
            
            # Store match with confidence
            center_x = max_loc[0] + w//2
            center_y = max_loc[1] + h//2

            if max_val < threshold:
                failed_matches.append((center_x, center_y, max_val, False))
                break
                
            matches.append((center_x, center_y, max_val, True))
            
            # Suppress region
            x1_sup = max(0, max_loc[0] - w//2)
            y1_sup = max(0, max_loc[1] - h//2)
            x2_sup = min(result_copy.shape[1], max_loc[0] + w//2)
            y2_sup = min(result_copy.shape[0], max_loc[1] + h//2)
            result_copy[y1_sup:y2_sup, x1_sup:x2_sup] = 0
        
        # Adjust coordinates if search region was used
        adjusted_matches = []
        for x, y, conf, success in matches:
            if search_region:
                x += search_region[0]
                y += search_region[1]
            adjusted_matches.append((x, y))
            
        # Save debug image
        _save_debug_image(img, template_name, matches or failed_matches, search_region, get_file_name=get_file_name)
        
        app_logger.debug(f"Found {len(matches)} matches for {template_name} with threshold {threshold}")
        return adjusted_matches
        
    except Exception as e:
        app_logger.error(f"Error finding templates: {e}")
        return []
    
def wait_for_image(
    template_name: str | list[str],
    timeout: float = 120.0,
    interval: float = 1.0
) -> Optional[Tuple[int, int]]:
    """Wait for template to appear in screenshot"""
    start_time = time.time()
    template_name_list = template_name if isinstance(template_name, list) else [template_name]
    while time.time() - start_time < timeout:
        coords = None
        for tmp in template_name_list:
            coords = find_template(tmp)
            if coords:
                return coords
        time.sleep(interval)
    return None

def compare_screenshots(img1: np.ndarray, img2: np.ndarray) -> bool:
    """
    Compare two screenshots to detect if they are nearly identical
    Returns True if images are the same, False if different
    """
    if img1 is None or img2 is None:
        return False
        
    if img1.shape != img2.shape:
        return False
        
    # Calculate structural similarity index
    score = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)[0][0]
    
    # Use match_threshold from config for consistency with template matching
    return score >= CONFIG['match_threshold']

def _save_debug_image(
    img: np.ndarray, 
    template_name: str,
    matches: list[Tuple[int, int, float, bool]] = None,
    search_region: Tuple[int, int, int, int] = None,
    padding: int = 20,
    get_file_name: Callable[[str, bool], str] = None,
) -> None:
    """Save debug image with matches and search region highlighted"""
    try:
        debug_img = img.copy()
        success = False
        template, template_config = _load_template(template_name)
        h, w = template.shape[:2]
        template_size = (w, h)

        # Draw search region if provided
        if search_region:
            x1, y1, x2, y2 = search_region
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
        # Draw matches if provided
        if matches and template_size:
            w, h = template_size
            for x, y, conf, match_success in matches:
                if (match_success): success = True
                color = (0, 255, 0) if match_success else (50, 50, 255)

                rect_x = x - w//2
                rect_y = y - h//2
                cv2.rectangle(debug_img, (rect_x - padding, rect_y - padding), 
                            (rect_x + w + padding, rect_y + h + padding), color, 2)
                cv2.putText(debug_img, f"{conf:.3f}", (rect_x, rect_y - padding - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
        # Save debug image
        file_name = f"debug{"" if success else "_fail"}_find_{template_name}"
        if (get_file_name):
            file_name= get_file_name(template_name, success) or file_name
        file_save_executor.submit(lambda: cv2.imwrite(f'tmp/{file_name}.png', debug_img))
        
    except Exception as e:
        app_logger.error(f"Error saving debug image: {e}")

def find_and_tap_template(
    template_name: str,
    make_new_screen: bool = True,
    error_msg: Optional[str] = None,
    success_msg: Optional[str] = None,
    press_duration: float = 0,
    critical: bool = False,
    timeout: float = None,
    interval: float = None,
    offset: tuple[int, int] = (0,0)
) -> bool:
    """Find and tap a template on screen"""
    if timeout:
        location = wait_for_image(template_name, timeout=timeout, interval=interval)
    else:
        location = find_template(template_name, make_new_screen=make_new_screen)
        
    if location is None:
        if error_msg:
            if critical:
                app_logger.error(error_msg)
            else:
                app_logger.info(error_msg)
        return False
        
    if success_msg:
        app_logger.info(success_msg)

    coors = (location[0] + offset[0], location[1] + offset[1])
        
    # Import here to avoid circular dependency
    from src.game.device import controls
        
    if press_duration:
        controls.click(coors[0], coors[1], duration=press_duration)
    else:
        controls.click(coors[0], coors[1])
        
    return True
