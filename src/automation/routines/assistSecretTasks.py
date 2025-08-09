from datetime import datetime, UTC
import time
from typing import List, Literal
from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.config import CONFIG
from src.core.image_processing import find_all_templates, find_and_tap_template, find_template
from src.game.device import controls
from src.core.logging import app_logger

SecretTaskType = Literal['star', 'hero', 'science', 'constr']
offset_x = 150
offset_y = 20

class AssistSecretTasks(TimeCheckRoutine):
    secret_task_types = ['star', 'hero', 'science', 'constr']

    def __init__(self, device_id: str, routine_name: str, interval: int, last_run: float = None, automation=None, *args, **kwargs):
        super().__init__(device_id, routine_name, interval, last_run, automation, *args, **kwargs)

        self.claim_types: List[SecretTaskType] = self.options.get("claim_types", ['star'])
        self.min_star: int = self.options.get("min_star", 4)
        self.num_swipes: int = self.options.get("num_swipes", 1)

    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        try:

            if not find_and_tap_template(
                "tasks_menu",
                error_msg=f"Not found 'tasks_menu' button",
            ):
                return True

            controls.human_delay('menu_animation')
            self.automation.game_state["is_home"] = False

            if (find_template('assisted_max')):
                self.state.set('assisted_max_date', time.time())

            if not find_and_tap_template(
                "ally_tasks",
                error_msg=f"Not found 'ally_tasks' button",
            ):
                return True
            
            controls.human_delay(CONFIG['timings']['menu_animation'])

            self.assist_tasks()
            for _ in range(self.num_swipes):
                controls.swipe(direction="down")
                controls.human_delay(CONFIG['timings']['menu_animation'])
                self.assist_tasks()
            
            return True
                    
        except Exception as e:
            app_logger.error(f"Error assisting secret tasks: {e}")
            return False
        
    def assist_tasks(self):
        """Assist all types of tasks"""
        for claim_type in self.claim_types:
            matches = find_all_templates(
                f"assist_{claim_type}_task_{self.min_star}", 
                get_file_name=lambda template_name, success: f"{template_name}_{success}_{time.time()}" if success else ""
            )

            for match in matches:
                controls.click(match[0] + offset_x, match[1] + offset_y)
                controls.human_delay('menu_animation')

    def should_run(self):
        should_run_routine = super().should_run()
        if not should_run_routine:
            return False
        
        assisted_max_date = self.state.get('assisted_max_date', None)
        if assisted_max_date is None:
            return should_run_routine
    
        now = datetime.now()

        # Convert the timestamp to a datetime object
        assisted_max_dt = datetime.fromtimestamp(assisted_max_date, UTC)

        # If not reached max assists today
        max_reached_today = (now.year != assisted_max_dt.year or
                    now.month != assisted_max_dt.month or
                    now.day != assisted_max_dt.day)
        
        return max_reached_today