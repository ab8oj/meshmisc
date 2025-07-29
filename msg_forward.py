# Forward direct messages to email, and log all messages

import logging
import os
import sys
from pubsub import pub
from enum import Enum, unique

import survey
from dotenv import load_dotenv

from mesh_managers import DeviceManager, InterfaceError, Unimplemented
from email_interface import send_email

# Since we don't get constants or #DEFINEs in Python, we make due with enumerations
@unique
class MessageType(Enum):  # Define constants for message type, since they will be used in several places
    DIRECT_MESSAGE = "Direct"  # A message sent directly to a node
    BROADCAST_MESSAGE = "Broadcast"  # A message sent to "^all" on a channel
    PASSTHRU_MESSAGE = "Passthru"  # A message destined for another specific node; we should never see this

# === Event handlers ===

# Incoming message
def onIncomingMessage(packet, interface):
    # TODO: Move packet parsing to a separate function, this is getting a bit long
    msg_log_name = os.getenv("MSG_LOG_NAME")  # Where the messages themselves get logged (flat file)

    log = logging.getLogger(__name__)
    log.info("Received incoming message")
    log.debug(packet)

    my_node_id = interface.getMyNodeInfo().get("user", {}).get("id", "unknown")
    our_shortname = interface.getShortName()

    text_message = packet.get("decoded", {}).get("text", "Unknown text")

    if "raw" in packet and hasattr(packet["raw"], "channel"):
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
        message_type = MessageType.DIRECT_MESSAGE
    elif to_id == "^all":
        message_type = MessageType.BROADCAST_MESSAGE
    else:
        message_type = MessageType.PASSTHRU_MESSAGE  # Belt and suspenders, we shouldn't see one of these

    msg_line = (f"Text Message on interface {our_shortname} channel {channel}:\n"
                f"   From node {from_longname} ({from_shortname}) type {message_type.value}:\n"
                f"   {text_message}")
    log.debug(msg_line)
    print(msg_line)
    with open(msg_log_name, "a") as f:
        f.write(msg_line)

    if message_type == MessageType.DIRECT_MESSAGE:
        print("forwarding to email")
        log.info("forwarding to email")
        try:
            # TODO: Probably better to get these values in email_interface
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_sender = os.getenv("SMTP_SENDER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            email_from_address = os.getenv("EMAIL_FROM_ADDRESS")
            email_to_address = os.getenv("EMAIL_TO_ADDRESS")
            send_email(smtp_server, smtp_sender, smtp_password,
                       email_from_address, email_to_address,
                       f"Mesh: direct message from {from_longname}", msg_line)
            del smtp_password
        except Exception as e:
            log.error(e)
            print(f"Forward to email failed; exception {e}")
        else:
            print("Message forwarded")
            log.info("Message forwarded")

def onConnectionUp(interface):
    print(f"Connection established on interface {interface.getShortName()}")
    return

def onConnectionDown(interface):
    print(f"Connection lost on interface {interface.getShortName()}")
    return

def main():
    load_dotenv()
    app_log_name = os.getenv("APP_LOG_NAME")  # Application log messages (logger)

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: [%(name)s] %(module)s.%(funcName)s %(message)s',
                        filename=app_log_name, filemode='a')  # Configure root logger
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)  # Set our own level separately
    logging.getLogger("bleak").setLevel(logging.INFO)  # Turn off BLE debug info
    # Sadly, meshtastic logging runs from the root logger, so there's likely no way to set that separately

    device_manager = DeviceManager()

    # Find all available devices and list them
    log.debug("Finding all devices")
    devices = device_manager.find_all_available_devices()
    shortnames = [name for (typ, address, name) in devices]
    if shortnames:
        index = survey.routines.select('Choose a device: ', options=shortnames, focus_mark = '> ')
    else:
        print("No devices found, exiting")
        sys.exit(1)

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
