# meshmisc
Miscellaneous meshtastic utilities and applications. Also see `README.md` in
the various subdirectories.

This is a (work in progress) simple three-layer application
framework for writing Meshtastic applications and utilities.

The three layers and their components are:

## Application / user interface layer
User-visible apps and 
utilities, such as GUI clients and utility scripts. See the `gui` and `scripts`
directories for examples.

## Management and "business logic" layer
Functions that are common
across all applications should go here, so they can be updated
in one place, rather than having to modify a fleet of apps. Currently, only
`common/mesh_managers.py` resides in this layer

## Device and external system layer
Access to Meshtastic devices and external systems. See the following files 
in the `common` directory:

* ble.py - Meshtastic devices via Bluetooth LE
* serial_port.py - Meshtastic devices via serial ports
* tcp.py (FUTURE) - Meshtastic devices via TCP connections
* email_interface.py - send email via SMTP over TLS

# Platform-specific notes
## Linux
* Bluetooth Meshtastic devices are not supported on Linux systems.
https://meshtastic.org/docs/hardware/devices/linux-native-hardware/ `sudo apt-get install libgtk-3-dev`
## Mac OS
* As of this writing, there is a bug in the Meshtastic package that causes a hang when
disconnecting from a BLE device. At present, the only option is to force-quit the application
(control-C works if you ran the application or script from a shell)
