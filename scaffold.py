# Console-type scaffolding of the logic layer
import time

# TODO: Support multiple mesh devices
# TODO: Move from print() to returning text or whatever to caller

import ble

from pubsub import pub
import logging

# Ugh, global variables
# TODO: Find a better way to track connection status, like perhaps making all this a class
connected = False

# === Handlers for events ===

# noinspection DuplicatedCode
def onConnectionUp(interface, topic=pub.AUTO_TOPIC):
    global connected
    print(f"\n--- CONNECTION STATUS: {topic} ---")
    connected = True
    return

# noinspection DuplicatedCode
def onConnectionDown(interface, topic=pub.AUTO_TOPIC):
    global connected
    print(f"\n--- CONNECTION STATUS: {topic} ---")
    connected = False
    return

# noinspection DuplicatedCode
def onReceive(packet, interface):
    # TODO: Flesh out
    print(f"--- RECEIVED PACKET on {interface.getShortName()} ---")
    # Check if the packet contains a text message
    if "decoded" in packet and "text" in packet["decoded"]:
        text_message = packet["decoded"]["text"]
        sender_id = packet["from"]
        print(f"Text Message from Node {sender_id}: {text_message}")
    # TODO: Add other interesting things here
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
pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnectionUp, "meshtastic.connection.established")
pub.subscribe(onConnectionDown, "meshtastic.connection.lost")

"""
neverland = ble.make_connection_busyloop(None)
print("We came back from Neverland")
"""
somewhereland = None
try:
    print("Connecting to Meshtastic BLE interface")
    somewhereland = ble.make_connection_and_return(None)
    print("Waiting for connection to be established")

    while not connected:
        time.sleep(1)
        print(f"Connected: {connected}")
        if connected:
            break  # Caveman style - why is this even needed in the while loop?
    print("Node database:")
    get_node_db(somewhereland)  # *** this hangs, but just printing .nodes works
    # print(somewhereland.nodes)  # *** this works
    # TODO: send a directed message to myself. I think that means getting node info first
    # Busy-wait until the node drops, so we can see the async stuff
    print("busy-waiting while async events happen")
    while True:
        time.sleep(1)
finally:
    if somewhereland:
        somewhereland.close()
        print(f"Connection closed for interface {somewhereland.getShortName()}")
