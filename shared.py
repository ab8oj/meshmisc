# Data shared between different parts of the GUI app

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
    {channel number:[           
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