import json
from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.image_processing import find_template, find_and_tap_template
from src.core.config import CONFIG
from src.core.logging import app_logger
from src.game.device import controls

class RallyRoutine(TimeCheckRoutine):
    def __init__(self, device_id: str, interval: int, last_run: float = None, automation=None, *args, **kwargs):
        super().__init__(device_id, interval, last_run, automation, *args, **kwargs)
        self.joined_count: int = self.state.get('joined_count') or 0

    def _execute(self) -> bool:
        """Check and click rally button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:        
        if not find_and_tap_template(
            "rallies",
            error_msg="Could not find rally icon"
        ):
            return True
        
        self.automation.game_state["is_home"] = False;
        controls.human_delay(CONFIG['timings']['menu_animation'])

        find_and_tap_template(
            "join_golden_rally",
            error_msg="Could not find join golden boss rally",
            offset=(-60, 0)
        )

        if not (self.options.get("only_golden")):
            find_and_tap_template(
                "join_de_rally",
                error_msg="Could not find join rally",
                offset=(-60, 0)
            )
        
        controls.human_delay(CONFIG['timings']['rally_animation'])

        if not find_and_tap_template(
            "march",
            error_msg="Could not find march icon",
            offset=(0, 10)
        ):
            return True
        
        self.joined_count += 1
        self.state.set('joined_count', self.joined_count)
        app_logger.info(f"Rally joined, total count: {self.joined_count}")

        return True 