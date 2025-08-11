from typing import Literal
from src.automation.routines import TimeCheckRoutine
from src.core.logging import app_logger
from src.core.image_processing import find_template
from src.core.discord_bot import discord
from src.game.device import controls
from src.core.config import CONFIG
import asyncio
import os

class CheckForDigsRoutine(TimeCheckRoutine):
    def __init__(self, device_id: str, routine_name: str, interval: int, last_run: float = None, automation=None, *args, **kwargs):
        super().__init__(device_id, routine_name, interval, last_run, automation, *args, **kwargs)
        self.is_enabled_notification = bool(os.getenv('DISCORD_WEBHOOK_URL'))
        self.unclaimed_dig_type: Literal['dig', 'drone'] = None
        self.found_count: int = self.state.get('found_count') or 0
        self.claimed_count: int = self.state.get('claimed_count') or 0
        self.claimed_drone_count: int = self.state.get('claimed_drone_count') or 0

        if not self.is_enabled_notification:
            app_logger.warning("Dig notification routine disabled: DISCORD_WEBHOOK_URL not found in environment variables")
        
    def _execute(self) -> bool:
        """Execute dig notification check sequence"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        """Check for dig icon and handle if found"""
        try:
            if (self.unclaimed_dig_type):
                self.search_chat_for_digs()

            # Open chat by clicking the dig icon
            if not find_template(
                "dig",
                tap=True,
                success_msg="Found dig icon"
            ):
                return True
            
            self.automation.game_state["is_home"] = False
                
            # Send Discord notification
            asyncio.run(self.send_notification())
            self.found_count += 1
            self.state.set('found_count', self.found_count)

            if not self.options.get("auto_claim"):
                return True

            # Check if dig is already dug up
            app_logger.info(f"Attempting to claim dig automatically")
            controls.human_delay(CONFIG['timings']['menu_animation'])
            self.claim_dig_from_chat()

            # If we just start digging
            if find_template(
                "dig_chat_start",
                tap=True,
                error_msg="Could not find dig_chat_start icon",
            ):
                self.unclaimed_dig_type = 'dig'

            if find_template(
                "dig_chat_start_drone",
                tap=True,
                error_msg="Could not find dig_chat_start_drone icon",
            ):
                self.unclaimed_dig_type = 'drone'

            if not self.unclaimed_dig_type:
                return True
                        
            controls.human_delay(CONFIG['timings']['menu_animation'])
            controls.human_delay(CONFIG['timings']['rally_animation'])

            # Look for all kinds of marks of ongoing dig
            found_dig = False
            if self.unclaimed_dig_type == 'dig':
                if find_template(
                    "dig_dig",
                    tap=True,
                    success_msg="Found dig_dig icon",
                    error_msg="Could not find dig_dig icon",
                    wait=3,
                    interval=0.3
                ):
                    found_dig = True

                if not found_dig:
                    if find_template(
                        "dig_dig_model_exc",
                        tap=True,
                        tap_offset=(0, -15),
                        success_msg="Found dig_dig_model_exc icon",
                        error_msg="Could not find dig_dig_model_exc icon",
                        wait=1,
                        interval=0.25
                    ):
                        found_dig = True
                
            if self.unclaimed_dig_type == 'drone':
                if find_template(
                    "dig_dig_drone",
                    tap=True,
                    success_msg="Found dig_dig_drone icon",
                    error_msg="Could not find dig_dig_drone icon",
                    wait=3,
                    interval=0.3
                ):
                    found_dig = True

                if not found_dig:
                    if find_template(
                        "dig_dig_model_drone",
                        tap=True,
                        tap_offset=(0, -15),
                        success_msg="Found dig_dig_model_drone icon",
                        error_msg="Could not find dig_dig_model_drone icon",
                        wait=1,
                        interval=0.25
                    ):
                        found_dig = True
   
            if not found_dig:
                if find_template(
                    "dig_dig_radar_icon",
                    tap=True,
                    tap_offset=(0, 40),
                    success_msg="Found dig_dig_radar_icon icon",
                    error_msg="Could not find dig_dig_radar_icon icon",
                    wait=3,
                    interval=0.3
                ):
                    found_dig = True

            if not found_dig:
                return True
            
            controls.human_delay(CONFIG['timings']['rally_animation'])

            if self.unclaimed_dig_type == 'dig' and not find_template(
                "dig_dig_dig",
                tap=True,
                error_msg="Could not find dig_dig_dig icon",
                success_msg="Found dig_dig_dig icon",
            ):
                return True
            
            if self.unclaimed_dig_type == 'drone' and not find_template(
                "dig_dig_dig_drone",
                tap=True,
                error_msg="Could not find dig_dig_dig_drone icon",
                success_msg="Found dig_dig_dig_drone icon",
            ):
                return True
            
            controls.human_delay(CONFIG['timings']['menu_animation'])
            
            if not find_template(
                "march",
                tap=True,
                error_msg="Could not find dig march icon",
            ):
                return True
            
            if not self.options.get("wait_for_dig"):
                return True
            
            wait_for_dig = self.options.get("wait_for_dig", 60)
            claim_btn = find_template(
                "dig_claim",
                wait=wait_for_dig,
                interval=self.options.get("wait_for_dig_interval", 0.5),
            )

            if claim_btn:
                controls.click(claim_btn[0], claim_btn[1])
                if (self.unclaimed_dig_type == 'dig'):
                    self.claimed_count += 1
                    self.state.set('claimed_count', self.claimed_count)
                else:
                    self.claimed_drone_count += 1
                    self.state.set('claimed_drone_count', self.claimed_drone_count)
                self.unclaimed_dig_type = None
                app_logger.info(f"Dig claimed, total count: {self.claimed_count + self.claimed_drone_count}")

            app_logger.info(f"Not found dig_claim after {wait_for_dig}s wait")

            return True
            
        except Exception as e:
            app_logger.error(f"Error in dig check routine: {e}")
            return False
        
    def open_alli_chat(self) -> bool:
        """Open the alliance chat"""
        try:
            width, height = controls.get_screen_size()
            chat = CONFIG['ui_elements']['chat']
            chat_x = int(width * float(chat['x'].strip('%')) / 100)
            chat_y = int(height * float(chat['y'].strip('%')) / 100)
            controls.click(chat_x, chat_y)
            controls.human_delay(CONFIG['timings']['menu_animation'])

            # Check if alliance chat is not selected
            alli_chat_inactive = find_template(
                "alliance_chat_inactive",
                wait=CONFIG['timings']['menu_animation'],
            )
            
            if alli_chat_inactive:
                controls.click(alli_chat_inactive[0], alli_chat_inactive[1])
                controls.human_delay(CONFIG['timings']['menu_animation'])

            return True
        
        except Exception as e:
            app_logger.error(f"Error opening alli chat: {e}")
            return False

    def claim_dig_from_chat(self) -> bool:
        # Check if dig is available to claim in chat
        found_dig = None
        if self.unclaimed_dig_type == 'drone' and find_template(
            "dig_chat_claim_drone",
            tap=True,
            tap_offset=(0, 15),
            success_msg="Found dig_chat_claim_drone icon",
        ):
            found_dig = 'drone'

        if self.unclaimed_dig_type == 'dig' and find_template(
            "dig_chat_claim",
            tap=True,
            tap_offset=(0, 15),
            success_msg="Found dig_chat_claim icon",
        ):
            found_dig = 'dig'

        if (found_dig):
            controls.human_delay(CONFIG['timings']['rally_animation'])

            if find_template(
                    "dig_claim",
                    tap=True,
                    error_msg="Could not find dig_claim icon",
                    success_msg="Found dig_claim icon"
                ):
                if (self.unclaimed_dig_type == 'dig'):
                    self.claimed_count += 1
                    self.state.set('claimed_count', self.claimed_count)
                else:
                    self.claimed_drone_count += 1
                    self.state.set('claimed_drone_count', self.claimed_drone_count)
                app_logger.info(f"Dig claimed, total count: {self.claimed_count + self.claimed_drone_count}")

            self.unclaimed_dig_type = None

            return True
        
        return False
    
            
    def search_chat_for_digs(self) -> bool:
        app_logger.info(f"Searching chat for digs")
        self.automation.game_state["is_home"] = False;
        self.open_alli_chat()

        chat_search_swipes = self.options.get("chat_search_swipes", 3);

        if self.claim_dig_from_chat():
            return True
        for _ in range(chat_search_swipes):
            controls.swipe(direction="up")
            controls.human_delay(CONFIG['timings']['menu_animation'])
            if self.claim_dig_from_chat():
                return True

        app_logger.info(f"No unclaimed dig found in chat")
        
        return False
            
    async def send_notification(self) -> bool:
        """Send bilingual notification"""
        if not self.is_enabled_notification:
            return True
            
        return await discord.send('dig')
