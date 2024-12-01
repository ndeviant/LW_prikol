# utils/config_utils.py

import json
import os
from dataclasses import dataclass
from typing import Dict, Any
from logging_config import app_logger

@dataclass
class Config:
    templates: Dict[str, str]
    options: Dict[str, Any]
    positions: Dict[str, Dict[str, Any]]
    
    @classmethod
    def load(cls, config_file: str = 'config.json') -> 'Config':
        """Load configuration from JSON file"""
        if not os.path.exists(config_file):
            app_logger.error(f"Configuration file {config_file} not found")
            raise FileNotFoundError(f"Configuration file {config_file} not found")
            
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            
        return cls(
            templates=config_data.get('templates', {}),
            options=config_data.get('options', {}),
            positions=config_data.get('positions', {})
        )

def load_config():
    """
    Loads the entire configuration from a JSON file.
    """
    config_file = 'config.json'  # Adjust the path to your config file
    if not os.path.exists(config_file):
        app_logger.error(f"Configuration file {config_file} not found.")
        return {}
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            app_logger.debug(f"Loaded configuration from {config_file}.")
            return config
    except json.JSONDecodeError as e:
        app_logger.exception(f"Error parsing JSON configuration: {e}")
        return {}

def load_config_section(config, section):
    """
    Loads a specific section from the configuration dictionary.
    """
    if section in config:
        app_logger.debug(f"Loaded section '{section}' from config.")
        return config[section]
    else:
        app_logger.warning(f"Section '{section}' not found in config.")
        return {}
