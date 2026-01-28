from datetime import datetime, UTC
import time
from typing import List, Literal
from src.automation.routines import FlexibleRoutine
from src.core.config import CONFIG
from src.game import controls

SecretTaskType = Literal['star', 'hero', 'science', 'constr']
offset_x = 120
offset_y = 20

class AssistSecretTasks(FlexibleRoutine):
    """
    A routine to assist alliance members with secret tasks.
    It checks for tasks to assist at a specified interval, but only after the
    daily server reset if the maximum assists weren't already made.
    """
    secret_task_types = ['star', 'hero', 'science', 'constr']

    def __init__(self, *args, **kwargs):
        # Call the parent's __init__ which handles all routine properties
        super().__init__(*args, **kwargs)

        self.claim_types: List[SecretTaskType] = self.options.get("claim_types", ['star'])
        self.min_star: int = self.options.get("min_star", 4)
        self.num_swipes: int = self.options.get("num_swipes", 1)

    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        if not controls.find_template(
            "tasks_menu",
            tap=True,
            error_msg=f"Not found 'tasks_menu' button",
        ):
            return True

        controls.human_delay('menu_animation')
        self.automation.game_state["is_home"] = False

        if (controls.find_template('assisted_max')):
            self.state.set('assisted_max_date', time.time())

        if not controls.find_template(
            "ally_tasks",
            tap=True,
            error_msg=f"Not found 'ally_tasks' button",
        ):
            return True
        
        controls.human_delay(CONFIG['timings']['menu_animation'])

        self.assist_tasks()
        for _ in range(self.num_swipes):
            controls.device.swipe(direction="down")
            controls.human_delay(CONFIG['timings']['menu_animation'])
            self.assist_tasks()
        
        return True

        
    def assist_tasks(self):
        """Assist all types of tasks"""
        for claim_type in self.claim_types:
            matches = controls.find_templates(
                f"assist_{claim_type}_task_{self.min_star}", 
                file_name_getter=lambda file_name, success, template_name: 
                    f"{template_name}_{success}_{time.time()}" if success else file_name
            )

            for match in matches:
                controls.device.click(match[0] + offset_x, match[1] + offset_y)
                controls.human_delay('tap_delay')

    def should_run(self):
        # First, let the parent class handle the primary schedule check (interval/daily)
        if not super().should_run():
            return False
        
        assisted_max_date = self.state.get('assisted_max_date', None)
        if assisted_max_date is None:
            # If we've never hit max assists, we should run.
            return True

        # Convert the timestamp to a datetime object
        assisted_max_dt = datetime.fromtimestamp(assisted_max_date, UTC)
        now = datetime.fromtimestamp(time.time(), UTC)

        # Define a datetime object for 2 AM of the current day (in UTC)
        # The `replace` method creates a new datetime object with the specified time.
        today_reset = now.replace(hour=CONFIG['server_reset_utc'] or 2, minute=0, second=0, microsecond=0)

        # The routine should run if the current time is past 2 AM AND
        # the last run was before 2 AM today.
        can_run = (now >= today_reset) and (assisted_max_dt < today_reset)

        return can_run