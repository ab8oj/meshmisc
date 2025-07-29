import meshtastic.mesh_interface

import ble
import logging
from pubsub import pub

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)  # Set our own logging level separately from the root

class InterfaceError(Exception):
    pass

class Unimplemented(Exception):
    pass

class DeviceManager:
    # Manage a set of Meshtastic devices across several interface types.
    supported_interface_types = ["ble", "tcp", "serial"]

    def __init__(self):
        log.debug("Initializing mesh manager")
        super().__init__()
        pub.subscribe(self.onConnectionUp, "meshtastic.connection.established")
        pub.subscribe(self.onConnectionDown, "meshtastic.connection.lost")

    # TODO: do we need these here? Do we need to reflect state change to app layer?
    def onConnectionUp(self, interface, topic=pub.AUTO_TOPIC):
        log.info(f"Connection established on interface {interface.getShortName()}")
        return

    def onConnectionDown(self, interface, topic=pub.AUTO_TOPIC):
        log.info(f"Connection lost on interface {interface.getShortName()}")
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

    def connect_to_specific_device(self, interface_type, address) -> meshtastic.mesh_interface.MeshInterface:
        # Connect to one device of the given type and address
        # Returns the MeshInterface object representing the connected device

        if not any(typ in interface_type for typ in self.supported_interface_types):
            raise InterfaceError(f"interface_type must be one of {str(self.supported_interface_types)}")

        if interface_type == "ble":
            log.info(f"Connecting to ble device {address}")
            interface = ble.make_connection_and_return(address)  # Let exceptions fly past us to the caller
        elif interface_type == "tcp":
            log.debug("Finding tcp devices")
            raise Unimplemented("TCP interface type is not currently supported")
        elif interface_type == "serial":
            log.debug("Finding serial devices")
            raise Unimplemented("Serial interface type is not currently supported")
        else:
            raise InterfaceError("Unknown interface type")  # Should not reach this (belt and suspenders)

        return interface

    def disconnect_from_specific_device(self, address):
        pass

    def connect_to_first_device_on_type(self, interface_type: str):
        pass

    def connect_to_first_available_device(self, type_list:list):
        pass
