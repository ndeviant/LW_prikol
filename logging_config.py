# logging_config.py

import logging
import sys

app_logger = logging.getLogger('lastwar')

def setup_logging(debug_mode: bool = False):
    """Setup application logging"""
    level = logging.DEBUG if debug_mode else logging.INFO
    
    # Create handlers
    c_handler = logging.StreamHandler(sys.stdout)
    f_handler = logging.FileHandler('lastwar.log')
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    
    # Set handler levels
    c_handler.setLevel(level)
    f_handler.setLevel(level)
    
    # Add handlers to logger
    app_logger.addHandler(c_handler)
    app_logger.addHandler(f_handler)
    app_logger.setLevel(level)
    
    app_logger.info(f"Logging initialized (debug={debug_mode})")
