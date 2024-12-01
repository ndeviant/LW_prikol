# utils/image_processing.py

import cv2
import numpy as np
import pytesseract
from typing import Optional, Tuple, List
from pathlib import Path
from logging_config import app_logger
from .error_handling import ImageProcessingError, OCRError

def find_on_screen(
    screenshot_path: str,
    template_path: str,
    threshold: float = 0.8,
    region: Optional[Tuple[int, int, int, int]] = None
) -> Optional[Tuple[int, int]]:
    """
    Find a template image within a screenshot.
    
    Args:
        screenshot_path: Path to screenshot image
        template_path: Path to template image
        threshold: Matching threshold (0-1)
        region: Optional region to search (x, y, width, height)
    
    Returns:
        Tuple of (x, y) coordinates of match center, or None if not found
    """
    try:
        # Load images
        screenshot = cv2.imread(screenshot_path)
        template = cv2.imread(template_path)
        
        if screenshot is None or template is None:
            raise ImageProcessingError("Failed to load images")
            
        # Crop screenshot to region if specified
        if region:
            x, y, w, h = region
            screenshot = screenshot[y:y+h, x:x+w]
        
        # Perform template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val < threshold:
            app_logger.debug(f"No match found above threshold {threshold}")
            return None
            
        # Calculate center point of match
        h, w = template.shape[:2]
        center_x = max_loc[0] + w//2
        center_y = max_loc[1] + h//2
        
        # Adjust coordinates if region was specified
        if region:
            center_x += region[0]
            center_y += region[1]
            
        app_logger.debug(f"Found match at ({center_x}, {center_y}) with confidence {max_val:.2f}")
        return center_x, center_y
        
    except Exception as e:
        app_logger.error(f"Error finding template: {e}")
        raise ImageProcessingError(f"Error finding template: {e}")

def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """Preprocess image for better OCR results"""
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Increase contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    contrast = clahe.apply(gray)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(contrast, (3,3), 0)
    
    # Use adaptive thresholding
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    
    # Invert if necessary (white text on black background)
    if cv2.countNonZero(binary) < binary.size / 2:
        binary = cv2.bitwise_not(binary)
    
    # Remove small noise
    kernel = np.ones((2,2), np.uint8)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # Connect nearby text components
    kernel = np.ones((1,3), np.uint8)
    connected = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    
    # Scale up image
    scaled = cv2.resize(connected, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    return scaled

def perform_ocr(
    image_path: str,
    lang: str = 'eng',
    config: str = '--psm 7'
) -> str:
    """
    Perform OCR with multiple attempts and preprocessing methods.
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise OCRError("Failed to load image")
            
        # Get image dimensions
        height, width = image.shape[:2]
        
        # Try different ROI heights to focus on text
        roi_heights = [
            int(height * 0.3),  # Top portion
            int(height * 0.5),  # Middle portion
            height  # Full height
        ]
        
        results = []
        
        for roi_height in roi_heights:
            # Extract ROI
            roi = image[0:roi_height, :]
            
            # Process with different methods
            processed1 = preprocess_for_ocr(roi)
            processed2 = preprocess_for_ocr(cv2.convertScaleAbs(roi, alpha=1.5, beta=0))
            
            # Save debug images
            cv2.imwrite(f"{image_path.replace('.png', f'_h{roi_height}_p1.png')}", processed1)
            cv2.imwrite(f"{image_path.replace('.png', f'_h{roi_height}_p2.png')}", processed2)
            
            # Try different PSM modes
            psm_modes = [7, 6, 3, 8, 13]
            
            for processed in [processed1, processed2]:
                for psm in psm_modes:
                    text = pytesseract.image_to_string(
                        processed,
                        lang=lang,
                        config=f'--psm {psm} --oem 3'
                    ).strip().lower()
                    
                    if text:
                        # Calculate confidence based on letter ratio and length
                        letters = sum(c.isalpha() for c in text)
                        total_chars = len(text)
                        if total_chars > 0:
                            confidence = letters / total_chars
                            # Bonus for longer text (likely more accurate)
                            if len(text) >= 3:
                                confidence *= 1.2
                            results.append((text, confidence, roi_height, psm))
                            app_logger.debug(f"OCR result (h={roi_height}, PSM {psm}): {text} (conf={confidence:.2f})")
        
        # Sort by confidence and return best result
        if results:
            results.sort(key=lambda x: x[1], reverse=True)
            best_text, conf, height, psm = results[0]
            app_logger.debug(f"Best OCR result: {best_text} (conf={conf:.2f}, h={height}, psm={psm})")
            return best_text
            
        return ""
        
    except Exception as e:
        app_logger.error(f"OCR failed: {e}")
        raise OCRError(f"OCR failed: {e}")

def find_all_matches(
    screenshot_path: str,
    template_path: str,
    threshold: float = 0.8,
    min_distance: int = 20
) -> List[Tuple[int, int]]:
    """
    Find all occurrences of a template in a screenshot.
    
    Args:
        screenshot_path: Path to screenshot
        template_path: Path to template
        threshold: Matching threshold
        min_distance: Minimum distance between matches
        
    Returns:
        List of (x, y) coordinates for matches
    """
    try:
        # Load images
        screenshot = cv2.imread(screenshot_path)
        template = cv2.imread(template_path)
        
        if screenshot is None or template is None:
            raise ImageProcessingError("Failed to load images")
            
        # Perform template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        
        # Find all matches above threshold
        locations = np.where(result >= threshold)
        h, w = template.shape[:2]
        matches = []
        
        for pt in zip(*locations[::-1]):
            x = pt[0] + w//2
            y = pt[1] + h//2
            
            # Check if this match is far enough from existing matches
            if not any(
                abs(x - mx) < min_distance and abs(y - my) < min_distance
                for mx, my in matches
            ):
                matches.append((x, y))
                
        app_logger.debug(f"Found {len(matches)} matches")
        return matches
        
    except Exception as e:
        app_logger.error(f"Error finding matches: {e}")
        raise ImageProcessingError(f"Error finding matches: {e}")

def save_debug_image(
    image_path: str,
    matches: List[Tuple[int, int]],
    output_path: Optional[str] = None
):
    """
    Save debug image with matches highlighted.
    
    Args:
        image_path: Path to original image
        matches: List of match coordinates
        output_path: Optional output path
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ImageProcessingError("Failed to load image")
            
        # Draw circles at match locations
        for x, y in matches:
            cv2.circle(image, (x, y), 10, (0, 255, 0), 2)
            
        # Save debug image
        output_path = output_path or f"debug_{Path(image_path).name}"
        cv2.imwrite(output_path, image)
        app_logger.debug(f"Saved debug image to {output_path}")
        
    except Exception as e:
        app_logger.error(f"Error saving debug image: {e}")
        # Don't raise here as this is a debug function
