# meshmisc gui
wxPython GUI applications using the Meshtastic Python package

* mesh_gui.py - Meshtastic client written in wxPython

# Platform-specific notes
## Linux
* Bluetooth Meshtastic devices are not supported on Linux systems.
https://meshtastic.org/docs/hardware/devices/linux-native-hardware/
* GTK 3 must be installed before you can install the wxPython package.  `sudo apt-get install libgtk-3-dev`
## Mac OS
* As of this writing, there is a bug in the Meshtastic package that causes a hang when
disconnecting from a BLE device. At present, the only option is to force-quit the application
(control-C works if you ran the application or script from a shell)

# Meshtastic GUI client installation instructions (work in progress)
1. Clone the meshmisc repo: `git clone https://github.com/ab8oj/meshmisc.git`
2. Create the .env file in the meshmisc directory (see contents below)
3. Install the required packages
* pip install wxPython
* pip install pypubsub
* pip install meshtastic
* pip install objectlistview3
* pip install urllib3 (on MacOS: urllib3==1.26.6)  
* pip install python-dotenv
4. Run the app: `cd gui; python ./mesh_gui.py`

# .env contents
APP_LOG_NAME=mesh_gui.log  
CHANNEL_MESSAGE_LOG=channel-messages.csv  
DIRECT_MESSAGE_LOG=direct-messages.csv  
CONFIRM_ON_EXIT=True or Yes to confirm, any other value is ignored  
TCP_DEVICES='\<IP or dns hostname>,...'  # single quotes are required here

## Important note about handling Meshtastic pub/sub events
Evidently the topic subscriber functions  get *called* by the same thread that does the SendMessage, so they
execute in a Meshtastic device thread context, not in the main GUI thread. This prevents us from
directly manipulating the GUI through things like layout(). Changing values of widgets in the GUI does
seem to execute, but the updates are not seen in the GUI until the window is jiggled.
    
For this reason, we need to use wxPython events rather than pub/sub to do certain GUI things like Layout()
https://stackoverflow.com/questions/50914555/compatibility-between-pypubsub-and-pyqt
https://stackoverflow.com/questions/68174615/python-multithreading-with-pypubsub-and-wx

# Known Issues
## Channel configuration
At least in MacOS BLE and serial environments, channel saving and deleting is hit-and-miss.
It might work, or it might not. This behavior also exists in the Meshtastic Python CLI,
although much less frequently than in this client.  This means it is likely a 
problem with the Meshtastic Python package.

At least in MacOS BLE environments, if you delete a channel in the middle of a 
block of channels, the topmost channel info will stay in its old slot. In other words,
you end up with two copies of the topmost channel: one in its original slot, and the other
in its new slot (where it's supposed to move to).  This is consistently replicated in the
Meshtastic Python CLI, so it is likely a bug with the Meshtastic Python package.

## GUI
Setting the color of button text does not work on all platforms, Mac being one of them.
