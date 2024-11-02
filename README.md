# Last War Bot Setup and Installation Guide

This guide provides instructions for setting up and running the Last War bot. Follow these steps carefully to ensure everything is set up correctly for smooth bot operation.

## Table of Contents


1. [Install Python](#install-python)
2. [Install Required Python Packages](#install-required-python-packages)
3. [Install ADB (Android Debug Bridge)](#install-adb-android-debug-bridge)
4. [Choose Your Android Environment](#choose-your-android-environment)
5. [Set Up Virtual Environment](#set-up-virtual-environment)
6. [Running the Bot](#running-the-bot)
7. [Troubleshooting](#troubleshooting)


---

## 1. Install Python

Ensure you have Python 3.6 or higher installed on your machine.

* **Download Python**: [Python Official Website](https://www.python.org/downloads/)
* **Verify Installation**:

  ```bash
  python --version
  ```


---

## 2. Install Required Python Packages

Install the necessary Python packages using pip.

* **Using requirements.txt**:

  ```bash
  pip install -r requirements.txt
  ```
* **Or Install Individually**:

  ```bash
  pip install opencv-python numpy Pillow
  ```


---

## 3. Install ADB (Android Debug Bridge)

Install ADB for Android debugging and communication with your device or emulator. Follow the instructions for your operating system:

### Windows:

* **Download ADB**: [Android SDK Platform Tools for Windows](https://developer.android.com/studio/releases/platform-tools)
* **Extract the ZIP File** to a directory (e.g., `C:\adb`).
* **Add ADB to System PATH** and verify installation by running:

  ```bash
  adb version
  ```

### macOS/Linux:

* **Download ADB**: [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
* **Extract the ZIP File** and add to your PATH, then verify by running:

  ```bash
  adb version
  ```


---

## 4. Choose Your Android Environment

You can run the bot using either a physical Android device or the BlueStacks emulator.

### Option A: Using a Physical Android Device


1. Enable USB Debugging on your Android device:
   * Go to **Settings > About phone**, tap **Build number** 7 times.
   * Go to **Settings > Developer options** and enable **USB Debugging**.
2. Connect your Android device via USB and authorize debugging.

### Option B: Using BlueStacks Emulator


1. Download and install [BlueStacks](https://www.bluestacks.com/).
2. Enable ADB debugging in BlueStacks by going to settings and toggling **ADB**.
3. Connect to BlueStacks using:

   ```bash
   adb connect 127.0.0.1:<port_number>
   ```


---

## 5. Set Up Virtual Environment

Setting up a virtual environment helps manage dependencies and avoid conflicts.

### Steps to Set Up a Virtual Environment:


1. **Create a Virtual Environment**:

   ```bash
   python -m venv venv
   ```
2. **Activate the Virtual Environment**:
   * **Windows**:

     ```bash
     venv\Scripts\activate
     ```
   * **macOS/Linux**:

     ```bash
     source venv/bin/activate
     ```
3. **Install Dependencies**:
   Inside the virtual environment, install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```


---

## 6. Running the Bot

Follow these steps to run the bot correctly:


1. **Start the Virtual Environment**:
   * **Windows**:

     ```bash
     venv\Scripts\activate
     ```
   * **macOS/Linux**:

     ```bash
     source venv/bin/activate
     ```
2. **Launch the Last War App**:
   * Open the Last War app on your Android device or BlueStacks emulator.
3. **Navigate to the Capitol Buffs Screen**:
   * Ensure that you are on the **Capitol Buffs screen** of the Last War app.
   * **Scroll to the bottom of the screen** if the Capitol is occupied and there are conqueror positions at the top of the screen. This will ensure that the secretary positions are visible and clickable.
4. **Adjust Line 23 in** `main.py` Based on Your UI:
5. **Verify and Adjust** `config.json`for Secretary Positions:
   * You may need to adjust the positions of the secretaries to match the current UI layout. If the capitol is currently conquered, set `options.alternatePositons: true`
6. **Run the Script**:
   Navigate to your project directory and run the script:

   ```bash
   python main.py
   ```


---

## 7. Troubleshooting

### ADB Issues:

* Ensure your device or emulator is connected and recognized by ADB.
* Verify by running:

  ```bash
  adb devices
  ```

### Icon Detection Issues:

* Enable `debug=True` in your function calls to get detailed logs.
* Verify that the icon template images are correct and paths are accurate.

### Dependencies:

* Make sure all required Python packages are installed:

  ```bash
  pip install --upgrade --force-reinstall -r requirements.txt
  ```


