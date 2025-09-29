import wx
from datetime import datetime
from pubsub import pub

import shared
from mesh_managers import DeviceManager
from gui_events import (set_status_bar, EVT_REFRESH_PANEL,
                        update_connection_status, EVT_UPDATE_CONNECTION_STATUS, announce_new_device)


class DevicesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)  # outer box
        device_box = wx.BoxSizer(wx.HORIZONTAL)  # Top part of page: buttons and device list

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
        self.device_list.InsertColumn(0, 'Name', width=wx.LIST_AUTOSIZE)
        self.device_list.InsertColumn(1, 'Status', width=wx.LIST_AUTOSIZE)
        self.device_list.InsertColumn(2, 'Int', width=wx.LIST_AUTOSIZE)
        self.device_list.InsertColumn(3, 'Address', width=wx.LIST_AUTOSIZE)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onDeviceSelected, self.device_list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onDeviceDeselected, self.device_list)
        device_list_box.Add(self.device_list, 1, flag=wx.EXPAND)
        device_box.Add(device_list_box, 1, flag=wx.EXPAND)

        self.ble_text = wx.TextCtrl(self, wx.ID_ANY,
                                    "NOTE: BLE devices may take several seconds to discover and connect",
                                    style=wx.TE_READONLY)

        self.device_details_grid = wx.GridBagSizer(hgap=10, vgap=5)  # Bottom part of page: device details
        # Row 1 - device long name, model, firmware
        self.device_name = wx.StaticText(self, wx.ID_ANY)
        self.device_details_grid.Add(self.device_name, pos=(0, 0))
        self.device_model_name = wx.StaticText(self, wx.ID_ANY)
        self.device_details_grid.Add(self.device_model_name, pos=(0, 1))
        # Row 2 - Battery level and voltage, channel and Tx utilization
        self.battery_info = wx.StaticText(self, wx.ID_ANY)
        self.util_info = wx.StaticText(self, wx.ID_ANY)
        self.device_details_grid.Add(self.battery_info, pos=(1,0))
        self.device_details_grid.Add(self.util_info, pos=(1,1))
        # Row 3 - Position time and last heard time
        self.last_position_time = wx.StaticText(self, wx.ID_ANY)
        self.last_heard_time = wx.StaticText(self, wx.ID_ANY)
        self.device_details_grid.Add(self.last_position_time, pos=(2,0))
        self.device_details_grid.Add(self.last_heard_time, pos=(2,1))
        # Row 4 - Channels
        self.channel_label = wx.StaticText(self, wx.ID_ANY)
        self.channel_0 = wx.StaticText(self, wx.ID_ANY)
        self.channel_1 = wx.StaticText(self, wx.ID_ANY)
        self.channel_2 = wx.StaticText(self, wx.ID_ANY)
        self.channel_3 = wx.StaticText(self, wx.ID_ANY)
        self.channel_4 = wx.StaticText(self, wx.ID_ANY)
        self.channel_5 = wx.StaticText(self, wx.ID_ANY)
        self.channel_6 = wx.StaticText(self, wx.ID_ANY)
        self.channel_7 = wx.StaticText(self, wx.ID_ANY)
        self.device_details_grid.Add(self.channel_label, pos=(3,0), span=(8,1))
        self.device_details_grid.Add(self.channel_0, pos=(3,1))
        self.device_details_grid.Add(self.channel_1, pos=(4,1))
        self.device_details_grid.Add(self.channel_2, pos=(5,1))
        self.device_details_grid.Add(self.channel_3, pos=(6,1))
        self.device_details_grid.Add(self.channel_4, pos=(7,1))
        self.device_details_grid.Add(self.channel_5, pos=(8,1))
        self.device_details_grid.Add(self.channel_6, pos=(9,1))
        self.device_details_grid.Add(self.channel_7, pos=(10,1))

        sizer.Add(device_box, 0, flag=wx.EXPAND)
        sizer.Add(self.ble_text, 0, flag=wx.EXPAND)
        sizer.Add(self.device_details_grid, 0, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        device_box.Fit(self)

        self.device_manager = DeviceManager()
        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel)
        self.Bind(EVT_UPDATE_CONNECTION_STATUS, self.update_connection_status)

        # Non-GUI stuff
        pub.subscribe(self.onConnectionUp, "meshtastic.connection.established")
        pub.subscribe(self.onConnectionDown, "meshtastic.connection.lost")

    # === Helpers and utilities

    def _show_device_info(self, device_index):
        # TODO: Update this info once every minute or so using a timer event
        # Show device info for the device at position <index> in the device list
        # This device must already have an interface object
        device_short_name = self.device_list.GetItemText(device_index, 0)
        device_interface = shared.connected_interfaces[device_short_name]
        my_node_info = device_interface.getMyNodeInfo()

        # Row 1
        longname = my_node_info.get("user", {}).get("longName", "No name")
        model = my_node_info.get("user", {}).get("hwModel", "Unknown model")
        if hasattr(device_interface.metadata, "firmware_version"):
            firmware = device_interface.metadata.firmware_version
        else:
            firmware = "Unknown firmware version"
        self.device_name.SetLabel(longname)
        self.device_model_name.SetLabel(f"{model} {firmware}")

        # Row 2
        battery_level = my_node_info.get("deviceMetrics", {}).get("batteryLevel", "?")
        battery_voltage = my_node_info.get("deviceMetrics", {}).get("voltage", "?")
        self.battery_info.SetLabel(f"Battery level: {battery_level}%, {battery_voltage}V")
        chan_util = my_node_info.get("deviceMetrics", {}).get("channelUtilization", "?")
        tx_util = my_node_info.get("deviceMetrics", {}).get("airUtilTx", "?")
        self.util_info.SetLabel(f"Channel utilization: {chan_util} Tx:{tx_util}")

        # Row 3
        last_pos = my_node_info.get("position", {}).get("time", 0)
        last_heard = my_node_info.get("lastHeard", 0)
        self.last_position_time.SetLabel(f"Last position time: {datetime.fromtimestamp(int(last_pos))}")
        self.last_heard_time.SetLabel(f"Last heard time: {datetime.fromtimestamp(int(last_heard))}")

        # Row 4
        self.channel_label.SetLabel("Channels")
        channel_list = device_interface.localNode.channels
        self.channel_0.SetLabel(f"0: {channel_list[0].settings.name}")
        self.channel_1.SetLabel(f"1: {channel_list[1].settings.name}")
        self.channel_2.SetLabel(f"2: {channel_list[2].settings.name}")
        self.channel_3.SetLabel(f"3: {channel_list[3].settings.name}")
        self.channel_4.SetLabel(f"4: {channel_list[4].settings.name}")
        self.channel_5.SetLabel(f"5: {channel_list[5].settings.name}")
        self.channel_6.SetLabel(f"6: {channel_list[6].settings.name}")
        self.channel_7.SetLabel(f"7: {channel_list[7].settings.name}")

    def _clear_device_info(self):
        # Since this is a sizer, it's not as simple as getting its children
        children = self.device_details_grid.GetChildren()
        for child in children:
            widget = child.GetWindow()
            if isinstance(widget, wx.StaticText):
                widget.SetLabel("")
            elif isinstance(widget, wx.TextCtrl):
                widget.Clear()

    # === wxPython events

    # noinspection PyUnusedLocal
    def refresh_panel(self, event):
        self.Layout()

    def update_connection_status(self, event):
        if event.name:
            short_name = event.name
        else:
            short_name = "unknown"  # triggers status-cannot-be-updated dialog below
        status = event.status
        index = self.device_list.FindItem(-1, short_name)
        if index == -1:
            message = (f"WARNING: Device with name {short_name} was not found in the node list, "
                       f"connection status cannot be updated")
            wx.RichMessageDialog(self, message, style=wx.ICON_WARNING).ShowModal()
            return

        self.device_list.SetItem(index, 1, status)
        if self.device_list.IsSelected(index) and status == "Connected":
            self._show_device_info(index)
        self.Layout()
        return

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

        name = self.device_list.GetItemText(selected_item, 0)
        status = self.device_list.GetItemText(selected_item, 1)
        dev_type = self.device_list.GetItemText(selected_item, 2)
        address = self.device_list.GetItemText(selected_item, 3)

        if status != "Disconnected":
            wx.RichMessageDialog(self, f"Cannot connect to device {name} because its status is {status}",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return
        try:
            shared.connected_interfaces[name] = self.device_manager.connect_to_specific_device(dev_type, address)
        except Exception as e:
            wx.RichMessageDialog(self, f"Error connecting to device: {str(e)}",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        return

    # noinspection PyUnusedLocal
    def onDisconnectButton(self, event):
        selected_item = self.device_list.GetFirstSelected()
        if selected_item == -1:
            wx.RichMessageDialog(self, "A device must be selected", style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        name = self.device_list.GetItemText(selected_item, 0)
        dev_type = self.device_list.GetItemText(selected_item, 2)
        if dev_type == "ble":
            # Warn use about BLE disconnect bug (might be Mac-specific)
            wx.RichMessageDialog(self, "WARNING: BLE device disconnects hang on some platforms, "
                                       "force-quit the application if the disconnect hangs",
                                 style=wx.ICON_WARNING | wx.OK).ShowModal()
        try:
            shared.connected_interfaces[name].close()
        except Exception as e:
            wx.RichMessageDialog(self, f"Error disconnecting from device: {str(e)}",)
            return

        # Remove the old interface object but don't close the associated windows. If a reconnect happens, the
        # key (name) will still be the same, so all the windows will still match up with the new object
        shared.connected_interfaces.pop(name, None)
        return

    # noinspection PyUnusedLocal
    def onDeviceSelected(self, event):
        selected_index = event.GetIndex()
        selected_short_name = self.device_list.GetItemText(selected_index, 0)
        self.connect_button.Enable()
        self.disconnect_button.Enable()
        # We won't have an interface object for this device if it hasn't connected at least once
        if selected_short_name in shared.connected_interfaces:
            self._show_device_info(selected_index)
        return

    # noinspection PyUnusedLocal
    def onDeviceDeselected(self, event):
        self.connect_button.Disable()
        self.disconnect_button.Disable()
        self._clear_device_info()

    # === Meshtastic pub/sub topic handlers
    """
    IMPORTANT NOTE: See README.md for important details about handling Meshtastic pub/sub messages.
    """

    # noinspection PyUnusedLocal
    def onConnectionUp(self, interface):
        short_name = interface.getShortName()
        shared.connected_interfaces[short_name] = interface
        wx.PostEvent(self, update_connection_status(name=short_name, status="Connected"))
        wx.PostEvent(self.GetTopLevelParent(), set_status_bar(text=f"Connection established to {short_name}"))
        wx.PostEvent(self.GetTopLevelParent(), announce_new_device(name=short_name, interface=interface))
        return

    def onConnectionDown(self, interface):
        # TODO: Turning off a BLE device doesn't seem to publish to this topic. Why?
        # NOTE: Don't remove the interface object, so we can still reference things in it
        short_name = interface.getShortName()
        wx.PostEvent(self, update_connection_status(name=short_name, status="Disconnected"))
        wx.PostEvent(self.GetTopLevelParent(), set_status_bar(text=f"Connection lost to {short_name}"))
        return
