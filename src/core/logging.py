"""Logging configuration"""

import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging(debug_mode: bool = False):
    """Initialize logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create logger
    logger = logging.getLogger('automation')
    
    # Set level based on debug flag
    level = logging.DEBUG if debug_mode else logging.INFO
    logger.setLevel(level)

    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # Create file handler
    file_handler = RotatingFileHandler(
        'logs/automation.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)  # Always keep debug in file
    file_handler.setFormatter(formatter)

    # Remove existing handlers if any
    logger.handlers = []
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create and configure logger
app_logger = setup_logging()