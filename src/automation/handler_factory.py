import json
from typing import Type, Dict, Any, Optional
import importlib
from src.automation.routines.routineBase import TimeCheckRoutine, DailyRoutine, RoutineBase
from src.core.logging import app_logger

class HandlerFactory:
    """Factory for creating automation handlers"""
    
    def __init__(self):
        self.failed_handlers = set()  # Track handlers that failed to create
    
    def create_handler(
        self, 
        handler_path: str, 
        device_id: str, 
        config: Dict[str, Any],
        automation=None
    ) -> Optional[RoutineBase]:
        """
        Create a handler instance from a path string
        Args:
            handler_path: Path to handler class (e.g. "src.automation.routines.help.HelpRoutine")
            device_id: Device ID to pass to handler
            config: Configuration data for the handler
            automation: Automation instance to pass to handler
        Returns:
            Instance of handler class or None if creation fails
        """
        # Skip if handler previously failed
        if handler_path in self.failed_handlers:
            return None
            
        try:
            # Import the module and get the class
            module_path, class_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            handler_class: Type[RoutineBase] = getattr(module, class_name)
            interval = None
            day = None

            # Create handler instance based on type
            if issubclass(handler_class, TimeCheckRoutine):
                # Time check routines need interval
                interval = config.get("time_to_check") or config.get("interval")
                if not interval:
                    app_logger.error(f"No interval specified for time check routine: {handler_path}")
                    self.failed_handlers.add(handler_path)
                    return None
            
            elif issubclass(handler_class, DailyRoutine):
                # Daily check routines needs day
                day = config.get("day")
                time = config.get("time")
                if not day:
                    app_logger.error(f"No day specified for daily check routine: {handler_path}")
                    self.failed_handlers.add(handler_path)
                    return None
                
            else:
                # Regular automation just needs device_id
                handler = handler_class(device_id, automation=automation)
                
                return handler
                    
            # Filter out known configuration keys that shouldn't be passed to __init__
            excluded_keys = {
                "handler", "time_to_check", "needs_check"
            }
            init_params = {
                k: v for k, v in config.items() 
                if k not in excluded_keys
            }
            
            if issubclass(handler_class, TimeCheckRoutine):
                handler = handler_class(
                    device_id,
                    automation=automation,
                    interval=interval,
                    **init_params
                )
            elif issubclass(handler_class, DailyRoutine):
                handler = handler_class(
                    device_id,
                    automation=automation,
                    **init_params
                )
                
            return handler
                
        except (ImportError, AttributeError) as e:
            app_logger.error(f"Failed to create handler {handler_path}: {e}")
            self.failed_handlers.add(handler_path)
            return None
        except Exception as e:
            app_logger.error(f"Unexpected error creating handler {handler_path}: {e}")
            self.failed_handlers.add(handler_path)
            return None 