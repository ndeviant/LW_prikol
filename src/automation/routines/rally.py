import json
from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.image_processing import find_template, find_and_tap_template
from src.game.controls import human_delay
from src.core.config import CONFIG
from src.core.logging import app_logger

class RallyRoutine(TimeCheckRoutine):
    def __init__(self, device_id: str, interval: int, last_run: float = None, automation=None, **kwargs):
        super().__init__(device_id, interval, last_run, automation, **kwargs)
        self.joined_count: int = 0

    def _execute(self) -> bool:
        """Check and click rally button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:        
        if not find_and_tap_template(
            self.device_id,
            "rallies",
            error_msg="Could not find rally icon"
        ):
            return True
        
        self.automation.game_state["is_home"] = False;
        human_delay(CONFIG['timings']['menu_animation'])

        find_and_tap_template(
            self.device_id,
            "join_golden_rally",
            error_msg="Could not find join golden boss rally",
            offset=(-30, 0)
        )

        if not (self.options.get("only_golden")):
            find_and_tap_template(
                self.device_id,
                "join_de_rally",
                error_msg="Could not find join rally",
                offset=(-30, 0)
            )
        
        human_delay(CONFIG['timings']['rally_animation'])

        if not find_and_tap_template(
            self.device_id,
            "march",
            error_msg="Could not find march icon",
            offset=(0, 10)
        ):
            self.joined_count += 1
            app_logger.info(f"Rally joined, total count: {self.joined_count}")
            return True

        return True 