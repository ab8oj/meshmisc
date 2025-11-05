# Experimenting and playing around
import time

# TODO: Support multiple mesh devices
# TODO: Move from print() to returning text or whatever to caller

from common import ble

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

def onConnectionUp(interface, topic=pub.AUTO_TOPIC):
    global CONNECTED
    print(f"Connected to {interface.getShortName()} ")
    CONNECTED = True
    return

def onConnectionDown(interface, topic=pub.AUTO_TOPIC):
    global CONNECTED
    print(f"Disconnected from {interface.getShortName()} ")
    CONNECTED = False
    # print("\n")
    return

def onReceiveText(packet, interface):
    our_shortname = interface.getShortName()
    text_message = packet.get("decoded").get("text")
    if "fromId" in packet and packet["fromId"] is not None:
        from_shortname = interface.nodes[packet["fromId"]].get("user").get("shortName")
        from_longname = interface.nodes[packet["fromId"]].get("user").get("longName")
    else:
        from_shortname = "unknown"
        from_longname = "unknown"
    msg_line = f"Text Message on {our_shortname} from node {from_longname} ({from_shortname}): {text_message}"
    print(msg_line)
    with open("message.log", "a") as log:  # TODO: make a better permanent storage solution
        print(msg_line, file=log)
    return

def onReceivePosition(packet, interface):
    print(f"Position packet received on interface {interface.getShortName()}")
    """
    if "decoded" in packet:
        print(packet["decoded"])
    else:
        print("Packet not decoded")
    """
    # print("\n")
    return

def onReceiveTelemetry(packet, interface):
    print(f"Telemetry packet received on interface {interface.getShortName()}")
    """
    if "decoded" in packet:
        print(packet["decoded"])
    else:
        print("Packet not decoded")
    """
    # print("\n")
    return

def onReceiveNeighborinfo(packet, interface):
    print(f"Neighborinfo packet received on interface {interface.getShortName()}")
    """
    if "decoded" in packet:
        print(packet["decoded"])
    else:
        print("Packet not decoded")
    """
    # print("\n")
    return

def onReceiveUser(packet, interface):
    print(f"User packet received on interface {interface.getShortName()}")
    """
    if "decoded" in packet:
        print(packet["decoded"])
    else:
        print("Packet not decoded")
    """
    # print("\n")
    return

def onReceiveData(packet, interface, topic=pub.AUTO_TOPIC):
    # print(f"Data packet, topic: {topic}")
    topic_str = str(topic)
    if topic_str in TOPIC_COUNTS:
        TOPIC_COUNTS[topic_str] += 1
    else:
        TOPIC_COUNTS[topic_str] = 1
    """
    if topic_str.startswith("meshtastic.receive("):  # Generic receive topic
        print(packet)
    """
    return

def onNodeUpdated(node, interface):
    # print(f"Node updated packet received on interface {interface.getShortName()}")
    # TODO: Create an in-memory node database from the relevant parts of the node data
    # print(node)
    # print("\n")
    return

def onLogLine(line, interface):
    print(f"Log line packet received on interface {interface.getShortName()}")
    print(line)
    print("\n")
    return

# === Functions that do useful things ===

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
pub.subscribe(onConnectionUp, "meshtastic.connection.established")
pub.subscribe(onConnectionDown, "meshtastic.connection.lost")
pub.subscribe(onReceiveText, "meshtastic.receive.text")
pub.subscribe(onReceivePosition, "meshtastic.receive.position")
pub.subscribe(onReceiveUser, "meshtastic.receive.user")
pub.subscribe(onReceiveTelemetry, "meshtastic.receive.telemetry")
pub.subscribe(onReceiveNeighborinfo, "meshtastic.receive.neighborinfo") # *** test this
pub.subscribe(onReceiveData, "meshtastic.receive")  # Catch-all to report and count all received packets
pub.subscribe(onNodeUpdated, "meshtastic.node.updated")
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
    for topic, count in TOPIC_COUNTS.items():
        print(f"{topic}: {count}")
    print("Done")
