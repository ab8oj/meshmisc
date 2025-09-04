import wx
from pubsub import pub

from mesh_managers import DeviceManager


class DevicesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)

        splitter = wx.SplitterWindow(self, wx.ID_ANY)
        top_panel = TopPanel(splitter)
        bottom_panel = BottomPanel(splitter)
        splitter.SplitHorizontally(top_panel, bottom_panel)
        splitter.SetMinimumPaneSize(20)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)


class TopPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        device_box = wx.BoxSizer(wx.HORIZONTAL)

        device_button_box = wx.BoxSizer(wx.VERTICAL)  # Left side of device box: buttons that do things
        discover_button = wx.Button(self, wx.ID_ANY, "Discover")
        self.discover_ble = wx.CheckBox(self, wx.ID_ANY, "Discover BLE")
        self.discover_serial = wx.CheckBox(self, wx.ID_ANY, "Discover Serial")
        self.discover_tcp = wx.CheckBox(self, wx.ID_ANY, "Discover TCP")
        connect_button = wx.Button(self, wx.ID_ANY, "Connect")
        disconnect_button = wx.Button(self, wx.ID_ANY, "Disconnect")
        self.Bind(wx.EVT_BUTTON, self.onDiscoverButton, discover_button)
        self.Bind(wx.EVT_BUTTON, self.onConnectButton, connect_button)
        self.Bind(wx.EVT_BUTTON, self.onDisconnectButton, disconnect_button)
        device_button_box.Add(discover_button)
        device_button_box.Add(self.discover_ble)
        device_button_box.Add(self.discover_serial)
        device_button_box.Add(self.discover_tcp)
        device_button_box.Add(connect_button)
        device_button_box.Add(disconnect_button)
        device_box.Add(device_button_box)

        # TODO: Make the device list box expand to the right as frame expands
        device_list_box = wx.BoxSizer(wx.VERTICAL)  # Right side of device box: device list
        self.device_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.device_list.InsertColumn(0, 'Name')
        self.device_list.InsertColumn(1, 'Status')
        self.device_list.InsertColumn(2, 'Type')
        self.device_list.InsertColumn(3, 'Address')
        self.device_list_index = 0  # Start with 0 items -- do I really need this?
        device_list_box.Add(self.device_list, 1, flag=wx.EXPAND)
        device_box.Add(device_list_box)

        self.SetSizer(device_box)
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
            self.device_list_index = +1

        return

    # noinspection PyUnusedLocal
    def onConnectButton(self, event):
        # TODO: Can connect button be disabled until a device is highlighted?
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


    def onConnectionUp(self, interface):
        short_name = interface.getShortName()
        message = f"Connection established on interface {short_name}"
        pub.sendMessage("mainframe.changeStatusBar", status_text=message)
        index = self.device_list.FindItem(-1, short_name)
        if index == -1:
            message = (f"WARNING: Device with address {short_name} was not found in the node list, "
                       f"connection status cannot be updated")
            pub.sendMessage("mainframe.changeStatusBar", status_text=message)
        else:
            self.device_list.SetItem(index, 1, "Connected")
        return

    def onConnectionDown(self, interface):
        # TODO: Turning off a BLE device doesn't seem to publish to this topic. Why?
        short_name = interface.getShortName()
        message = f"Connection lost on interface {short_name}"
        pub.sendMessage("mainframe.changeStatusBar", status_text=message)
        index = self.device_list.FindItem(-1, short_name)
        if index == -1:
            message = (f"WARNING: Device with address {short_name} was not found in the node list, "
                       f"connection status cannot be updated")
            pub.sendMessage("mainframe.changeStatusBar", status_text=message)
        else:
            self.device_list.SetItem(index, 1, "Disconnected")
        return


class BottomPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        wx.StaticText(self, wx.ID_ANY, "Device details go here")
