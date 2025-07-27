# Forward select messages to another channel or SMS (via email)

import logging
from pubsub import pub

import survey

from mesh_managers import DeviceManager, InterfaceError, Unimplemented

# TODO: move these to a configuration file
log_name = "msg_forward.log"

# === Event handlers ===

# Incoming message
def onIncomingMessage(packet, interface):
    # TODO: Move packet parsing to a separate function, this is getting a bit long
    my_node_id = interface.getMyNodeInfo().get("user", {}).get("id", "unknown")
    our_shortname = interface.getShortName()

    text_message = packet.get("decoded", {}).get("text", "Unknown text")

    if "raw" in packet:  # Assumes channel will always be in the raw packet, if present. Harden later?
        channel = packet["raw"].channel
    else:
        channel = "Unknown"

    if "fromId" in packet and packet["fromId"] is not None:
        from_shortname = interface.nodes[packet["fromId"]].get("user", {}).get("shortName", "Unknown")
        from_longname = interface.nodes[packet["fromId"]].get("user", {}).get("longName", "Unknown")
    else:
        from_shortname = "unknown"
        from_longname = "unknown"

    to_id = packet.get("toId", "Unknown ToId")
    if to_id == my_node_id:
        message_type = "Direct"
    elif to_id == "^all":
        message_type = "Broadcast"
    else:
        message_type = "Passthru"  # I don't think this should happen, since the mesh bits should just forward it

    msg_line = (f"Text Message on interface {our_shortname} channel {channel}:\n"
                f"From node {from_longname} ({from_shortname}) type {message_type}: {text_message}")
    print(msg_line)

def onConnectionUp(interface):
    print(f"Connection established on interface {interface.getShortName()}")
    return

def onConnectionDown(interface):
    print(f"Connection lost on interface {interface.getShortName()}")
    return

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: [%(name)s] %(module)s.%(funcName)s %(message)s',
                        filename=log_name, filemode='a')  # Configure root logger
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)  # Set our own level separately
    logging.getLogger("bleak").setLevel(logging.INFO)  # Turn off BLE debug info
    # Sadly, meshtastic logging runs from the root logger, so there's likely no way to set that separately

    device_manager = DeviceManager()

    # Find all available devices and list them
    log.debug("Finding all devices")
    devices = device_manager.find_all_available_devices()
    shortnames = [name for (typ, address, name) in devices]
    index = survey.routines.select('Choose a device: ', options=shortnames, focus_mark = '> ')

    # Subscribe to relevant pubsub topics
    pub.subscribe(onConnectionUp, "meshtastic.connection.established")
    pub.subscribe(onConnectionDown, "meshtastic.connection.lost")
    pub.subscribe(onIncomingMessage, "meshtastic.receive.text")

    # Connect to the selected device
    (interface_type, address, name) = devices[index]
    interface = None
    try:
        interface = device_manager.connect_to_specific_device(interface_type, address)
        response = ""
        while response != "quit":
            response = survey.routines.input("Enter 'quit' to exit or anything else to be ignored\n")
    except Unimplemented:
        print(f"Unimplemented interface type: {interface_type}")
    except InterfaceError as e:
        print(f"Interface error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if interface:
            print(f"Disconnecting from {interface.getShortName()}")
            interface.close()  # *** close() hangs on disconnect at the present time

if __name__ == "__main__":
    main()
