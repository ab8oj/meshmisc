# Interface to a node connected via BLE
import logging
from typing import Optional

import meshtastic.ble_interface

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)  # Set our own logging level separately from the root

def make_connection_and_return(address: Optional[str]):
    # This relies on the caller to keep the script alive, and to close the interface
    # if address = None, the meshtastic BLE interface will hunt for one and connect to it
    interface = None
    try:
        log.info(f"Connecting to {address}")
        interface = meshtastic.ble_interface.BLEInterface(address)
        log.info(f"BLEInterface to {interface.getShortName()} initialized")
    except meshtastic.ble_interface.BLEInterface.BLEError as e:
        log.error(f"\nERROR: Could not connect via BLE. {e}")
    except Exception as e:
        log.error(f"\nAn unexpected error occurred: {e}")

    return interface

def scan_all_devices() -> list:
    # Return a list of tuples: ("ble", device address , device name) or empty list
    log.info("Scanning for BLE devices...")
    ble_devices = meshtastic.ble_interface.BLEInterface.scan()
    dev_list = []
    for dev in ble_devices:
        dev_list.append(("ble", dev.address, dev.name))
    log.info(f"Found {len(dev_list)} BLE devices.")
    return dev_list
