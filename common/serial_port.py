# Interface to a node connected via serial port (really virtual serial port over USB)
# This can't be named "serial" because, like "golf", that name is already taken

import logging
import serial
from typing import Optional

import meshtastic.serial_interface
import meshtastic.util

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)  # Set our own level separately

def make_connection_and_return(device_path: Optional[str]):
    # This relies on the caller to keep the script alive, and to close the interface
    # if address = None, the meshtastic serial interface has 2 possible behaviors:
    #    1 - if only one Meshtastic device is found, it will connect to that one
    #    2 - if more than one device is found, it returns a warning and runs away like Brave Sir Robin

    interface = None
    if device_path:
        log.info(f"Connecting to {device_path}")
    else:
        log.info(f"Connecting to serial port")
    try:
        interface = meshtastic.serial_interface.SerialInterface(device_path)
        log.info(f"Serial interface to {interface.getShortName()} initialized")
    except serial.SerialException as e:
        log.error(f"\nERROR: Could not connect via serial port. {e}")
    except Exception as e:
        log.error(f"\nAn unexpected error occurred: {e}")

    return interface

def scan_all_devices() -> list:
    # Return a list of tuples: ("serial", device address , device name) or empty list
    log.info("Scanning for serial devices")
    serial_devices = meshtastic.util.findPorts(eliminate_duplicates=True)
    dev_list = []
    for dev in serial_devices:
        dev_list.append(("serial", dev, dev))  # Return the device path for both address and shortname
    log.info(f"Found {len(dev_list)} serial devices")
    return dev_list
