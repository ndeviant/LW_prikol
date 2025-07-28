"""Configuration loading utilities"""

import json
from typing import Dict, Any
from pathlib import Path
from src.core.logging import app_logger


class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._config: Dict[str, Any] = {}
        self._automation_config: Dict[str, Any] = {}
        self._load_configs()

    def _load_configs(self) -> None:
        """Load all configuration files"""
        try:
            with open(self.config_dir / "config.json") as f:
                self._config = json.load(f)
            with open(self.config_dir / "automation.json") as f:
                self._automation_config = json.load(f)
        except Exception as e:
            app_logger.error(f"Error loading config: {e}")
            if not self._config:
                self._config = {}
            if not self._automation_config:
                self._automation_config = {}

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to main config"""
        return self._config.get(key, {})

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from main config with default"""
        nested_value = self.get_nested_value(self._config, key) or default

        return nested_value

    def get_nested_value(self, d: Dict, path: str):
        keys = path.split('.')
        current_value = d
        for key in keys:
            if isinstance(current_value, dict):
                current_value = current_value.get(key)
                if current_value is None: # Key not found at this level
                    return None
            else: # Path continues but current_value is not a dict
                return None
        return current_value

    @property
    def time_checks(self) -> Dict[str, Any]:
        return self._automation_config.get("time_checks", {})

    @property
    def scheduled_events(self) -> Dict[str, Any]:
        return self._automation_config.get("scheduled_events", {})

    @property
    def control_list(self) -> Dict[str, Any]:
        """Get control list from main config"""
        return self._config.get('control_list', {
            "whitelist": {"alliance": []},
            "blacklist": {"alliance": []}
        })

    @property
    def adb(self) -> Dict[str, Any]:
        return self._config.get('adb', {
            "package_name": "com.fun.lastwar.gp",
            "host": "",
            "port": -1,
            "binary_path": "adb",
            "enforce_connection": False
        })


# Create global instances
CONFIG = ConfigManager()
