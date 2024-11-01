# logging_config.py

import logging
import os
from logging.handlers import RotatingFileHandler

# Determine the path to the logs directory
base_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(base_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s:%(name)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ]
)

# Create applicant logger
applicant_logger = logging.getLogger('applicant_logger')
applicant_logger.setLevel(logging.INFO)

applicant_log_file = os.path.join(logs_dir, 'applicant_logs.log')

applicant_handler = RotatingFileHandler(
    applicant_log_file, maxBytes=5 * 1024 * 1024, backupCount=5
)
applicant_handler.setLevel(logging.INFO)
applicant_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
applicant_handler.setFormatter(applicant_formatter)
applicant_logger.addHandler(applicant_handler)

# Create status logger
status_logger = logging.getLogger('status_logger')
status_logger.setLevel(logging.INFO)

status_log_file = os.path.join(logs_dir, 'status_logs.log')

status_handler = RotatingFileHandler(
    status_log_file, maxBytes=5 * 1024 * 1024, backupCount=5
)
status_handler.setLevel(logging.INFO)
status_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s:%(name)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
status_handler.setFormatter(status_formatter)
status_logger.addHandler(status_handler)
