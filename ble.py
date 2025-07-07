# Playing around with BLE devices. A work in progress

import meshtastic
from meshtastic.ble_interface import BLEInterface, BLEClient
from pubsub import pub

def onReceive(packet, interface): # called when a packet arrives
    print(f"Received: {packet}")

def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    print("Connection established")

pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")

print("Scanning for BLE devices")
scan_result = BLEInterface.scan()
for device in scan_result:
    print(f"Name: {device.name} -- address: {device.address}")

print("Connecting to first device for now")
interface = BLEInterface(scan_result[0].address)
interface.connect(scan_result[0].address)

"""
Seems like I need the connect() in order to get output; just istantiating the interface object isn't enough.
But after several receives I get a BLEError saying the device doesn't exist. Is it dropping offline, or is 
the connect finally getting around to trying something?
Maybe try find_device instead of connect?
Maybe find an actual example?
"""
