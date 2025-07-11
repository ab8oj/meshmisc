# TODO: This will be where the "logic layer" lives, that can be used by a number of higher-level
#       Python applications, whether simple scripts or more complex stuff
#       Try to make it add value to the meshtastic package.

"""
Ideas for stuff to add here:
in general, move interface management here, leaving the apps to do simple things like send text
    and display node info.
    class interfaceManager
        interface - maybe a dict if we support multiple interfaces - all the active interfaces
            then a caller can do something like: im=interfaceManager(), im.interface["OJB1"].sendText("foo")
            include "connected" key to show connection state (take that, global variable!)
        interface_types - list of supported interface types e.g. ["ble", "rest", "serial"]
        methods for:
            getting all available interfaces (optionally a specific type)
            connect to a specific interface (pass in what, the address or short name or ?)
            connect to the first available device on a given interface type (might only work for ble?)
            connect to the first available device on all interface types, given a specific order of types

"""

"""
Anti-ideas: what *shouldn't* go here
App layer should probably be the one to do the subscribing to the topics
"""
