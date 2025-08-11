"""Image processing utilities"""

import cv2
import numpy as np
import time
from typing import Callable, Optional, Tuple
import os
import concurrent.futures

from sympy import Q 

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

def _save_debug_image(
    img: np.ndarray, 
    template_name: str,
    matches: list[Tuple[int, int, float, bool]] = None,
    search_region: Tuple[int, int, int, int] = None,
    padding: int = 20,
    file_name_getter: Callable[[str, bool], str] = None,
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
        if (file_name_getter):
            file_name= file_name_getter(template_name, success) or file_name
        file_save_executor.submit(lambda: cv2.imwrite(f'tmp/{file_name}.png', debug_img))
        
    except Exception as e:
        app_logger.error(f"Error saving debug image: {e}")

def _get_templates_coords(
    template_name: str,
    search_region: Tuple[int, int, int, int] = None,
    file_name_getter = None,
    find_one: bool = False,
) -> list[Tuple[int, int]]:
    """Find all template matches in image and return center coordinates"""
    try:
        app_logger.debug(f"Looking for template: '{template_name}'")
        
        template, template_config = _load_template(template_name)
        if template is None:
            app_logger.debug(f"Failed to load template: '{template_name}'")
            return []
            
        h, w = template.shape[:2]
        
        img = _take_and_load_screenshot()
        if img is None:
            app_logger.debug("Failed to load screenshot")
            return []
            
        app_logger.debug(f"Screenshot loaded successfully. Shape: {img.shape}")

        # Get region to search
        if search_region:
            x1, y1, x2, y2 = search_region
            img_region = img[y1:y2, x1:x2]
        else:
            img_region = img
            
        result = cv2.matchTemplate(img_region, template, cv2.TM_CCOEFF_NORMED)
        threshold = template_config.get('threshold', CONFIG['match_threshold'])
            
        matches = []
        failed_max_val = None
        failed_matches = []
        result_copy = result.copy()
        
        while True:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_copy)
            
            # Store match with confidence
            center_x = max_loc[0] + w//2
            center_y = max_loc[1] + h//2

            app_logger.debug(f"Match values - Max: {max_val:.4f}, Min: {min_val:.4f}, Threshold: {threshold}")
            app_logger.debug(f"Match location - Max: {max_loc}, Min: {min_loc}")

            if max_val < threshold:
                failed_max_val = max_val
                failed_matches.append((center_x, center_y, max_val, False))
                break
                
            app_logger.debug(f"Match value {max_val:.4f} EXCEEDS threshold {threshold} !")
            matches.append((center_x, center_y, max_val, True))

            if (find_one):
                break
            
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

        if failed_matches and not matches:
            app_logger.debug(f"Match value {failed_max_val:.4f} below threshold {threshold}")
            
        # Save debug image
        _save_debug_image(img, template_name, matches or failed_matches, search_region, file_name_getter=file_name_getter)

        app_logger.debug(f"Found {len(matches)} matches for '{template_name}' with threshold {threshold}")
        return adjusted_matches
        
    except Exception as e:
        app_logger.error(f"Error finding templates: {e}")
        return []
    
def _wait_for_image(
    template_name: str | list[str],
    wait: float = 120.0,
    interval: float = 1.0,
    search_region: Tuple[int, int, int, int] = None,
    file_name_getter = None,
    find_one: bool = False,
) -> Optional[list[Tuple[int, int]]]:
    """Wait for template to appear in screenshot"""
    start_time = time.time()
    template_name_list = template_name if isinstance(template_name, list) else [template_name]
    while time.time() - start_time < wait:
        coords_list = []
        for tmp in template_name_list:
            coords_list = _get_templates_coords(tmp, search_region, file_name_getter, find_one)
            if coords_list:
                return coords_list
        time.sleep(interval)
    return []

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

def find_templates(
    template_name: str,
    error_msg: Optional[str] = None,
    success_msg: Optional[str] = None,
    critical: bool = False,
    wait: float = None,
    interval: float = None,
    tap: bool = False,
    tap_duration: float = None,
    tap_offset: Tuple[int, int] = (0, 0),
    search_region: Tuple[int, int, int, int] = None,
    file_name_getter: Callable[[str, bool], str] = None,
    find_one: bool = False,
) -> list[Tuple[int, int]]:
    """Find and tap a template on screen"""
    if wait:
        locations = _wait_for_image(
            template_name, file_name_getter=file_name_getter, find_one=find_one, wait=wait, interval=interval, 
        )
    else:
        locations = _get_templates_coords(
            template_name, file_name_getter=file_name_getter, find_one=find_one, search_region=search_region,
        )
        
    if not locations:
        if error_msg:
            if critical:
                app_logger.error(error_msg)
            else:
                app_logger.info(error_msg)
        return []
        
    if success_msg:
        app_logger.info(success_msg)

    if not tap:
        return locations
    
    # Import here to avoid circular dependency
    from src.game.device import controls

    location = locations[0]
    coors = (location[0] + tap_offset[0], location[1] + tap_offset[1])

    # Create a dictionary for the optional keyword arguments
    click_kwargs = {}

    if tap_duration is not None:
        click_kwargs['duration'] = tap_duration
        
    # Unpack the dictionary into the function call
    controls.click(coors[0], coors[1], **click_kwargs)
        
    return locations

# The new function that runs the first one
def find_template(
    template_name: str,
    error_msg: Optional[str] = None,
    success_msg: Optional[str] = None,
    critical: bool = False,
    wait: float = None,
    interval: float = None,
    tap: bool = False,
    tap_duration: float = None,
    tap_offset: Tuple[int, int] = (0, 0),
    search_region: Tuple[int, int, int, int] = None,
    file_name_getter: Callable[[str, bool], str] = None,
) -> list[Tuple[int, int]]:
    """A wrapper function that calls find_templates with all its arguments."""

    # This single line calls the first function with all the arguments it received.
    locations = find_templates(
        template_name=template_name,
        error_msg=error_msg,
        success_msg=success_msg,
        critical=critical,
        wait=wait,
        interval=interval,
        tap=tap,
        tap_duration=tap_duration,
        tap_offset=tap_offset,
        search_region=search_region,
        file_name_getter=file_name_getter,
        find_one=True
    )
    
    return locations[0] if locations else None