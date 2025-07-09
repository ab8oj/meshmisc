# TODO: This will be where the "logic layer" lives, that can be used by a number of higher-level
#       Python applications, whether simple scripts or more complex stuff
#       Try to make it add value to the meshtastic package.

"""
Ideas for stuff to add here:
find all mesh devices on all interfaces that can be discovered or configured
    e.g. app says "go find me a device and connect to it" or "go find me all devices and let user choose"
handle the selection of which interface type (might run counter to GUI wanting control of that, though)
in general, move interface management here, leaving the apps to do simple things like send text
    and display node info.
"""

"""
Anti-ideas: what *shouldn't* go here
App layer should probably be the one to do the subscribing to the topics
"""