# meshmisc
Miscellaneous meshtastic utilities and applications

This is a (work in progress) simple three-layer application
framework for writing Meshtastic applications and utilities.

The three layers and their components are:

## Application / user interface layer
User-visible apps and 
utilities, such as GUI clients and utility scripts.
* msg_forward.py - forward direct messages to email and log all messages in a file

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

# .env contents
APP_LOG_NAME=msg_forward.log  
MSG_LOG_NAME=messages.log  
SMTP_SERVER=<smtp server address>  
SMTP_SENDER=<smtp server username>  
SMTP_PASSWORD=<smtp server password>   
EMAIL_FROM_ADDRESS=<email-from-address>  
EMAIL_TO_ADDRESS=<email-to-address>  