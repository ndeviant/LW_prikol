from abc import ABC, abstractmethod
from datetime import datetime, UTC
import time
from src.core.logging import app_logger
from src.game.device import controls

class RoutineBase(ABC):
    """Base class for all automation routines"""

    def __init__(self, device_id: str, routine_name: str, automation=None, options=None) -> None:
        self.device_id = device_id
        self.automation = automation
        self.options = options or {}
        self.routine_name = routine_name
        self.bind_state()

    @abstractmethod
    def _execute(self) -> bool:
        """Execute the routine's main logic"""
        pass
    
    def start(self) -> bool:
        """Start the automation sequence with home navigation"""
        try:
            if not self.automation.game_state["is_home"]:
                if not controls.navigate_home(True):
                    app_logger.error("Failed to navigate home after on start")
                    return False
            self.automation.game_state["is_home"] = True
            return self._execute()
        except Exception as e:
            app_logger.error(f"Error in routine execution: {e}")
            return False
            
    def execute_with_error_handling(self, func, *args, **kwargs) -> bool:
        """Execute a function with standard error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            app_logger.error(f"Error in {func.__name__}: {e}")
            return False
        
    def bind_state(self):
        self.state = StateProxy(
            get = lambda field_name, default=None: self.automation.state.get(field_name, self.routine_name, self.routine_type, default=default),
            set = lambda field_name, value: self.automation.state.set(field_name, value, self.routine_name, self.routine_type)
        )
    
    @abstractmethod
    def should_run(self) -> bool:
        """Check if the routine should run now"""
        pass
        
    @abstractmethod
    def after_run(self) -> None:
        """Actions to perform after successful run"""
        pass


class TimeCheckRoutine(RoutineBase):
    """Base class for time-based check routines"""
    
    def __init__(self, device_id: str, routine_name: str, interval: int, last_run: float = None, automation=None, options=None) -> None:
        super().__init__(device_id, routine_name, automation, options)
        self.interval = interval
        self._last_run = last_run or 0
        self.automation = automation
        self.routine_type = 'time_checks'
        
    def should_run(self) -> bool:
        if self._last_run is None:
            return True
        return time.time() - self._last_run >= self.interval
        
    def after_run(self) -> None:
        self._last_run = time.time()


class DailyRoutine(RoutineBase):
    """Base class for daily scheduled routines"""
    
    def __init__(self, device_id: str, routine_name: str, day: str, time: str, last_run: float = None, automation=None, options=None):
        super().__init__(device_id, routine_name, automation, options)
        self.day = day.lower()
        self.time = time
        self._last_run = last_run or 0
        self.automation = automation
        self.routine_type = 'scheduled_events'
        
    def should_run(self) -> bool:
        current_dt = datetime.fromtimestamp(time.time(), UTC)

        if self._last_run:
            last_dt = datetime.fromtimestamp(self._last_run, UTC)
            if last_dt.date() == current_dt.date():
                return False
                
        current_week_day = current_dt.strftime('%A').lower()
        if current_week_day != self.day:
            return False
            
        target_hour, target_min = map(int, self.time.split(':'))
        target_dt = current_dt.replace(hour=target_hour, minute=target_min)
        time_diff = abs((current_dt - target_dt).total_seconds() / 60)
        
        return time_diff <= 10
    
    def after_run(self) -> None:
        self._last_run = time.time() 


class StateProxy:
    def __init__(self, get, set):
        self.get = get
        self.set = set
    