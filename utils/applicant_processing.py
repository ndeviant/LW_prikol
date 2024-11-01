# utils/applicant_processing.py

import logging

from .adb_utils import click_at_location

logger = logging.getLogger(__name__)

def check_blacklist(applicant_name, alliance_tag, blacklist):
    """
    Checks if an applicant or their alliance tag is in the blacklist.
    """
    if applicant_name in blacklist.get('names', []):
        logger.warning(f"Applicant '{applicant_name}' is in the blacklist.")
        return True
    if alliance_tag in blacklist.get('tags', []):
        logger.warning(f"Alliance tag '{alliance_tag}' is in the blacklist.")
        return True
    return False

def click_applicant_checkbox(index, device_id, base_x, base_y, y_increment):
    """
    Simulates clicking the checkbox next to an applicant.
    """
    try:
        checkbox_x = base_x
        checkbox_y = base_y + (index * y_increment)
        click_at_location(checkbox_x, checkbox_y, device_id)
        logger.info(
            f"Clicked checkbox at index {index} at position ({checkbox_x}, {checkbox_y})."
        )
        return True
    except Exception as e:
        logger.exception(f"Error clicking checkbox at index {index}: {e}")
        return False
