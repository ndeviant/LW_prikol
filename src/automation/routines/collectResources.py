from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.logging import app_logger
from src.core.image_processing import find_templates, find_template
from src.game.device import controls
from src.core.config import CONFIG

class CollectResourcesRoutine(TimeCheckRoutine):
    def _execute(self) -> bool:
        """Reset game state by restarting the app"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:

        for template in [
            "rss_exp",
            "rss_ore",
            "rss_screw",
            "rss_drone_box"
        ]:
            if find_template(
                template,
                tap=True,
            ):
                controls.human_delay(0.2)
        
        if (find_template("status_interior")):
            app_logger.info("Secretary of interior status found, collecting RSS")

            for template in [
                "rss_gold",
                "rss_iron",
                "rss_food",
            ]:
                find_template(
                    template,
                    tap=True,
                )

        if not find_template(
            "rss_truck",
            tap=True,
            error_msg="Could not find rss_truck icon",
        ):
            return True   

        controls.human_delay(CONFIG['timings']['menu_animation'])
        
        if not find_template(
            "collect",
            tap=True,
            error_msg="Could not find collect icon",
        ):
            return True

        self.automation.game_state["is_home"] = False;

        return True 