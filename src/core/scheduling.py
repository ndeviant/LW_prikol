from typing import TypedDict, Optional, Dict
from datetime import datetime, UTC
from src.core.logging import app_logger

class CheckInfo(TypedDict):
    last_run: Optional[float]  # Unix timestamp of last run
    needs_check: bool           # Whether check is currently due
    time_to_check: int         # Interval in seconds between checks

class ScheduledEvent(TypedDict):
    last_run: Optional[float]  # Unix timestamp of last run
    needs_check: bool           # Whether event is currently due
    day: str                    # Day of week (e.g., 'friday')
    time: str                   # Time in 24h format (e.g., '13:50')

def update_interval_check(checks: Dict[str, CheckInfo], current_time: float) -> Dict[str, CheckInfo]:
    """Update check times and set needs_check flags based on intervals"""
    for check_name, check_info in checks.items():
        if check_info["last_run"] is None:
            app_logger.debug(f"First run for check: {check_name}")
            check_info["needs_check"] = True
        else:
            time_elapsed = current_time - check_info["last_run"]
            check_info["needs_check"] = time_elapsed >= check_info["time_to_check"]
            app_logger.debug(
                f"Check {check_name}: elapsed={time_elapsed:.1f}s, interval={check_info['time_to_check']}s, needs_check={check_info['needs_check']}"
            )
    return checks

def update_schedule(events: dict[str, ScheduledEvent], current_time: float) -> dict[str, ScheduledEvent]:
    """Update scheduled events based on day of week and time (UTC)"""
    # Convert to UTC
    current_dt = datetime.fromtimestamp(current_time, UTC)
    current_day = current_dt.strftime('%A').lower()
    
    app_logger.debug(f"Current UTC time: {current_dt}, Day: {current_day}")
    
    for event_name, event in events.items():
        app_logger.debug(f"Checking schedule for '{event_name}'")
        app_logger.debug(f"Current day: {current_day}, Event day: {event['day']}")
        
        # Check if day matches or if no specific day is required
        if event["day"] is None or current_day != event["day"].lower():
            continue

        if event["last_run"] is not None:
            last_run_dt = datetime.fromtimestamp(event["last_run"], UTC)
            last_run_today = last_run_dt.date() == current_dt.date()

            if last_run_today:
                app_logger.debug(f"Event {event_name} already ran today (UTC)")
                continue
        
        # Parse target time (UTC)
        target_hour, target_min = map(int, event["time"].split(':'))
        target_dt = current_dt.replace(hour=target_hour, minute=target_min)
        
        # Calculate time difference in minutes
        time_diff = abs((current_dt - target_dt).total_seconds() / 60)
        app_logger.debug(f"Time difference for {event_name}: {time_diff:.1f} minutes (UTC)")
        
        # Check if within 10 minute window
        if time_diff <= 10:
            app_logger.info(f"Scheduling event {event_name} (within {time_diff:.1f} minute window UTC)")
            event["needs_check"] = True
                
    return events 