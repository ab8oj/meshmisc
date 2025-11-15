# Data and functions shared between different parts of the GUI app

import logging

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)  # Set our own level separately

# === Shared data ===

# Environment configuration
dotenv_file = ""
config = {}

# Mesh interface objects for connected mesh devices
connected_interfaces = {}  # key = device shortname, value = MeshInterface object for that device

# Message buffers
node_conversations = {}  # Direct messages grouped by device and remote node shortname
"""
Either "from" or "to" can be the remote
node name, based on which direction that particular message was going
{local node (device) shortname:
    {remote node shortname:[           
        {"Timestamp": timestamp,
         "From": from,
         "To": to,
         "Message": message}
        ]
    }
}
e.g. node_conversations["OJB1"]["nrdW"][0]["message"]
"""
direct_messages = {}  # Direct messages grouped by device
"""
Simpler buffer for all direct messages regardless of node. 
{devicename:[           
    {"Timestamp": timestamp,
     "From": from,
     "To": to,
     "Message": message}
    ]
}
"""
channel_messages = {}  # Non-direct messages (sent to ^all) grouped by device and channel
"""
channel_messages[devicename][channel] is a list of messages: 
{devicename:
    {channel name:[           
        {"Timestamp": timestamp,
         "Sender": sender,
         "Message": message}
        ]
    }
}
"""

# Shared in-memory node database (potentially more reliable than in-device node database)
node_database = {}
"""
{devicename:
    {nodeid:
        {"shortName": shotname,
         "longName": longname,
         "hwModel": hwmodel,
         "publicKey": publickey,
         "position":
            {"time": timestamp,,
             "latitude": latitude,
             "longitude": longitude,
             "altitude": altitude,
             },
        "deviceMetrics":
            {"batteryLevel": batterylevel,
             "voltage": voltage,
             "channelUtilization": channelUtilization,
             "airUtilTx": airUtilTx,
             "uptimeSeconds": uptimeSeconds,
            },
        "snr": snr,
        "hopsAway": hopsAway,
        "lastHeard": lastHeard,
    }
}
"""

# Channel roles: channel_roles[integer_role_value] is the string value of the role
channel_roles = ["DISABLED", "PRIMARY", "SECONDARY"]

# === Shared functions ===

def find_longname_from_shortname(device, shortname):
    log.debug(f"Finding a node's longname from shortname {shortname}")
    # Brute force for now: shuffle through the interface's node list looking for the shortname
    for node_id, node_info in connected_interfaces[device].nodes.items():
        if node_info.get("user", {}).get("shortName", None) == shortname:
            longname = node_info.get("user", {}).get("longName", None)
            if longname:
                return longname
            else:
                return f"Meshtastic {shortname}"  # Node was found but has no longname

    return f"Meshtastic {shortname}"  # Node was not found
