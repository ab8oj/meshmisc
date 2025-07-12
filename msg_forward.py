# Forward select messages to another channel or SMS (via email)

from mesh_managers import MeshManager,  InterfaceError, Unimplemented
from pubsub import pub
import logging

# TODO: move these to a configuration file
log_name = "msg_forward.log"

# === Event handlers ===

# Incoming message
def onIncomingMessage(packet, interface):
    pass


# === Main ===

# Setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', filename=log_name, filemode='a')
logger = logging.getLogger(__name__)

logger.debug("Subscribing to incoming messages")
pub.subscribe(onIncomingMessage, "meshtastic.receive.text")

logger.debug("Instantiating MeshManager")
mesh_manager = MeshManager()
logging.debug("Finding all devices")
devices = mesh_manager.find_all_available_devices()

# ***
print(devices)
