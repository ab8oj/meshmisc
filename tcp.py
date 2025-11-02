# Interface to a node connected via tcp

import meshtastic.tcp_interface
import meshtastic.util

import shared


# TODO: it would be nice to make this class-based somehow.
# TODO: change print statements to logger

def make_connection_and_return(address):
    # This relies on the caller to keep the script alive, and to close the interface

    interface = None
    try:
        interface = meshtastic.tcp_interface.TCPInterface(address)
        print(f"TCP interface to {interface.getShortName()} initialized")
    except Exception as e:
        print(f"\nERROR: Could not connect via TCP: {e}")

    return interface

def scan_all_devices() -> list:
    # Return a list of tuples: ("tcp", device address, device name (address again)) or empty list
    if "TCP_DEVICES" not in shared.config:
        return []

    dev_list = []
    for dev in shared.config["TCP_DEVICES"].split(","):
        # TODO: basic IP address / hostname sanity checking
        dev_list.append(("tcp", dev, dev))  # Return the device address or DNS hostname for both address and shortname
    return dev_list
