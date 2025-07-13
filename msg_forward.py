# Forward select messages to another channel or SMS (via email)

from mesh_managers import DeviceManager,  InterfaceError, Unimplemented
from pubsub import pub
import logging

# TODO: move these to a configuration file
log_name = "msg_forward.log"

# === Event handlers ===

# Incoming message
def onIncomingMessage(packet, interface):
    pass


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: [%(name)s] %(module)s.%(funcName)s %(message)s',
                        filename=log_name, filemode='a')
    log = logging.getLogger(__name__)
    logging.getLogger("bleak").setLevel(logging.INFO)  # Turn off BLE debug info

    log.debug("Subscribing to incoming messages")
    pub.subscribe(onIncomingMessage, "meshtastic.receive.text")

    log.debug("Instantiating MeshManager")
    device_manager = DeviceManager()
    log.debug("Finding all devices")
    devices = device_manager.find_all_available_devices()

    # ***
    print(devices)

if __name__ == "__main__":
    main()
