# Game Automation

An automation tool for managing game tasks efficiently.

## Features

- Automated secretary management
- Resource collection
- Alliance donation handling (configurable)
- Automatic help button detection and clicking
- Smart delay system with configurable multiplier
- Robust error handling and recovery
- Automatic cleanup of temporary files and screenshots
- Log rotation with size limits

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
5. Configure your settings in `config/game_config.json`

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
  "match_threshold": 0.8         // Confidence threshold for template matching
}
```

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
│   ├── positions.json       # Screen coordinates
│   └── templates/           # Template images
├── src/
│   ├── core/               # Core functionality
│   ├── game/               # Game-specific logic
│   └── utils/              # Utility functions
├── logs/                   # Log files (rotated, max 10MB each)
└── tmp/                    # Temporary files (auto-cleaned)
```

## Logging

Logs are stored in the `logs/` directory with automatic rotation:
- Maximum file size: 10MB
- Keeps last 5 backup files
- Automatically rotates when size limit is reached

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License.


