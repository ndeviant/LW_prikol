import asyncio
from src.automation.routines import FlexibleRoutine
from src.core.discord_bot import discord
from src.core.logging import app_logger
from src.game import controls

class SeasonResourceRoutine(FlexibleRoutine):
    def _execute(self) -> bool:
        """Check and click rally button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        # Go to world map
        if not (controls.find_template(
            "home",
            tap=True,
        ) or controls.find_template(
            "base",
        )):
            return True
        
        controls.human_delay('rally_animation')
        self.automation.game_state["is_home"] = False;

        if not controls.find_template(
            "rss_map",
            tap=True,
            success_msg="Found 'rss_map' icon"
        ):
            return True

        controls.human_delay('rally_animation')
        
        offset_y = 80
        found = controls.find_template(
            "rss_map_dig",
            tap=True,
            tap_offset=(0, offset_y),
            error_msg="Not found 'rss_map_dig' icon",
            wait=3,
            interval=0.5,
        )

        if not found:
            offset_y = 120
            found = controls.find_template(
                "rss_map_arrow",
                tap=True,
                tap_offset=(0, offset_y),
                error_msg="Not found 'rss_map_arrow' icon",
                wait=1,
                interval=0.5,
            )
            controls.human_delay('tap_delay')

        if not found:
            return True
        
        controls.device.click(found[0], found[1] + offset_y)
        controls.human_delay('menu_animation')

        if not controls.find_template(
            "dig_dig_dig",
            tap=True,
            error_msg="Could not find 'dig_dig_dig' icon",
        ):
            return True
        
        controls.human_delay('menu_animation')

        if not (controls.find_template(
            "squad_idle",
            tap=True,
            tap_offset=(20, 10),
        ) or controls.find_template(
            "squad_returning",
            tap=True,
            tap_offset=(20, 10),
        )):
            return True
        
        if not controls.find_template(
            "march",
            tap=True,
            error_msg="Could not find dig 'march' icon",
        ):
            return True
        
        app_logger.info('Gathering season resource...')
        
        return True 
    
    def find_in_chat(self):
        if not controls.find_template(
            "rss_bottom_chat",
            tap=True,
            success_msg="Found 'rss_bottom_chat' icon"
        ):
            return None
                            
        controls.human_delay('menu_animation')
        matches = controls.find_templates(
            "rss_chat",
            tap=True,
            error_msg="Not found 'rss_chat' icon"
        )

        if not matches:
            return True
        
        # Find the tuple with the largest y value
        best_match = max(matches, key=lambda match: match[1])

        return best_match
