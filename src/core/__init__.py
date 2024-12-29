"""Core functionality package"""

from .config import CONFIG, CONTROL_LIST
from .logging import setup_logging, app_logger
from .device import (
    get_screen_size,
    cleanup_device_screenshots,
    cleanup_temp_files,
    cleanup,
    ensure_dir
)
from .adb import (
    get_device_list,
    get_connected_device,
    launch_package,
    force_stop_package,
    press_back,
    tap_screen,
    swipe_screen
)
from .image_processing import (
    wait_for_image,
    find_all_templates,
    find_template
)

from .scheduling import (
    update_interval_check,
    update_schedule
)