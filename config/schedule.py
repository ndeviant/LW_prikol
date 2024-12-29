from src.core.scheduling import CheckInfo, ScheduledEvent

# Interval-based checks
time_checks: dict[str, CheckInfo] = {
    "reset": {
        "last_check": None,
        "needs_check": True,
        "time_to_check": 2700
    },
    "cleanup": {
        "last_check": None,
        "needs_check": True,
        "time_to_check": 3600
   },
   "donate": {
       "last_check": None,
       "needs_check": True,
       "time_to_check": 43200
   }
}

# Scheduled events
scheduled_events: dict[str, ScheduledEvent] = {
   "vs_capture": {
       "last_check": None,
       "needs_check": False,
       "day": "sunday",
       "time": "01:50"
   },
   "test_event": {
       "last_check": None,
       "needs_check": False,
       "day": "sunday",
       "time": "00:15"
   }
}