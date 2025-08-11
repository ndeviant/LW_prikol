import json
from typing import Dict, List, Literal
from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.image_processing import find_template, find_templates
from src.core.config import CONFIG
from src.core.logging import app_logger
from src.game.device import controls

SecretTaskType = Literal['any', 'golden', 'de', 'de_s1']

class RallyRoutine(TimeCheckRoutine):
    secret_task_types = ['any', 'golden', 'de', 'de_s1']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.joined: Dict = self.state.get('joined') or {}
        self.rally_types: List[SecretTaskType] = self.options.get('rally_types') or ['golden']

    def _execute(self) -> bool:
        """Check and click rally button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        if not find_template(
            "rallies",
            tap=True,
            error_msg="Could not find 'rallies' icon"
        ):
            return True
        
        self.automation.game_state["is_home"] = False;

        for rally_type in self.rally_types:
            controls.human_delay(CONFIG['timings']['menu_animation'])
            if not find_template('rallies_opened'):
                find_template(
                    "rallies",
                    tap=True,
                )
                controls.human_delay(CONFIG['timings']['menu_animation'])
            
            matches = find_templates(
                f"join_{rally_type}_rally",
            )

            if not matches:
                continue

            last_index = len(matches) - 1

            for index, match in enumerate(matches):
                controls.click(match[0] - 60, match[1])
                controls.human_delay(CONFIG['timings']['rally_animation'])

                if not find_template(
                    "march",
                    tap=True,
                    tap_offset=(0, 10),
                    error_msg="Could not find march icon",
                ):
                    continue
                
                self.joined[rally_type] = self.joined.get(rally_type, 0)
                self.joined[rally_type] += 1
                self.state.set('joined', self.joined)
                app_logger.info(f"'{rally_type}' rally joined, total count: {self.joined[rally_type]}")

                if index < last_index:
                    controls.human_delay(CONFIG['timings']['menu_animation'])
                    if not find_template(
                        "rallies",
                        tap=True,
                        error_msg="Could not find 'rallies' icon, while iterating through matches"
                    ):
                        return True
                    controls.human_delay(CONFIG['timings']['menu_animation'])

        return True 