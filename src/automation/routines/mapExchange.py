from src.automation.routines import TimeCheckRoutine
from src.core.image_processing import find_all_templates, find_and_tap_template
from src.game.controls import humanized_tap
from src.core.logging import app_logger
from typing import Optional

class MapExchangeRoutine(TimeCheckRoutine):

    def _execute(self) -> bool:
        """Execute alliance donation sequence"""
        return self.execute_with_error_handling(self.run)

    def run(self) -> bool:
        """Run the map exchange routine"""
        if not self.navigate():
            return False

        return self.exchange_maps()

    def navigate(self) -> bool:
        self.automation.game_state["is_home"] = False

        """Navigate to the alliance donate menu and donate"""
        # Open alliance menu
        if not find_and_tap_template(
            self.device_id,
            "secret_task",
            error_msg="Could not find secret task icon"
        ):
            return False
        
        # Click the hidden treasures tab
        if not find_and_tap_template(
            self.device_id,
            "hidden_treasures",
            error_msg="Could not find hidden treasures tab"
        ):
            return False
        
        # Click the exchange button
        if not find_and_tap_template(
            self.device_id,
            "hidden_treasures_exchange",
            error_msg="Could not find hidden_treasures_exchange button"
        ):
            return False
        
        # Click the allies exchange button
        if not find_and_tap_template(
            self.device_id,
            "hidden_treasures_allies_exchange",
            error_msg="Could not find hidden_treasures_allies_exchange button"
        ):
            return False
        
        return True

    def exchange_maps(self) -> bool:
        """Start the exchange"""
        ignore_locations = []
        max_exchanges = 10
        exchanges = 0
        refresh_list = False
        exchange_locations = find_all_templates(
            self.device_id,
            "hidden_treasures_start_exchange"
        )
        
        while exchanges < max_exchanges and len(exchange_locations) > 0:
            # If we've already done an exchange, we need to find the next one
            if refresh_list:
                exchange_locations = find_all_templates(
                    self.device_id,
                    "hidden_treasures_start_exchange"
                )
            
            if not exchange_locations:
                app_logger.debug("Could not find hidden_treasures_start_exchange button")
                return True

            next_location = self.get_next_exchange_location(exchange_locations, ignore_locations)
            if not next_location:
                app_logger.debug("No more valid exchange locations")
                return True
            
            humanized_tap(self.device_id, next_location[0], next_location[1])

            if not find_and_tap_template(
                self.device_id,
                "hidden_treasures_confirm_exchange",
                error_msg="Could not find confirm button"
            ):
                ignore_locations.append(next_location)
                refresh_list = False
            else:
                refresh_list = True
            
            exchanges += 1

        return True

    def get_next_exchange_location(
        self, 
        exchange_locations: list[tuple[int, int]], 
        ignore_locations: list[tuple[int, int]]
    ) -> Optional[tuple[int, int]]:
        """
        Get the first exchange location that's not in the ignored list
        
        Args:
            exchange_locations: List of (x,y) coordinates for all exchange buttons
            ignore_locations: List of (x,y) coordinates for already processed locations
            
        Returns:
            Tuple of (x,y) coordinates for next valid location, or None if no valid locations
        """
        if not exchange_locations:
            return None
        
        # Define proximity threshold (in pixels)
        PROXIMITY_THRESHOLD = 10
        
        for location in exchange_locations:
            # Check if this location is close to any ignored location
            is_ignored = False
            for ignored in ignore_locations:
                # Calculate if points are within threshold distance
                if (abs(location[0] - ignored[0]) < PROXIMITY_THRESHOLD and 
                    abs(location[1] - ignored[1]) < PROXIMITY_THRESHOLD):
                    is_ignored = True
                    break
                
            if not is_ignored:
                app_logger.debug(f"Found next valid exchange location at: {location}")
                return location
            
        app_logger.debug("No more valid exchange locations found")
        return None
