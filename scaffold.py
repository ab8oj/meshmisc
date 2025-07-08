# Console-type scaffolding of the logic layer
import time

# TODO: Support multiple mesh devices
# TODO: Move from print() to returning text or whatever to caller

import ble

from pubsub import pub
import logging

# Ugh, global variables
# TODO: Find a better way to track connection status, like perhaps making all this a class
CONNECTED = False
TOPIC_COUNTS = {}

# === Mesh event handlers ===
# NOTE: the parameter names must match exactly what the topic expects. For example,
#       the node parameter name in onNodeUpdated must be 'node'.
#       Topics and parameters: https://python.meshtastic.org/index.html#published-pubsub-topics

# noinspection DuplicatedCode
def onConnectionUp(interface, topic=pub.AUTO_TOPIC):
    global CONNECTED
    print(f"Connected to {interface.getShortName()} ")
    CONNECTED = True
    return

# noinspection DuplicatedCode
def onConnectionDown(interface, topic=pub.AUTO_TOPIC):
    global CONNECTED
    print(f"Disconnected from {interface.getShortName()} ")
    CONNECTED = False
    print("\n")
    return

def onReceiveText(packet, interface):
    print(f"Text message received on interface {interface.getShortName()}")
    if "decoded" in packet and "text" in packet["decoded"]:
        # ***
        print(packet["decoded"])
        text_message = packet["decoded"]["text"]
        sender_id = packet["from"]
        print(f"Text Message from Node {sender_id}: {text_message}")
    else:
        print("Packet not decoded")
    print("\n")
    return

def onReceivePosition(packet, interface):
    print(f"Position packet received on interface {interface.getShortName()}")
    if "decoded" in packet:
        print(packet["decoded"])
    else:
        print("Packet not decoded")
    print("\n")
    return

def onReceiveTelemetry(packet, interface):
    print(f"Telemetry packet received on interface {interface.getShortName()}")
    if "decoded" in packet:
        print(packet["decoded"])
    else:
        print("Packet not decoded")
    print("\n")
    return

def onReceiveUser(packet, interface):
    print(f"User packet received on interface {interface.getShortName()}")
    if "decoded" in packet:
        print(packet["decoded"])
    else:
        print("Packet not decoded")
    print("\n")
    return

def onReceiveData(packet, interface, topic=pub.AUTO_TOPIC):
    print(f"Data packet, topic: {topic}")
    if topic in TOPIC_COUNTS:
        TOPIC_COUNTS[topic] += 1
    else:
        TOPIC_COUNTS[topic] = 1
    return

def onNodeUpdated(node, interface):
    print(f"Node updated packet received on interface {interface.getShortName()}")
    print(node)
    print("\n")
    return

def onLogLine(line, interface):
    print(f"Log line packet received on interface {interface.getShortName()}")
    print(line)
    print("\n")
    return

# === Functions that do useful things ===

# noinspection DuplicatedCode
def get_node_db(interface):
    print(f"\n--- NODE DATABASE for {interface.getShortName()} ---")
    # Each node is a dict, key is node name and value is a dict of things about that node
    # Some of those things are also dicts unto themselves (e.g. "user")
    # And not all of the things exist for each node, so do the usual checks for existence
    # TODO: Have a lot of "fun" formatting this
    for node in interface.nodes:
        print(f"Node: {node}")  # works
        for thing in interface.nodes[node].keys():
            print(f"{thing}: {interface.nodes[node][thing]}")
        print("-----------")
    print("End node DB")
    return

def send_broadcast_message(interface, message):
    print(f"\n--- SENDING BROADCAST MESSAGE on {interface.getShortName()} ---")
    try:
        # Send a broadcast message (to all nodes)
        # You can also specify a destination ID like: interface.sendText("Hello!", destinationId="!abcdef1234")
        interface.sendText(message)
        print("Broadcast sent")
    except Exception as e:
        print(f"Error sending message: {e}")
    print("-----------------------")
    return

# === Main ===

# Configure logging to see more details from the Meshtastic library
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Subscribe to events ---
# noinspection DuplicatedCode
# pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnectionUp, "meshtastic.connection.established")
pub.subscribe(onConnectionDown, "meshtastic.connection.lost")
# pub.subscribe(onReceiveText, "meshtastic.receive.text")  # Getting text fine
# pub.subscribe(onReceivePosition, "meshtastic.receive.position")  # Getting position fine
# pub.subscribe(onReceiveUser, "meshtastic.receive.user")  # Getting user fine
# pub.subscribe(onReceiveTelemetry, "meshtastic.receive.telemetry")  # Getting telemetry fine
pub.subscribe(onReceiveData, "meshtastic.receive")  # Catch-all to report all received packets
# pub.subscribe(onNodeUpdated, "meshtastic.node.updated")
pub.subscribe(onLogLine, "meshtastic.log.line")

somewhereland = None
try:
    print("Connecting to Meshtastic BLE interface")
    somewhereland = ble.make_connection_and_return(None)
    print("busy-waiting while async events happen")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Keyboard interrupt")
finally:
    """
    if somewhereland:
        print("Closing connection to Meshtastic BLE interface")
        somewhereland.close()
        print(f"Connection closed")
    """
    print(TOPIC_COUNTS)
    print("Done")
