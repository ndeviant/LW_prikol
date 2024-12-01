# Last War Bot Setup and Installation Guide

This guide provides instructions for setting up and running the Last War bot. Follow these steps carefully to ensure everything is set up correctly for smooth bot operation.

## Table of Contents


1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Bot](#running-the-bot)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

* Python 3.6 or higher
* Android device or emulator (BlueStacks recommended)
* ADB (Android Debug Bridge)
* USB debugging enabled on device/emulator

### Required Python Packages

```bash
opencv-python>=4.8.0
numpy>=1.24.0
pytesseract>=0.3.10
Pillow>=10.0.0
python-dotenv>=1.0.0
typing-extensions>=4.7.1
click>=8.0.0
pydantic>=2.0.0
```

## Installation


1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd lastwar-bot
   ```
2. **Set Up Virtual Environment**

   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```
3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Install ADB**
   * Windows: Download [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
   * Add ADB to system PATH
   * Verify installation:

     ```bash
     adb version
     ```

## Configuration


1. **Device Setup**
   * Enable USB debugging on your Android device
   * Connect device via USB or setup emulator
   * Verify connection:

     ```bash
     adb devices
     ```
2. **Game Setup**
   * Install Last War game on your device
   * Launch game once manually to complete initial setup
3. **Bot Configuration**
   The `config.json` file contains all necessary settings:
   * Button positions (in percentage of screen)
   * Template image paths
   * Game options
   * OCR settings

   Key positions:

   ```json
   "positions": {
       "profile": {"x": "5%", "y": "5%"},
       "secretaryMenu": {"x": "60%", "y": "68%"},
       "list": {"x": "85%", "y": "85%"},
       "accept": {"x": "50%", "y": "85%"}
   }
   ```

## Running the Bot


1. **Basic Run**

   ```bash
   python cli.py run
   ```
2. **Debug Mode**

   ```bash
   python cli.py --debug run
   ```

## Testing


1. **Test Game Launch**

   ```bash
   python cli.py test-relaunch
   ```

   This will:
   * Force close the game
   * Launch game
   * Wait for home screen
   * Clear notifications
   * Navigate to profile
   * Test secretary menu access
2. **Debug Testing**

   ```bash
   python cli.py --debug test-relaunch
   ```

   Shows detailed logs including:
   * Screen dimensions
   * Click positions
   * Template matching results
   * Navigation steps
3. **Expected Test Results**
   * Game should launch successfully
   * Home screen should be detected
   * Profile button click should work (5%, 5%)
   * Secretary menu should open (60%, 68%)
   * List and accept buttons should be accessible

## Troubleshooting

### Common Issues


1. **ADB Connection Issues**

   ```bash
   adb devices
   ```

   Should list your device. If not:
   * Check USB connection
   * Verify USB debugging is enabled
   * Try different USB ports
   * Restart ADB server:

     ```bash
     adb kill-server
     adb start-server
     ```
2. **Game Not Launching**
   * Verify package name in config.json
   * Check game installation
   * Try launching manually first
3. **Position Misalignment**
   * Run in debug mode to see click positions
   * Check screen dimensions are detected correctly
   * Verify percentage values in config.json
4. **Template Matching Failures**
   * Ensure template images match your game version
   * Check image paths in config.json
   * Verify template_match_threshold in config

### Logs and Debugging

* Check `lastwar.log` for detailed logs
* Use `--debug` flag for verbose output
* Temporary screenshots stored in `tmp/` folder
* Automatic cleanup of old temp files

### Support

If issues persist:


1. Run in debug mode
2. Collect logs
3. Take screenshots of the issue
4. Report with detailed steps to reproduce


