from enum import Enum
from typing import Dict, Any, Set

class SecretaryType(Enum):
    STRATEGY = "strategy"
    SECURITY = "security"
    DEVELOPMENT = "development"
    SCIENCE = "science"
    INTERIOR = "interior"
    MILITARY = "military"
    ADMINISTRATIVE = "administrative"

# Required secretaries (must be found)
REQUIRED_SECRETARIES: Set[str] = {
    SecretaryType.STRATEGY.value,
    SecretaryType.SECURITY.value,
    SecretaryType.DEVELOPMENT.value,
    SecretaryType.SCIENCE.value,
    SecretaryType.INTERIOR.value
}

# Optional secretaries (nice to have)
OPTIONAL_SECRETARIES: Set[str] = {
    SecretaryType.MILITARY.value,
    SecretaryType.ADMINISTRATIVE.value
}

# OCR Configuration
OCR_CONFIG: Dict[str, Any] = {
    'DEFAULT_LANG': 'eng',
    'PSM_MODE': 6,
    'ENGINE_MODE': 3,
    'WHITELIST': 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '
}

# Image Processing Constants
IMAGE_PROCESSING: Dict[str, float] = {
    'DEFAULT_THRESHOLD': 0.8,
    'MIN_MATCH_DISTANCE': 20,
    'TEMPLATE_MATCH_METHOD': 'TM_CCOEFF_NORMED'
}

# Device Interaction Constants
DEVICE_INTERACTION: Dict[str, Any] = {
    'CLICK_DELAY': 0.5,
    'SWIPE_DURATION': 300,
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 1.0
}

# File Paths
PATHS: Dict[str, str] = {
    'TEMP_DIR': 'tmp',
    'LOGS_DIR': 'logs',
    'CONFIG_FILE': 'config.json',
    'TEMPLATES_DIR': 'images/templates'
}

# Secretary Names and Aliases
SECRETARY_ALIASES: Dict[str, list] = {
    "strategy": ["strat", "strategy"],
    "security": ["secur"],
    "development": ["dev"],
    "science": ["sci", "science"],
    "interior": ["int", "interior"],
    "military": ["mil", "military"],
    "administrative": ["admin"]
} 