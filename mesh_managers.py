# TODO: Add sane logging

import ble
import logging
from pubsub import pub

log = logging.getLogger(__name__)

class InterfaceError(Exception):
    pass

class Unimplemented(Exception):
    pass

class MeshManager:
    # TODO: Do I even need a connected variable here? See if there is one in the interface object
    connected = False  # TODO: Hey, this forces a single device at a time. Fix that!
    supported_interface_types = ["ble", "tcp", "serial"]
    # An "interface" is (connected, meshtastic.interface object)
    interfaces = []  # TODO: Add interface on first connect, making a distinction between "active" and "connected"

    def __init__(self):
        log.debug("Initializing mesh manager")
        super().__init__()
        pub.subscribe(self.onConnectionUp, "meshtastic.connection.established")
        pub.subscribe(self.onConnectionDown, "meshtastic.connection.lost")

    def onConnectionUp(self, interface, topic=pub.AUTO_TOPIC):
        log.info(f"Connection established on interface {interface.getShortName()}")
        self.connected = True  # TODO: fix for multiple interfaces
        return

    def onConnectionDown(self, interface, topic=pub.AUTO_TOPIC):
        log.info(f"Connection lost on interface {interface.getShortName()}")
        self.connected = False  # TODO: fix for multiple interfaces
        return

    def find_all_available_devices(self, interface_types=None) -> list:
        # Find all available mesh nodes on the listed interface types
        # Returns a list of tuples: (type, address, name)

        if interface_types is None:
            interface_types = self.supported_interface_types
        else:
            if not isinstance(interface_types, list):
                raise InterfaceError("interface_type must be a list")
            if not all(y in self.supported_interface_types for y in interface_types):
                raise InterfaceError(f"interface_type must be one of {str(self.supported_interface_types)}")

        # For each interface type, find all devices
        log.debug(f"Finding available devices for {interface_types}")
        devices = []  # List of all available devices on all requested types
        for i_type in interface_types:
            try:
                devs = self.find_devices_on_type(i_type)
                devices.extend(devs)
            except Unimplemented:
                pass  # Ignore unimplemented for now
            except Exception as e:
                log.error(f"Exception raised while trying to find devices on type {i_type}: {e}")
                raise

        return devices

    def find_devices_on_type(self, interface_type: str) -> list:
        # Find all available devices on a specific interface type
        # Returns a list of tuples: (type, address, name)

        if not any(typ in interface_type for typ in self.supported_interface_types):
            raise InterfaceError(f"interface_type must be one of {str(self.supported_interface_types)}")

        if interface_type == "ble":
            log.debug("Finding ble devices")
            return ble.scan_all_devices()  # Gives us a list of ("ble", address, name) tuples
        elif interface_type == "tcp":
            log.debug("Finding tcp devices")
            raise Unimplemented("TCP interface type is not currently supported")
        elif interface_type == "serial":
            log.debug("Finding serial devices")
            raise Unimplemented("Serial interface type is not currently supported")
        else:
            raise InterfaceError("Unknown interface type")  # Should not reach this (belt and suspenders)

    def connect_to_specific_device(self, address):  # TODO: verify input(s)
        # TODO: Don;'t forget to add the interface if it doesn't exist yet
        pass

    def disconnect_from_specific_device(self, address):
        pass

    def connect_to_first_device_on_type(self, interface_type: str):
        pass

    def connect_to_first_available_device(self, type_list:list):
        pass
