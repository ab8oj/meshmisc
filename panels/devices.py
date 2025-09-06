import wx
from pubsub import pub

from mesh_managers import DeviceManager


class DevicesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)  # outer box
        device_box = wx.BoxSizer(wx.HORIZONTAL)  # Top part: buttons and device list

        device_button_box = wx.BoxSizer(wx.VERTICAL)  # Left side of device box: buttons
        discover_button = wx.Button(self, wx.ID_ANY, "Discover")
        self.discover_ble = wx.CheckBox(self, wx.ID_ANY, "Discover BLE")
        self.discover_serial = wx.CheckBox(self, wx.ID_ANY, "Discover Serial")
        self.discover_tcp = wx.CheckBox(self, wx.ID_ANY, "Discover TCP")
        self.connect_button = wx.Button(self, wx.ID_ANY, "Connect")
        self.disconnect_button = wx.Button(self, wx.ID_ANY, "Disconnect")
        self.connect_button.Disable()
        self.disconnect_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.onDiscoverButton, discover_button)
        self.Bind(wx.EVT_BUTTON, self.onConnectButton, self.connect_button)
        self.Bind(wx.EVT_BUTTON, self.onDisconnectButton, self.disconnect_button)
        device_button_box.Add(discover_button)
        device_button_box.Add(self.discover_ble)
        device_button_box.Add(self.discover_serial)
        device_button_box.Add(self.discover_tcp)
        device_button_box.Add(self.connect_button)
        device_button_box.Add(self.disconnect_button)
        device_box.Add(device_button_box)

        device_list_box = wx.BoxSizer(wx.VERTICAL)  # Right side of device box: device list
        self.device_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.device_list.InsertColumn(0, 'Name')
        self.device_list.InsertColumn(1, 'Status')
        self.device_list.InsertColumn(2, 'Type')
        self.device_list.InsertColumn(3, 'Address')
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onDeviceSelected, self.device_list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onDeviceDeselected, self.device_list)
        device_list_box.Add(self.device_list, 1, flag=wx.EXPAND)
        device_box.Add(device_list_box, 1, flag=wx.EXPAND)

        device_details_box = wx.BoxSizer(wx.HORIZONTAL)  # Bottom part: device information
        self.temp_text = wx.TextCtrl(self, wx.ID_ANY, "Device information goes here",
                                     style=wx.TE_READONLY)
        device_details_box.Add(self.temp_text, 1, flag=wx.EXPAND)

        sizer.Add(device_box, 0, flag=wx.EXPAND)
        sizer.Add(device_details_box, 0, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        device_box.Fit(self)

        self.device_manager = DeviceManager()
        pub.subscribe(self.onConnectionUp, "meshtastic.connection.established")
        pub.subscribe(self.onConnectionDown, "meshtastic.connection.lost")

    # noinspection PyUnusedLocal
    def onDiscoverButton(self, event):
        # TODO: Find a way to make a "busy note" work on Mac
        # TODO: preserve connection status for connected devices or don't allow rediscover if any are connected
        device_types = []
        if self.discover_ble.IsChecked():
            device_types.append("ble")
        if self.discover_tcp.IsChecked():
            device_types.append("tcp")
        if self.discover_serial.IsChecked():
            device_types.append("serial")
        if not device_types:
            wx.RichMessageDialog(self, "At least one device type must be checked",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        discovered_devices = []
        try:
            discovered_devices = self.device_manager.find_all_available_devices(device_types)
        except Exception as e:
            wx.RichMessageDialog(self, f"Error discovering devices: {str(e)}", style=wx.OK | wx.ICON_ERROR).ShowModal()
        finally:
            if not discovered_devices:
                return

        # TODO: How will the split of name work out for serial and TCP devices?
        for dev_type, address, name in discovered_devices:
            self.device_list.Append((name.split("_")[0], "Disconnected", dev_type, address))
            for col in range(self.device_list.GetColumnCount()):
                self.device_list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
            self.Layout()  # Columns don't resize until window is jiggled

        return

    # noinspection PyUnusedLocal
    def onConnectButton(self, event):
        # TODO: Deal with messages to stdout from mesh manager
        # TODO: Disallow reconnection to already-connected device (and handle failed disconnect somehow)
        selected_item = self.device_list.GetFirstSelected()
        if selected_item == -1:
            wx.RichMessageDialog(self, "A device must be selected", style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        dev_type = self.device_list.GetItemText(selected_item, 2)
        address = self.device_list.GetItemText(selected_item, 3)
        try:
            device_interface = self.device_manager.connect_to_specific_device(dev_type, address)
        except Exception as e:
            wx.RichMessageDialog(self, f"Error connecting to device: {str(e)}",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        self.temp_text.SetLabel("Connection pending")

        return

    # noinspection PyUnusedLocal
    def onDisconnectButton(self, event):
        # TODO: go implement disconnect_from_specific_device, remembering the BLE disconnect bug
        selected_item = self.device_list.GetFirstSelected()
        if selected_item == -1:
            wx.RichMessageDialog(self, "A device must be selected", style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        address = self.device_list.GetItemText(selected_item, 3)
        try:
            # TODO: Need to implement this in ble.py
            self.device_manager.disconnect_from_specific_device(address)
        except Exception as e:
            wx.RichMessageDialog(self, f"Error disconnecting from device: {str(e)}",)
            return

    # noinspection PyUnusedLocal
    def onDeviceSelected(self, event):
        self.connect_button.Enable()
        self.disconnect_button.Enable()
        return

    # noinspection PyUnusedLocal
    def onDeviceDeselected(self, event):
        self.connect_button.Disable()
        self.disconnect_button.Disable()

    # noinspection PyUnusedLocal
    def onConnectionUp(self, interface):
        # TODO: Connection status does not update until window is manipulated
        # TODO: Trying to do layout() in here or "widget changed" handler crashes w/thread error
        short_name = interface.getShortName()
        index = self.device_list.FindItem(-1, short_name)
        if index == -1:
            message = (f"WARNING: Device with address {short_name} was not found in the node list, "
                       f"connection status cannot be updated")
            wx.RichMessageDialog(self, message, style=wx.ICON_WARNING).ShowModal()
        else:
            self.device_list.SetItem(index, 1, "Connected")
        self.temp_text.SetLabel("Device informtion still goes here ")

        return

    def onConnectionDown(self, interface):
        # TODO: Turning off a BLE device doesn't seem to publish to this topic. Why?
        short_name = interface.getShortName()
        index = self.device_list.FindItem(-1, short_name)
        if index == -1:
            message = (f"WARNING: Device with address {short_name} was not found in the node list, "
                       f"connection status cannot be updated")
            wx.RichMessageDialog(self, message, style=wx.ICON_WARNING).ShowModal()
        else:
            self.device_list.SetItem(index, 1, "Disconnected")
        return
