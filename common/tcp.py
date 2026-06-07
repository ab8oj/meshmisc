# Interface to a node connected via tcp
import logging
import ipaddress

import meshtastic.tcp_interface
import meshtastic.util

from gui import shared

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)  # Set our own level separately

def make_connection_and_return(address):
    # This relies on the caller to keep the script alive, and to close the interface
    log.info(f"Connecting to {address}")
    interface = None
    try:
        interface = meshtastic.tcp_interface.TCPInterface(address)
        log.info(f"TCP interface to {interface.getShortName()} initialized")
    except Exception as e:
        log.info(f"ERROR: Could not connect via TCP: {e}")

    return interface

def scan_all_devices() -> list:
    # Return a list of tuples: ("tcp", device address, device name (address again)) or empty list
    if "TCP_DEVICES" not in shared.config:
        log.warning("No TCP_DEVICES key found in configuration file")
        return []

    log.info("Scanning for TCP devices")
    dev_list = []
    for dev in shared.config["TCP_DEVICES"].split(","):
        # Make sure we have a valid IP address before returning it
        try:
            valid_ip = ipaddress.ip_address(dev)
        except Exception as e:
            log.error(f"Invalid IP address in configuration: {dev} -- {e}")
        else:
            dev_list.append(("tcp", valid_ip, valid_ip))  # Return the device address or DNS hostname for both address and shortname
    log.info(f"Found {len(dev_list)} TCP device(s)")
    return dev_list
