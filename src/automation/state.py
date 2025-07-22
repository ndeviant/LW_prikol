from pathlib import Path
import json
from typing import Dict, Any, Optional
from src.core.logging import app_logger
from collections import OrderedDict

class AutomationState:
    def __init__(self, state_file: Path = Path("state/automation_state.json")):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()
        
    def _load(self) -> Dict[str, Any]:
        """Load state from file"""
        if not self.state_file.exists():
            return {"time_checks": {}, "scheduled_events": {}}
        
        try:
            with open(self.state_file) as f:
                return json.load(f)
        except Exception as e:
            app_logger.error(f"Error loading state: {e}")
            return {"time_checks": {}, "scheduled_events": {}}
            
    def save(self) -> None:
        """Save current state to file"""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            app_logger.error(f"Error saving state: {e}")

    def get(self, field_name: str, check_name: str, check_type: str = "time_checks"):
        """Get last run time for a check"""
        return self._state.get(check_type, {}).get(check_name, {}).get(field_name)
    
    def set(self, field_name: str, value, check_name: str, check_type: str = "time_checks") -> None:
        """Set last run time for a check"""
        from collections import OrderedDict
        
        if check_type not in self._state:
            self._state[check_type] = OrderedDict()
        if check_name not in self._state[check_type]:
            self._state[check_type][check_name] = {}
        
        self._state[check_type][check_name][field_name] = value
        
    def get_all_checks(self, check_type: str = "time_checks") -> Dict[str, Any]:
        """Get all checks of a specific type"""
        return self._state.get(check_type, {}) 