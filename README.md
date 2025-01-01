# Game Automation

An automation tool for managing game tasks efficiently, including secretary management, alliance donations, and scheduled events.

## Features

- Automated secretary management with alliance tag filtering
- Resource collection
- Alliance donation handling
- Automatic help button detection
- Smart delay system with configurable multiplier
- Robust error handling and recovery
- Automatic cleanup of temporary files
- Log rotation with size limits
- Alliance whitelist filtering
- Scheduled event automation
- Map exchange automation
- Dig checking system

## Setup

1. Install Python 3.8 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Tesseract OCR:
   - **Windows**:
     1. Download and install [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)
     2. Add Tesseract to your PATH (default: `C:\Program Files\Tesseract-OCR`)
     3. Download additional language data files:
        - [Chinese (Simplified)](https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata)
        - [Korean](https://github.com/tesseract-ocr/tessdata/raw/main/kor.traineddata)
        - [Japanese](https://github.com/tesseract-ocr/tessdata/raw/main/jpn.traineddata)
        - [Russian](https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata)
        - [Arabic](https://github.com/tesseract-ocr/tessdata/raw/main/ara.traineddata)
        - [Thai](https://github.com/tesseract-ocr/tessdata/raw/main/tha.traineddata)
     4. Place downloaded .traineddata files in `C:\Program Files\Tesseract-OCR\tessdata`
   - **Linux**:
     ```bash
     sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-kor tesseract-ocr-jpn tesseract-ocr-rus tesseract-ocr-ara tesseract-ocr-tha
     ```
4. Connect your device via ADB
5. Configure your settings in `config/game_config.json` and `config/automation.json`
6. Create a `.env` file in the root directory with your Discord webhook:
   ```
   DISCORD_WEBHOOK_URL=your_webhook_url_here
   ```

## Configuration

### Game Config (`config/game_config.json`)

```json
{
  "package_name": "com.example.game",
  "sleep_multiplier": 1.0,        // Global multiplier for all delays
  "debug_mode": false,            // Enable/disable debug logging
  "max_retries": 3,              // Maximum retry attempts for actions
  "retry_delay": 1.0,            // Delay between retries
  "collect_resources_interval": 300,  // Seconds between resource collections
  "donate_alliance_interval": null,   // Seconds between alliance donations (null to disable)
  "screenshot_quality": 100,      // Quality of captured screenshots
  "match_threshold": 0.8,         // Confidence threshold for template matching
  "timings": {
    "menu_animation": 1.5         // Delay for menu animations
  },
  "discord": {
    "dig_notification": {
      "content": "🏴‍☠️ **Dig Notification!**\nA new dig location has been discovered on the map.",
      "embed_color": "0xFF0000",
      "embed_title": "Action Required",
      "embed_value": "Check the map for new dig locations!"
    }
  }
}
```

### Automation Config (`config/automation.json`)

This file controls all automation routines and their scheduling. Each routine can be configured with:
- `handler`: The Python class that implements the routine
- `interval`: Time in seconds between routine executions (for time-based checks)
- `schedule`: Specific schedule for routines that run at fixed times (for scheduled events)

Example:
```json
{
  "time_checks": {
    "routine_name": {
      "handler": "src.automation.routines.RoutineClass",
      "interval": 300
    }
  },
  "scheduled_events": {
    "event_name": {
      "handler": "src.automation.routines.EventClass",
      "schedule": {
        "day": "sunday",
        "time": "01:50"
      }
    }
  }
}
```

## Available Routines

The following routines are available for automation:

1. **Secretary Management** (`secretary`)
   - Handles secretary-related tasks
   - Interval: 30 seconds
   - Filters alliance tags and manages resources

2. **Alliance Donations** (`donate`)
   - Manages alliance donations
   - Interval: 25000 seconds
   - Automatically handles resource distribution

3. **Help Detection** (`help`)
   - Monitors and clicks help buttons
   - Interval: 10 seconds
   - Provides alliance support

4. **Map Exchange** (`mapExchange`)
   - Handles map exchange activities
   - Interval: 300 seconds
   - Manages map-related resources

5. **Dig Checking** (`dig`)
   - Monitors for dig opportunities
   - Interval: 10 seconds
   - Automates dig-related activities

6. **Cleanup** (`cleanup`)
   - Manages temporary files and resources
   - Interval: 3600 seconds (1 hour)
   - Prevents disk space issues

7. **Reset** (`reset`)
   - Handles game reset procedures
   - Interval: 2700 seconds
   - Maintains game state

8. **Weekly Reset** (`weekly_reset`)
   - Scheduled event for weekly resets
   - Runs every Sunday at 01:50
   - Handles weekly maintenance tasks

### Managing Routines

To enable or disable routines:
1. Open `config/automation.json`
2. To disable a routine:
   - Remove its entry from the configuration
   - Or set its interval to `null`
3. To enable a routine:
   - Add its configuration under `time_checks` or `scheduled_events`
   - Specify the handler path and desired interval/schedule

### Positions Config (`config/positions.json`)

Contains all screen coordinates for UI elements. Coordinates are specified as `[x, y]` pairs.

### Templates

Place template images in `config/templates/` directory:
- `help.png`: Template for help button detection
- Other game-specific templates

## Usage

Run the automation:
```bash
python cli.py
```

## Directory Structure

```
├── config/
│   ├── game_config.json     # Main configuration
│   ├── automation.json      # Routine configuration
│   ├── positions.json       # Screen coordinates
│   └── templates/           # Template images
├── src/
│   ├── core/               # Core functionality
│   ├── game/               # Game-specific logic
│   ├── automation/         # Automation routines
│   │   └── routines/      # Individual routine implementations
│   └── utils/             # Utility functions
├── logs/                   # Log files (rotated, max 10MB each)
└── tmp/                    # Temporary files (auto-cleaned)
```

## Logging

Logs are stored in the `logs/` directory with automatic rotation:
- Maximum file size: 10MB
- Keeps last 5 backup files
- Automatically rotates when size limit is reached
- Includes detailed routine execution information

## Cleanup

The automation includes automatic cleanup features:
- Temporary files older than 24 hours are removed
- Device screenshots are cleaned up periodically
- Cleanup runs every hour during automation
- Log files are automatically rotated when size limits are reached

## Error Handling

The automation includes robust error handling:
- Automatic recovery from disconnections
- Smart retries for failed actions
- Comprehensive logging for debugging
- Routine-specific error recovery mechanisms

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License.


