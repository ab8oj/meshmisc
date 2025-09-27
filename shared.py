# Data shared between different parts of the GUI app

dotenv_file = ""
config = {}

node_conversations = {}
"""
Direct messages grouped by remote node shortname. Either "from" or "to" can be the remote
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
direct_messages = {}
"""
Simpler buffer for all direct messages regardless of node. 
{devicename:[           
    {"Timestamp": timestamp,
     "Sender": sender,
     "Message": message}
    ]
}
"""