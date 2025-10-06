# meshmisc
Miscellaneous meshtastic utilities and applications

This is a (work in progress) simple three-layer application
framework for writing Meshtastic applications and utilities.

The three layers and their components are:

## Application / user interface layer
User-visible apps and 
utilities, such as GUI clients and utility scripts.
* msg_forward.py - forward direct messages to email and log all messages in a file
* mesh_gui.py - Meshtastic client written in wxPython

## Management and "business logic" layer
Functions that are common
across all applications should go here, so they can be updated
in one place, rather than having to modify a fleet of apps
* mesh_managers.py
  * DeviceManager: protocol-independent functions such as "find all devices on all interfaces"

## Device and external system layer
Access to Meshtastic devices and external systems

* ble.py - Meshtastic devices via Bluetooth LE
* serial_port.py - Meshtastic devices via serial ports
* tcp.py (FUTURE) - Meshtastic devices via TCP connections
* email_interface.py - send email via SMTP over TLS

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
4. Run the app: `python ./mesh_gui.py`

# .env contents
APP_LOG_NAME=msg_forward.log  
MSG_LOG_NAME=messages.log  
CHANNEL_MESSAGE_LOG=channel-messages.csv  
DIRECT_MESSAGE_LOG=direct-messages.csv  
SMTP_SERVER=<smtp server address>  
SMTP_SENDER=<smtp server username>  
SMTP_PASSWORD=<smtp server password>   
EMAIL_FROM_ADDRESS=<email-from-address>  
EMAIL_TO_ADDRESS=<email-to-address>  

## Important note about handling Meshtastic pub/sub events
Evidently the topic subscriber functions  get *called* by the same thread that does the SendMessage, so they
execute in a Meshtastic device thread context, not in the main GUI thread. This prevents us from
directly manipulating the GUI through things like layout(). Changing values of widgets in the GUI does
seem to execute, but the updates are not seen in the GUI until the window is jiggled.
    
For this reason, we need to use wxPython events rather than pub/sub to do certain GUI things like Layout()
https://stackoverflow.com/questions/50914555/compatibility-between-pypubsub-and-pyqt
https://stackoverflow.com/questions/68174615/python-multithreading-with-pypubsub-and-wx
