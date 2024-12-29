#!/usr/bin/env python3

import sys
import argparse
import traceback
import time
from pathlib import Path
import signal

from src.core.adb import launch_package, force_stop_package, get_device_list, get_connected_device
from src.core.device import cleanup_temp_files, ensure_dir
from src.core.logging import setup_logging, app_logger
from src.game.alliance_donate import run_alliance_donate
from src.game.automation import run_automation
from src.game.secretary_automation import run_secretary_loop

# Create parser at module level
parser = argparse.ArgumentParser(description='Game automation CLI')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
parser.add_argument('--output', help='Output file for results')
parser.add_argument('--no-home-check', action='store_true', help='Disable periodic home screen checks')
parser.add_argument('--no-cleanup', action='store_true', help='Disable cleanup of temporary files')
parser.add_argument(
    'command',
    choices=[
        'run',
        'loop',
        'devices',
        'force-stop',
        'launch',
        'donate',
    ],
    help='Command to execute'
)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    app_logger.info("\nShutdown requested, cleaning up...")
    args = parser.parse_args()
    if not args.no_cleanup:
        cleanup_temp_files()
    sys.exit(0)

def main():
    try:
        # Register signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        
        args = parser.parse_args()
        
        # Set up logging
        setup_logging(args.debug)
        
        # Create debug screenshot directory
        ensure_dir("tmp")
        
        # Get connected device
        device_id = get_connected_device()
        if not device_id:
            sys.exit(1)
            
        # Execute command
        if args.command == 'run':
            try:
                run_automation(device_id)
            finally:
                if not args.no_cleanup:
                    cleanup_temp_files()
        
        elif args.command == 'test':
            app_logger.info("Starting secretary processing loop...")
            try:
                run_secretary_loop(device_id)
            finally:
                cleanup_temp_files()
        
        elif args.command == 'loop':
            app_logger.info("Starting secretary processing loop...")
            try:
                for i in range(100):
                    app_logger.info(f"Running loop {i}")
                    run_secretary_loop(device_id)
            finally:
                cleanup_temp_files()
            
        elif args.command == 'devices':
            devices = get_device_list()
            print("\nConnected devices:")
            for device in devices:
                print(f"  {device}")
                
        elif args.command == 'force-stop':
            app_logger.info("Force stopping game...")
            force_stop_package(device_id, "com.fun.lastwar.gp")
            
        elif args.command == 'launch':
            app_logger.info("Launching game...")
            launch_package(device_id, "com.fun.lastwar.gp")
            
        elif args.command == 'donate':
            app_logger.info("Donating to alliance tech...")
            run_alliance_donate(device_id)
            
    except Exception as e:
        app_logger.error(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main() 