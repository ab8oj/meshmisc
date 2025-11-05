# meshmisc scripts
Scripts that do interesting things

* msg_forward.py - forward direct messages to email and log all messages in a file

# Platform-specific notes
## Linux
* Bluetooth Meshtastic devices are not supported on Linux systems.  `sudo apt-get install libgtk-3-dev`
## Mac OS
* As of this writing, there is a bug in the Meshtastic package that causes a hang when
disconnecting from a BLE device. At present, the only option is to force-quit the application
(control-C works if you ran the application or script from a shell)

# .env contents
APP_LOG_NAME=msg_forward.log  
MSG_LOG_NAME=messages.log  
SMTP_SERVER=\<smtp server address>  
SMTP_SENDER=\<smtp server username>  
SMTP_PASSWORD=\<smtp server password>   
EMAIL_FROM_ADDRESS=\<email-from-address>  
EMAIL_TO_ADDRESS=\<email-to-address>  
