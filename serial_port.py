# Interface to a node connected via serial port (really virtual serial port over USB)
# This can't be named "serial" because, like "golf", that name is already taken

import serial
from typing import Optional

import meshtastic.serial_interface
import meshtastic.util

# TODO: it would be nice to make this class-based somehow.
# TODO: change print statements to logger

def make_connection_and_return(device_path: Optional[str]):
    # This relies on the caller to keep the script alive, and to close the interface
    # if address = None, the meshtastic serial interface has 2 possible behaviors:
    #    1 - if only one Meshtastic device is found, it will connect to that one
    #    2 - if more than one device is found, it returns a warning and runs away like Brave Sir Robin

    interface = None
    try:
        interface = meshtastic.serial_interface.SerialInterface(device_path)
        print(f"Serial interface to {interface.getShortName()} initialized")
    except serial.SerialException as e:
        print(f"\nERROR: Could not connect via serial port. {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

    return interface

def scan_all_devices() -> list:
    # Return a list of tuples: ("serial", device address , device name) or empty list
    # TODO: what does this actually return?
    serial_devices = meshtastic.util.findPorts(eliminate_duplicates=True)
    dev_list = []
    for dev in serial_devices:
        dev_list.append(("serial", dev, dev))  # Return the device path for both address and shortname
    return dev_list
