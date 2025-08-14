#!/bin/sh

if command -v adb >/dev/null 2>&1; then
    echo "ADB command found. Attempting to connect..."
    adb connect localhost:21503
fi
script_dir=$(dirname "$0")
python $script_dir/cli.py auto # --debug
read 