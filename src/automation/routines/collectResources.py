from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.adb import simulate_shake
from src.core.logging import app_logger
from src.core.discord_bot import discord
from src.core.image_processing import find_and_tap_template
from src.game.controls import human_delay
from src.core.config import CONFIG

class CollectResourcesRoutine(TimeCheckRoutine):
    def _execute(self) -> bool:
        """Reset game state by restarting the app"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        print("Collecting resources todo")
        #simulate_shake(self.device_id)

        if not find_and_tap_template(
            self.device_id,
            "rss_truck",
            error_msg="Could not find rss_truck icon",
        ):
            return True   

        human_delay(CONFIG['timings']['menu_animation'])
        
        if not find_and_tap_template(
            self.device_id,
            "collect",
            error_msg="Could not find collect icon",
        ):
            return True

        self.automation.game_state["is_home"] = False;

        return True 