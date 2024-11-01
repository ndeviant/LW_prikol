# utils/image_processing.py

import cv2
import logging
import numpy as np

logger = logging.getLogger(__name__)

def find_icon_on_screen(screenshot_path, icon_path, threshold=0.8, scale_range=(0.7, 1.3), debug=False):
    """
    Finds the position of a specific icon in a screenshot using multi-scale template matching.
    """
    try:
        # Load images
        screenshot = cv2.imread(screenshot_path)
        icon = cv2.imread(icon_path)

        if screenshot is None:
            logger.error(f"Screenshot image not found at {screenshot_path}.")
            return None
        if icon is None:
            logger.error(f"Icon image not found at {icon_path}.")
            return None

        icon_height, icon_width = icon.shape[:2]
        all_matches = []
        num_scales = 20
        scales = np.linspace(scale_range[0], scale_range[1], num_scales)

        for scale in scales:
            # Resize the icon template
            resized_icon = cv2.resize(
                icon,
                (int(icon_width * scale), int(icon_height * scale))
            )
            resized_height, resized_width = resized_icon.shape[:2]

            # Perform template matching
            result = cv2.matchTemplate(
                screenshot, resized_icon, cv2.TM_CCOEFF_NORMED
            )

            # Find locations where the matching result is above the threshold
            locations = np.where(result >= threshold)
            matches = list(zip(*locations[::-1]))  # Convert to (x, y) coordinates

            # Collect matches with their matching scores
            for pt in matches:
                x, y = pt
                match_score = result[y, x]
                all_matches.append({
                    'x': x,
                    'y': y,
                    'w': resized_width,
                    'h': resized_height,
                    'scale': scale,
                    'score': match_score
                })

            if debug and matches:
                logger.debug(f"Scale {scale:.2f}: Found {len(matches)} matches.")

        if all_matches:
            # Select the match with the highest matching score
            best_match = max(all_matches, key=lambda m: m['score'])
            center_x = best_match['x'] + best_match['w'] // 2
            center_y = best_match['y'] + best_match['h'] // 2

            logger.debug(
                f"Best match at center ({center_x}, {center_y}) with scale {best_match['scale']:.2f} and score {best_match['score']:.2f}."
            )

            if debug:
                top_left = (best_match['x'], best_match['y'])
                bottom_right = (
                    top_left[0] + best_match['w'],
                    top_left[1] + best_match['h']
                )
                cv2.rectangle(
                    screenshot, top_left, bottom_right, (0, 255, 0), 2
                )
                cv2.circle(
                    screenshot, (center_x, center_y), 5, (255, 0, 0), -1
                )
                cv2.imshow('Best Match with Center', screenshot)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

            return (center_x, center_y)
        else:
            logger.debug(f"No matches found for icon {icon_path}.")
            return None

    except Exception as e:
        logger.exception(f"Error finding icon on screen: {e}")
        return None
