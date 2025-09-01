import wx

class DevicesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        """
        Top of panel:
        - list of available devices on the left, with a "Discover" button and checkbokes for serial, ble, tcp
          - also a "Connect" button for each one
        - list of connected devices on the right, with "Disconnect" and "Configure" buttons for each one
          - as an alternative to the configure button, there could be a bottom grid with config options for the device
            that gets filled in when the device is highlighted
          - maybe this: channel list on the left of the bottom part, and other config buttons on the right
        """
        wx.StaticText(self, label="Devices")
