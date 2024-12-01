#!/usr/bin/env python3

import sys
import argparse
from typing import List, Optional
from pathlib import Path

from logging_config import app_logger, setup_logging
from utils.device_utils import get_screen_size
from utils.adb_utils import (
    launch_package,
    force_stop_package,
    press_back,
    get_device_list
)
from utils.game_utils import (
    test_relaunch,
    navigate_startup_screens,
    process_secretaries,
    detect_secretary_positions,
    run_automation
)
from utils.config_validation import load_and_validate_config as load_config
from utils.game_options import GameOptions
from utils.cleanup import clear_tmp_folder, start_cleanup_thread
from utils.session import Session
from utils.image_utils import capture_screenshot

def get_device_id() -> Optional[str]:
    """Get the first connected device ID"""
    try:
        devices = get_device_list()
        if not devices:
            app_logger.error("No devices connected")
            return None
            
        if len(devices) > 1:
            app_logger.warning(f"Multiple devices found, using first one: {devices[0]}")
            
        return devices[0]
        
    except Exception as e:
        app_logger.error(f"Error getting device ID: {e}")
        return None

def take_screenshot(device_id: str, output_path: Optional[str] = None) -> bool:
    """Take a screenshot and save it"""
    try:
        if output_path:
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Take screenshot
        screenshot_path = capture_screenshot(device_id, output_path)
        if screenshot_path:
            app_logger.info(f"Screenshot saved to: {screenshot_path}")
            return True
        return False
        
    except Exception as e:
        app_logger.error(f"Failed to take screenshot: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Last War Game Automation')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('command', choices=[
        'test-relaunch',
        'run',
        'screenshot',
        'devices',
        'detect-positions',
        'force-stop',
        'launch'
    ], help='Command to run')
    parser.add_argument('--output', '-o', help='Output path for screenshot')
    
    args = parser.parse_args()
    
    # Initialize logging
    setup_logging(args.debug)
    
    # Initialize cleanup
    if args.command in ['test-relaunch', 'run']:
        app_logger.info("Initializing cleanup")
        clear_tmp_folder()  # Initial cleanup
        start_cleanup_thread()  # Start periodic cleanup
    
    # Simple commands that don't need config
    if args.command == 'devices':
        devices = get_device_list()
        if devices:
            print("\nConnected devices:")
            for device in devices:
                print(f"  - {device}")
            print()
        else:
            print("\nNo devices connected\n")
        return
    
    # Get connected device
    device_id = get_device_id()
    if not device_id:
        sys.exit(1)
    
    # Commands that don't need full config
    if args.command == 'screenshot':
        if not take_screenshot(device_id, args.output):
            sys.exit(1)
        return
    
    # Load config for commands that need it
    config = load_config()
    if not config:
        sys.exit(1)
    
    # Create options
    options = GameOptions(**config.options)
    
    # Run command
    try:
        if args.command == 'test-relaunch':
            if not test_relaunch(device_id, config.templates, options, config.positions):
                sys.exit(1)
                
        elif args.command == 'run':
            # Create session
            session = Session(config, device_id)
            
            try:
                # Launch game and navigate to secretary screen
                if not test_relaunch(device_id, config.templates, options, config.positions):
                    app_logger.error("Failed to launch game")
                    sys.exit(1)
                
                # Run automation loop
                run_automation(device_id, config.templates, options, config.positions)
                
            except KeyboardInterrupt:
                app_logger.info("Interrupted by user")
            except Exception as e:
                app_logger.error(f"Error during run: {e}")
                sys.exit(1)
            finally:
                # Clean up session
                session.cleanup.cleanup_session_files()
                
        elif args.command == 'detect-positions':
            # Detect secretary positions
            positions = detect_secretary_positions(device_id, config.templates, options)
            if positions:
                print("\nDetected secretary positions:")
                for name, pos in positions.items():
                    print(f"  {name}: ({pos[0]}, {pos[1]})")
                print()
                
        elif args.command == 'force-stop':
            app_logger.info("Force stopping game")
            force_stop_package(device_id, options.package_name)
            
        elif args.command == 'launch':
            app_logger.info("Launching game")
            launch_package(device_id, options.package_name)
            
    except KeyboardInterrupt:
        app_logger.info("Interrupted by user")
    except Exception as e:
        app_logger.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 