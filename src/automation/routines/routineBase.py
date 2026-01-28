from abc import ABC, abstractmethod
from datetime import datetime, UTC, timedelta
import time
import traceback
from typing import List
from src.core.config import CONFIG
from src.core.logging import app_logger
from src.game import controls

class RoutineBase(ABC):
    """Base class for all automation routines"""

    def __init__(self, routine_name: str, automation=None, schedule=None, options=None) -> None:
        self.automation = automation
        self.schedule = schedule or {}
        self.options = options or {}
        self.routine_name = routine_name
        self._bind_state()

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
            app_logger.error(f"Error in '{self.routine_name}' {func.__name__}: {e}")
            error_traceback = traceback.format_exc()
            app_logger.error(error_traceback)
            return False
        
    def _bind_state(self):
        self.state = StateProxy(
            get = lambda field_name, default=None: self.automation.state.get(field_name, self.routine_name, self.routine_type, default=default),
            set = lambda field_name, value: self.automation.state.set(field_name, value, self.routine_name, self.routine_type),
            save = lambda: self.automation.state.save()
        )
    
    @abstractmethod
    def should_run(self) -> bool:
        """Check if the routine should run now"""
        pass
        
    @abstractmethod
    def after_run(self) -> None:
        """Actions to perform after successful run"""
        pass

class FlexibleRoutine(RoutineBase):
    """
    A routine class that can handle different scheduling patterns based on its parameters.
    """
    def __init__(self, routine_name: str, automation=None, schedule=None, options=None):
        super().__init__(routine_name, automation, schedule, options)
        
        # All possible parameters for different routines. Defaults to None.
        self.interval = schedule.get('interval')
        self.start_time = schedule.get('start_time')
        self.end_time = schedule.get('end_time')
        self.last_run = schedule.get('last_run') or 0
        self.except_days = [d.lower() for d in schedule.get('except_days', [])]
        self.run_week_parity = schedule.get('run_week_parity') # 'odd' or 'even'

        self.days: List[str] = []
        if self.schedule.get("day"):
            self.days = [self.schedule.get("day").lower()]
        elif self.schedule.get("days"):
            self.days = [d.lower() for d in self.schedule["days"]]
            
        self.routine_type = 'routines'

    @property
    def overdue_time(self) -> float:
        """
        Returns the time in seconds since the routine was last run,
        compared to its scheduled interval. Returns infinity if no interval is set.
        """
        # If there's no interval, the concept of "overdue" doesn't apply.
        # If the routine has never run, it is considered overdue.
        if not self.interval:
            return float('inf')
        
        if not self.last_run:
            return 300

        # Calculate the time that has passed since the last run.
        time_since_last_run = time.time() - self.last_run
        
        # Return the difference between the time passed and the required interval.
        # This value will be positive if overdue, or negative if not yet due.
        return time_since_last_run - self.interval

    def should_run(self) -> bool:
        """
        Determines if the routine should run based on the provided parameters.
        """
        if not self.schedule:
            app_logger.info(f"Routine '{self.routine_name}' skipped. Schedule not provided.")
            return False
        
        current_time_s = time.time()
        current_dt = datetime.fromtimestamp(current_time_s, UTC)

        # Veto 1: Skip if the current day is in the except_days list.
        current_week_day = current_dt.strftime('%A').lower()
        if current_week_day in self.except_days:
            app_logger.debug(f"Routine '{self.routine_name}' skipped. Current day '{current_week_day}' is in except_days list.")
            return False

        # Veto 2: Skip if the week parity does not match.
        if self.run_week_parity:
            current_week_num = current_dt.isocalendar()[1]
            is_odd_week = current_week_num % 2 != 0
            
            if (self.run_week_parity.lower() == 'odd' and not is_odd_week) or \
               (self.run_week_parity.lower() == 'even' and is_odd_week):
                app_logger.debug(f"Routine '{self.routine_name}' skipped. Week parity mismatch.")
                return False

        # Check for daily (one-time) schedule first, as it is the most specific time-based pattern
        if self.start_time and not self.interval and not self.end_time:
            # Check for specific days if provided
            if self.days and current_week_day not in self.days:
                app_logger.debug(f"Routine '{self.routine_name}' skipped. Mismatched day: {current_week_day} not in {self.days}")
                return False

            # Check if it has already run today
            if self.last_run:
                last_dt = datetime.fromtimestamp(self.last_run, UTC)
                if last_dt.date() == current_dt.date():
                    app_logger.debug(f"Event '{self.routine_name}' already ran today (UTC).")
                    return False
            
            # Check if current time is within a small window of the target time
            try:
                target_hour, target_min = map(int, self.start_time.split(':'))
                target_dt = current_dt.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)
                time_diff_minutes = abs((current_dt - target_dt).total_seconds() / 60)
                max_overdue = 10

                # Check if the target time has passed
                if current_dt < target_dt:
                    app_logger.debug(f"Routine '{self.routine_name}' skipped. Target time {self.start_time} has not yet passed.")
                    return False

                if time_diff_minutes <= max_overdue:
                    app_logger.info(f"Scheduling event '{self.routine_name}' (within {time_diff_minutes:.1f} minute window UTC).")
                    return True
                
                app_logger.debug(f"Routine '{self.routine_name}' skipped. It is more than {max_overdue} minutes overdue.")
                return False

            except ValueError:
                app_logger.error(f"Invalid start_time format: '{self.start_time}'")
                return False

        # Check for interval-based schedules, which can optionally have a day and/or time window
        if self.interval:
            # Check for specific days if provided
            if self.days and current_week_day not in self.days:
                app_logger.debug(f"Routine '{self.routine_name}' skipped. Mismatched day: {current_week_day} not in {self.days}")
                return False
            
            # Check for a time window if provided
            if self.start_time and self.end_time:
                try:
                    start_hour, start_min = map(int, self.start_time.split(':'))
                    end_hour, end_min = map(int, self.end_time.split(':'))
                    
                    start_dt = current_dt.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
                    end_dt = current_dt.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)

                    # Handle case where end_time is on the next day
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    
                    if not (start_dt <= current_dt <= end_dt):
                        app_logger.debug(f"Routine '{self.routine_name}' skipped. Current time not within window {self.start_time}-{self.end_time}.")
                        return False
                except ValueError:
                    app_logger.error(f"Invalid time format in schedule: start_time='{self.start_time}', end_time='{self.end_time}'")
                    return False

            # Finally, check if the interval has passed since the last run
            if self.last_run is None:
                return True
            
            return current_time_s - self.last_run >= self.interval

        # No valid pattern matched for a run
        return False
        
    def after_run(self) -> None:
        """Actions to perform after a successful run."""
        self.last_run = time.time()
        # We can remove this check because 'after_run' is already handling it
        self.state.set("last_run", time.time())
        self.state.save()


class ArmsRaceRoutine(RoutineBase):
    """Base class for daily scheduled routines"""
    def __init__(self, device_id: str, routine_name: str, last_run: float = None, automation=None, options=None):
        super().__init__(device_id, routine_name, automation, options)
        self.last_run = last_run or 0
        self.automation = automation
        self.routine_type = 'arms_race'

        self.ar_monday_day=CONFIG.get('ar_monday_day', 2)
        self.ar_count_daily = 24 / 4
        self.ar_total_count = 7 * self.ar_count_daily

        # Create the full list by repeating the schedule and slicing to the total count
        # We repeat the schedule enough times to exceed the total count, then slice.
        ar_schedule_sequence = ['hero', 'city', 'unit', 'tech', 'drone']
        self.ar_schedule = (ar_schedule_sequence * (self.ar_total_count // len(ar_schedule_sequence) + 1))[:self.ar_total_count]

    @property
    def ar_week_day(self) -> int:
        """
        Returns the adjusted day of the week (1-7), where the week starts on ar_monday_day.
        """
        # Get the actual day of the week (1=Monday, 7=Sunday)
        current_day = datetime.date.today().isoweekday()
        
        # Get the day on which the schedule week starts (e.g., Tuesday)
        start_day = self.ar_monday_day
        
        # Calculate the adjusted day using modular arithmetic.
        # The +7 handles cases where current_day < start_day.
        adjusted_day = ((current_day - start_day + 7) % 7) + 1
        
        return adjusted_day

    def get_daily_schedule(self, day_of_the_week: int = None) -> list:
        """
        Returns the schedule for a given day of the week.
        If no day is provided, returns the adjusted schedule for today.
        `day_of_the_week` should be 1-indexed (e.g., 1 for Monday, 7 for Sunday).
        """
        # If no day is provided, use the property
        if day_of_the_week is None:
            day_of_the_week = self.ar_week_day

        if not 1 <= day_of_the_week <= 7:
            raise ValueError("day_of_the_week must be between 1 and 7")
        
        start_index = (day_of_the_week - 1) * self.ar_count_daily
        end_index = start_index + self.ar_count_daily
        
        return self.ar_schedule[start_index:end_index]
    
    def after_run(self) -> None:
        self.last_run = time.time() 

class StateProxy:
    def __init__(self, get, set, save):
        self.get = get
        self.set = set
        self.save = save