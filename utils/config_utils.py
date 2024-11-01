# utils/config_utils.py

import json
import logging
import os

logger = logging.getLogger(__name__)

def load_config():
    """
    Loads the entire configuration from a JSON file.
    """
    config_file = 'config.json'  # Adjust the path to your config file
    if not os.path.exists(config_file):
        logger.error(f"Configuration file {config_file} not found.")
        return {}
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            logger.debug(f"Loaded configuration from {config_file}.")
            return config
    except json.JSONDecodeError as e:
        logger.exception(f"Error parsing JSON configuration: {e}")
        return {}

def load_config_section(config, section):
    """
    Loads a specific section from the configuration dictionary.
    """
    if section in config:
        logger.debug(f"Loaded section '{section}' from config.")
        return config[section]
    else:
        logger.warning(f"Section '{section}' not found in config.")
        return {}
