"""Configuration loading utilities"""

import json
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load main configuration file"""
    with open('config/config.json') as f:
        return json.load(f)
    
def load_control_list() -> Dict[str, Any]:
    """Load main configuration file"""
    with open('config/control_list.json') as f:
        return json.load(f)
    
# Load config once at module level
CONFIG = load_config() 

CONTROL_LIST = load_control_list()