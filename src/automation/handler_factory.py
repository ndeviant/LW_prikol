import json
from typing import Type, Dict, Any, Optional
import importlib
from src.automation.routines.routineBase import RoutineBase, FlexibleRoutine
from src.core.logging import app_logger

class HandlerFactory:
    """Factory for creating automation handlers, using FlexibleRoutine as the base for all scheduled routines."""
    
    def __init__(self):
        self.failed_handlers = set()  # Track handlers that failed to create
    
    def create_handler(
        self, 
        handler_path: str, 
        config: Dict[str, Any],
        automation=None
    ) -> Optional[RoutineBase]:
        """
        Create a handler instance from a path string using the FlexibleRoutine class.
        
        Args:
            handler_path: Path to handler class (e.g., "src.automation.routines.help.HelpRoutine")
            config: Configuration data for the handler
            automation: Automation instance to pass to handler
            
        Returns:
            Instance of handler class or None if creation fails
        """
        # Skip if handler previously failed
        if handler_path in self.failed_handlers:
            return None
            
        try:
            module_path, class_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            handler_class: Type[RoutineBase] = getattr(module, class_name)
            
            # Use the 'schedule' key from the config to pass to FlexibleRoutine
            routine_name = config.get('routine_name', class_name)
            schedule_config = config.get('schedule', {})
            options = config.get('options', {})

            # All scheduled routines now inherit from FlexibleRoutine
            if issubclass(handler_class, FlexibleRoutine):
                if not schedule_config:
                    app_logger.error(f"No 'schedule' specified for the routine: {handler_path}")
                    self.failed_handlers.add(handler_path)
                    return None
        
                # We can now handle all scheduling patterns with a single class
                handler = handler_class(
                    routine_name=routine_name,
                    automation=automation,
                    schedule=schedule_config,
                    options=options
                )
            else:
                # This branch handles any other, non-flexible routines
                # that might exist and do not rely on a schedule.
                handler = handler_class(
                    routine_name=routine_name,
                    automation=automation,
                    schedule={},
                    options=options
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