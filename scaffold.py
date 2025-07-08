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

# === Mesh event handlers ===
# NOTE: the parameter names must match exactly what the topic expects. For example,
#       the node parameter name in onNodeUpdated must be 'node'.
#       Topics and parameters: https://python.meshtastic.org/index.html#published-pubsub-topics

# noinspection DuplicatedCode
def onConnectionUp(interface, topic=pub.AUTO_TOPIC):
    global CONNECTED
    print(f"\n--- CONNECTION STATUS: {topic} ---")
    CONNECTED = True
    return

# noinspection DuplicatedCode
def onConnectionDown(interface, topic=pub.AUTO_TOPIC):
    global CONNECTED
    print(f"\n--- CONNECTION STATUS: {topic} ---")
    CONNECTED = False
    return

# noinspection DuplicatedCode
def onReceive(packet, interface):
    # TODO: In the process of being replaced by message type handlers
    print(f"--- RECEIVED PACKET on {interface.getShortName()} ---")
    # Check if the packet contains a text message
    if "decoded" in packet and "text" in packet["decoded"]:
        text_message = packet["decoded"]["text"]
        sender_id = packet["from"]
        print(f"Text Message from Node {sender_id}: {text_message}")
    return

def onReceiveText(packet, interface):
    # Text nessage received (meshtastic.receive.text)
    if "decoded" in packet and "text" in packet["decoded"]:
        # ***
        print(packet["decoded"])
        text_message = packet["decoded"]["text"]
        sender_id = packet["from"]
        print(f"Text Message from Node {sender_id}: {text_message}")
    else:
        print("Packet not decoded")
    return

def onReceivePosition(packet, interface):
    print("Position packet received")
    return

def onReceiveUser(packet, interface):
    print("User packet received")
    return

def onReceiveDataPortnum(packet, interface):
    print("Data portnum packet received")
    return

def onNodeUpdated(node, interface):
    print("Node updated packet received")
    return

def onLogLine(line, interface):
    print("Log line packet received")
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
pub.subscribe(onReceiveText, "meshtastic.receive.text")
pub.subscribe(onReceivePosition, "meshtastic.receive.position")
pub.subscribe(onReceiveUser, "meshtastic.receive.user")
pub.subscribe(onReceiveDataPortnum, "meshtastic.receive.data.portnum")
pub.subscribe(onNodeUpdated, "meshtastic.node.updated")
pub.subscribe(onLogLine, "meshtastic.log.line")

somewhereland = None
try:
    print("Connecting to Meshtastic BLE interface")
    somewhereland = ble.make_connection_and_return(None)
    print("Waiting for connection to be established")

    while not CONNECTED:
        time.sleep(1)
        print(f"Connected: {CONNECTED}")
        if CONNECTED:
            break  # Caveman style - why is this even needed in the while loop?
    print("Node database:")
    get_node_db(somewhereland)
    # TODO: send a directed message to myself. I think that means getting node info first
    # Busy-wait until the node drops, so we can see the async stuff
    print("busy-waiting while async events happen")
    while True:
        time.sleep(1)
finally:
    if somewhereland:
        somewhereland.close()
        print(f"Connection closed for interface {somewhereland.getShortName()}")
