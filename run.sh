adb connect localhost:21503
script_dir=$(dirname "$0")
python $script_dir/cli.py auto # --debug
read 