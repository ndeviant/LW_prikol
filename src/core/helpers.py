from datetime import datetime, time, UTC
from zoneinfo import ZoneInfo
from pathlib import Path

def ensure_dir(path: str) -> None:
    """Ensure directory exists"""
    Path(path).mkdir(exist_ok=True)

def convert_local_time_to_utc(local_time_str: str) -> datetime:
    """
    Converts a local time string (e.g., "HH:MM") for the current date
    into a UTC-aware datetime object, using the recommended built-in approach.
    """
    # 1. Get the current local date (naive)
    current_local_naive_date = datetime.now().date()

    # 2. Parse the time string
    try:
        hour, minute = map(int, local_time_str.split(':'))
    except ValueError:
        raise ValueError("Invalid time format. Please use 'HH:MM'.")

    # 3. Create a naive local datetime object for today at the specified time
    local_naive_dt = datetime.combine(current_local_naive_date, time(hour, minute))

    # 4. Make the datetime object timezone-aware using the system's local timezone
    # Calling .astimezone() on a naive datetime without arguments makes it aware
    # using the system's local timezone.
    local_aware_dt = local_naive_dt.astimezone()

    # 5. Convert to UTC
    utc_aware_dt = local_aware_dt.astimezone(UTC) # Use the imported UTC constant
    return utc_aware_dt
