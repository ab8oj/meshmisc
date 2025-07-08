# Modifications from what Gemini gave me:
# - Added required address to BLEInterface (None in this case so it scans for a device)
# - Don't spam folks with a message every time a connection is made

import meshtastic.ble_interface
from pubsub import pub
import time
import logging

# Configure logging to see more details from the Meshtastic library
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Callback Functions for Meshtastic Events ---

def onReceive(packet, interface):
    """
    Callback function called when a Meshtastic packet is received.
    This function will print details of the received packet.
    """
    print("\n--- RECEIVED PACKET ---")
    print(f"Packet: {packet}")

    # Check if the packet contains a text message
    if "decoded" in packet and "text" in packet["decoded"]:
        text_message = packet["decoded"]["text"]
        sender_id = packet["from"]
        print(f"Text Message from Node {sender_id}: {text_message}")
    print("-----------------------")

def onConnection(interface, topic=pub.AUTO_TOPIC):
    """
    Callback function called when the connection status to the radio changes.
    This is useful for knowing when you've successfully connected.
    """
    print(f"\n--- CONNECTION STATUS: {topic} ---")
    if topic == "meshtastic.connection.established":
        print("Successfully connected to the Meshtastic device!")
        # Once connected, you can access the node database and send messages
        print("\n--- NODE DATABASE ---")
        # The node database is available via interface.nodes
        # It's a dictionary where keys are node IDs and values are NodeInfo objects
        for node_id, node_info in interface.nodes.items():
            print(f"  Node ID: {node_id}")
            if node_info.user:
                print(f"    User: {node_info.user.longName} ({node_info.user.shortName})")
            if node_info.position:
                print(f"    Position: Lat={node_info.position.latitude}, Lon={node_info.position.longitude}")
            print("-" * 20)

        # Example: Send a text message after connection is established
        print("\n--- SENDING MESSAGE ---")
        try:
            # Send a broadcast message (to all nodes)
            # You can also specify a destination ID like: interface.sendText("Hello!", destinationId="!abcdef1234")
            # interface.sendText("Hello from Python BLE!")
            print("Message would have been sent successfully!")
        except Exception as e:
            print(f"Error sending message: {e}")
        print("-----------------------")
    elif topic == "meshtastic.connection.lost":
        print("Connection to Meshtastic device lost.")

# --- Main Script ---

if __name__ == "__main__":
    # 1. Subscribe to Meshtastic events
    # We subscribe to "meshtastic.receive" for all incoming packets
    pub.subscribe(onReceive, "meshtastic.receive")
    # We subscribe to connection status changes
    pub.subscribe(onConnection, "meshtastic.connection.established")
    pub.subscribe(onConnection, "meshtastic.connection.lost")

    # 2. Initialize the BLEInterface
    # You can specify the Bluetooth address of your device if you know it:
    # device_address = "XX:XX:XX:XX:XX:XX" # Replace with your device's MAC address
    # interface = meshtastic.ble_interface.BLEInterface(address=device_address)

    # If you don't specify an address, it will try to find the first available Meshtastic device
    print("Attempting to connect to a Meshtastic device via BLE...")
    interface = None
    try:
        interface = meshtastic.ble_interface.BLEInterface(None)
        print("BLEInterface initialized. Waiting for connection...")

        # Keep the script running to allow for asynchronous events (like receiving messages)
        # and to keep the BLE connection alive.
        # This loop will run indefinitely until you stop the script (e.g., Ctrl+C).
        while True:
            time.sleep(1) # Sleep for a short period to avoid busy-waiting

    except meshtastic.ble_interface.BLEInterface.BLEError as e:
        print(f"\nERROR: Could not connect via BLE. {e}")
        print("Please ensure your Meshtastic device is on, discoverable, and not connected to another client.")
        print("You might need to specify the device's Bluetooth MAC address if multiple devices are nearby.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # 3. Clean up: Close the interface when the script exits
        if interface:
            print("\nClosing Meshtastic BLE interface...")
            interface.close()
            print("Interface closed.")
