import random
from utils.adb_utils import (
    get_connected_devices,
    select_device,
)


# Initialize last status check to None
last_status_check = None

def main():
    devices = get_connected_devices()
    if len(devices) == 0:
        raise Exception("No devices connected.")

    device_id = select_device(devices)
    

if __name__ == "__main__":
    main()
