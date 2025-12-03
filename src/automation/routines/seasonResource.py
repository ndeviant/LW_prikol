import asyncio
from src.automation.routines import FlexibleRoutine
from src.core.discord_bot import discord
from src.core.logging import app_logger
from src.game import controls

class SeasonResourceRoutine(FlexibleRoutine):
    def __init__(self, *args, **kwargs):
        # Call the parent's __init__ which handles all routine properties
        super().__init__(*args, **kwargs)
        self.found_count: int = self.state.get('found_count', 0)
        self.gathered_count: int = self.state.get('gathered_count', 0)

        self.map_checks: bool = self.options.get('map_checks', True)

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

        if (self.map_checks):
            cold_wave_active = controls.find_template(
                "s2_cold_wave",
                success_msg=f"Found 's2_cold_wave' indicator",
            )

            self.automation.state.set('cold_wave_active', bool(cold_wave_active), 'snow_storm', self.routine_type)

        if not controls.find_template(
            "rss_map",
            tap=True,
            success_msg="Found 'rss_map' icon"
        ):
            return True

        self.state.set('found_count', self.found_count + 1)
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
                wait=3,
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
            wait=4,
            interval=0.5,
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
        
        self.state.set('gathered_count', self.gathered_count + 1)
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
