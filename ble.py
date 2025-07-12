# Interface to a node connected via BLE
import time
from typing import Optional

import meshtastic.ble_interface

# TODO: it would be nice to make this class-based somehow.
# TODO: move print statements to something better like, oh I dunno, logging?
# TODO: see if multiple BLE devices can be supported

def make_connection_busyloop(address: Optional[str]):
    # Mostly just an example of the entire process: connect, keep the script executing, close when done
        print("Attempting to connect to a Meshtastic device via BLE...")
        interface = None
        try:
            interface = meshtastic.ble_interface.BLEInterface(address)
            print(f"BLEInterface to {interface.getShortName()} initialized. Waiting for connection...")
            # Keep the script running to allow for asynchronous events and to keep the BLE connection alive.
            while True:
                time.sleep(1)  # Sleep for a short period to avoid busy-waiting
        except meshtastic.ble_interface.BLEInterface.BLEError as e:
            print(f"\nERROR: Could not connect via BLE. {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
        finally:
            # Close the interface when the script exits
            if interface:
                print("\nClosing Meshtastic BLE interface...")
                interface.close()
                print("Interface closed.")

def make_connection_and_return(address: Optional[str]):
    # This relies on the caller to keep the script alive, and to close the interface
    # if address = None, the meshtastic BLE interface will hunt for one (and I think only one)
    interface = None
    try:
        interface = meshtastic.ble_interface.BLEInterface(address)
        print(f"BLEInterface to {interface.getShortName()} initialized")
    except meshtastic.ble_interface.BLEInterface.BLEError as e:
        print(f"\nERROR: Could not connect via BLE. {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

    return interface

def scan_all_devices() -> list:
    # Return a list of tuples: ("ble", device address , device name) or empty list
    ble_devices = meshtastic.ble_interface.BLEInterface.scan()
    dev_list = []
    for dev in ble_devices:
        dev_list.append(("ble", dev.address, dev.name))
    return dev_list
