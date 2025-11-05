import wx
from datetime import datetime

from ObjectListView3 import ObjectListView, ColumnDefn

from gui import shared
from gui.gui_events import (EVT_REFRESH_PANEL, EVT_ADD_DEVICE, EVT_NODE_UPDATED, EVT_CHILD_CLOSED,
                               EVT_PROCESS_RECEIVED_MESSAGE, refresh_panel, EVT_REMOVE_DEVICE, fake_device_disconnect)
from gui.panels.node_convo_frame import NodeConvoFrame


class NodesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)  # Outer box

        dev_picker_label = wx.StaticText(self, wx.ID_ANY, "Devices")
        self.msg_device_picker = wx.Choice(self, wx.ID_ANY, choices=[], name="Device",
                                           size=wx.Size(150, 20),
                                           style=wx.CB_SORT | wx.ALIGN_TOP)
        self.msg_device_picker.SetSelection(wx.NOT_FOUND)
        self.Bind(wx.EVT_CHOICE, self.onDevicePickerChoice, self.msg_device_picker)
        sizer.Add(dev_picker_label, 0, flag=wx.LEFT)
        sizer.Add(self.msg_device_picker, 0, wx.BOTTOM | wx.TOP, 2)
        sizer.Add(wx.StaticLine(self, wx.ID_ANY), 0, wx.EXPAND | wx.BOTTOM | wx.TOP, 5)

        self.node_list_label = wx.StaticText(self, wx.ID_ANY, "Nodes")
        self.node_list = ObjectListView(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.node_list.SetMinSize(wx.Size(-1, 300))
        self.node_list.SetMaxSize(wx.Size(-1, 300))
        self.node_list.SetColumns([
            ColumnDefn("Node ID", "left", 100, "nodeid", isEditable=False),
            ColumnDefn("Name", "left", 50, "name", isEditable=False),
            ColumnDefn("Long Name", "left", -1, "longname", isEditable=False, isSpaceFilling=True),
        ])
        self.node_list.SetEmptyListMsg("No nodes")
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onNodeSelected, self.node_list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onNodeDeselected, self.node_list)
        sizer.Add(self.node_list_label, 0, flag=wx.LEFT)
        sizer.Add(self.node_list, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        self.convo_button = wx.Button(self, wx.ID_ANY, "Show direct message conversation")
        self.convo_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.onConvoButton, self.convo_button)
        sizer.Add(self.convo_button, 0, wx.BOTTOM, 5)

        self.node_details_grid = wx.GridBagSizer(hgap=10, vgap=5)  # Bottom part of page: node details
        # Row 1 - model
        self.node_model_name = wx.StaticText(self, wx.ID_ANY)
        self.node_details_grid.Add(self.node_model_name, pos=(0, 0))
        # Row 2 - Battery level and voltage, channel and Tx utilization
        self.battery_info = wx.StaticText(self, wx.ID_ANY)
        self.util_info = wx.StaticText(self, wx.ID_ANY)
        self.node_details_grid.Add(self.battery_info, pos=(1, 0))
        self.node_details_grid.Add(self.util_info, pos=(1, 1))
        # Row 3 - Position
        self.last_position_time = wx.StaticText(self, wx.ID_ANY)
        self.position_info = wx.StaticText(self, wx.ID_ANY)
        self.node_details_grid.Add(self.last_position_time, pos=(2, 0))
        self.node_details_grid.Add(self.position_info, pos=(2, 1))
        # Row 4 - Hops away / SNR, last heard time
        self.hops_away_snr = wx.StaticText(self, wx.ID_ANY)
        self.last_heard_time = wx.StaticText(self, wx.ID_ANY)
        self.node_details_grid.Add(self.hops_away_snr, pos=(3, 0))
        self.node_details_grid.Add(self.last_heard_time, pos=(3, 1))
        sizer.Add(self.node_details_grid, 0, wx.EXPAND | wx.ALL, 5)

        self.reset_node_db_button = wx.Button(self, wx.ID_ANY, "Reset node database")
        self.reset_node_db_button.SetForegroundColour(wx.RED)  # Does not work on all platforms (looking at you, Mac)
        self.reset_node_db_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.onResetNodeDBButton, self.reset_node_db_button)
        bottom_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_button_sizer.Add(self.reset_node_db_button, 0, flag=wx.ALIGN_BOTTOM)
        sizer.Add(bottom_button_sizer, 1, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)
        self.Bind(EVT_REMOVE_DEVICE, self.remove_device_event)
        self.Bind(EVT_NODE_UPDATED, self.receive_node_event)
        self.Bind(EVT_CHILD_CLOSED, self.child_closed_event)
        self.Bind(EVT_PROCESS_RECEIVED_MESSAGE, self.receive_message_event)

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time
        self.selected_node = None  # Ditto for node last selected
        self.active_subpanels = []  # List of active node conversation frames that will get refreshed on new messages
        self.node_data = []  # Abbreviated node data for node list

    # === Helpers and utilities

    def _show_node_info(self, device_index):
        # TODO: Update this info once every minute or so using a timer event
        nodeid = self.node_list.GetItemText(device_index, 0)

        node = shared.connected_interfaces[self.selected_device].nodes.get(nodeid, None)
        if not node:
            self.node_model_name.SetLabel("Node not found in node database")
            return

        # Row 1
        model = node.get("user", {}).get("hwModel", "Unknown model")
        self.node_model_name.SetLabel(model)

        # Row 2
        battery_level = node.get("deviceMetrics", {}).get("batteryLevel", "?")
        battery_voltage = node.get("deviceMetrics", {}).get("voltage", "?")
        self.battery_info.SetLabel(f"Battery level: {battery_level}%, {battery_voltage}V")
        chan_util = node.get("deviceMetrics", {}).get("channelUtilization", "?")
        tx_util = node.get("deviceMetrics", {}).get("airUtilTx", "?")
        self.util_info.SetLabel(f"Channel utilization: {chan_util} Tx:{tx_util}")

        # Row 3
        last_pos = node.get("position", {}).get("time", 0)
        pos_lat = node.get("position", {}).get("latitude", 0)
        pos_lon = node.get("position", {}).get("longitude", 0)
        pos_alt = node.get("position", {}).get("altitude", 0)
        self.last_position_time.SetLabel(f"Last position time: {datetime.fromtimestamp(int(last_pos))}")
        self.position_info.SetLabel(f"Lat: {pos_lat}, Lon: {pos_lon}, Alt: {pos_alt}")

        # Row 4
        snr = node.get("snr", "N/A")
        hops_away = node.get("hopsAway", "N/A")
        last_heard = node.get("lastHeard", 0)
        self.hops_away_snr.SetLabel(f"Hops away: {hops_away}, SNR: {snr}")
        self.last_heard_time.SetLabel(f"Last heard time: {datetime.fromtimestamp(int(last_heard))}")

        self.SendSizeEvent()  # No, I don't know why I need this here but not in the device panel

    def _clear_node_info(self):
        # Since this is a sizer, it's not as simple as getting its children
        children = self.node_details_grid.GetChildren()
        for child in children:
            widget = child.GetWindow()
            if isinstance(widget, wx.StaticText):
                widget.SetLabel("")
            elif isinstance(widget, wx.TextCtrl):
                widget.Clear()

    def _populate_node_list(self):
        # If we don't have a selected device, we clearly don't need to see anything in the list
        if not self.selected_device:
            return

        # Populate the node list
        self.node_data = []
        for nodeid, data in shared.connected_interfaces[self.selected_device].nodes.items():
            node_data_row = {
                "nodeid": nodeid,
                "name": data.get("user", {}).get("shortName", "????"),
                "longname": data.get("user", {}).get("longName", "Unknown"),
            }
            self.node_data.append(node_data_row)
        self.node_list.SetObjects(self.node_data)

        # Update node count
        self.node_list_label.SetLabel(f"Nodes ({self.node_list.GetItemCount()})")
        self.Layout()

    # === wxPython events

    def onDevicePickerChoice(self, evt):
        self.selected_device = self.msg_device_picker.GetString(evt.GetSelection())
        self._populate_node_list()
        self.reset_node_db_button.Enable()

    def onNodeSelected(self, evt):
        self.selected_node = evt.GetIndex()
        self._show_node_info(self.selected_node)
        self.convo_button.Enable()

    # noinspection PyUnusedLocal
    def onNodeDeselected(self, evt):
        self._clear_node_info()
        self.convo_button.Disable()

    # noinspection PyUnusedLocal
    def onConvoButton(self, evt):
        selected_node = self.node_list.GetFirstSelected()
        node_id = self.node_list.GetItemText(selected_node, 0)
        node_name = self.node_list.GetItemText(selected_node, 1)

        # Make sure the per-node message buffer is populated enough for the conversation frame to work
        if self.selected_device not in shared.node_conversations:
            shared.node_conversations[self.selected_device] = {}
        if node_name not in shared.node_conversations[self.selected_device]:
            shared.node_conversations[self.selected_device][node_name] = []

        node_convo_frame = NodeConvoFrame(self, self.GetTopLevelParent(),
                                          shared.connected_interfaces[self.selected_device], node_name, node_id)
        self.active_subpanels.append(node_convo_frame)
        node_convo_frame.Show(True)

    # noinspection PyUnusedLocal
    def onResetNodeDBButton(self, event):
        confirm = wx.RichMessageDialog(self, f"Reset node database on device {self.selected_device}?",
                                       style=wx.OK | wx.CANCEL | wx.ICON_WARNING).ShowModal()
        if confirm == wx.ID_OK:
            shared.connected_interfaces[self.selected_device].getNode("^local").resetNodeDb()
            self.node_data = []
            self.node_list.SetObjects(self.node_data)
            # Some device types may not generate a node-down pubsub event. Assume this node just rebooted,
            # and fake the disconnect
            wx.PostEvent(self.GetTopLevelParent(),
                         fake_device_disconnect(name=self.selected_device,
                                                interface=shared.connected_interfaces[self.selected_device]))
            wx.RichMessageDialog(self, "Device will now reboot, reconnect from the Devices panel",
                                 style=wx.OK).ShowModal()

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.node_list.SetObjects(self.node_data)
        self.Layout()
        for child in self.active_subpanels:
            wx.PostEvent(child, refresh_panel())

    # noinspection PyUnusedLocal
    def add_device_event(self, evt):
        device_name = evt.name
        interface = evt.interface
        node_dict = interface.nodes

        # Add the new device to the device picker
        self.msg_device_picker.Append(device_name)
        if self.msg_device_picker.GetCount() == 1:  # this is the first device, auto-select it
            self.selected_device = device_name
            self.msg_device_picker.Select(0)  # This doesn't seem to generate a select event, so...
            self._populate_node_list()
            self.reset_node_db_button.Enable()

    def remove_device_event(self, evt):
        device_name = evt.name

        index = self.msg_device_picker.FindString(device_name)
        if index != wx.NOT_FOUND:
            self.msg_device_picker.Delete(index)
        if self.selected_device == device_name:
            self.selected_device = None
            self.node_data = []
            self.node_list.SetObjects(self.node_data)
            self.node_list_label.SetLabel("Nodes")
            self._clear_node_info()
            self.reset_node_db_button.Disable()

    # noinspection PyUnusedLocal
    def receive_node_event(self, event):
        device_name = event.device
        node_id = event.nodeid  # Could be None
        node_num = event.nodenum  # Could be None
        node = event.node  # Meshtastic.Node object
        interface = event.interface  # Not used here, just document its existence

        short_name = node.get("user", {}).get("shortName", "??")
        long_name = node.get("user", {}).get("longName", "Unknown")

        # Add to shared node database
        # For now, it's keyed by node ID for compatibility. See how many missing node IDs we get
        if node_id:
            if device_name not in shared.node_database:
                shared.node_database[device_name] = {}
            shared.node_database[device_name][node_id] = node
        else:
            # TODO: Change to logging
            print("Could not add node to shared database, no nodeID")
            print(f"Device name: {device_name}, node number: {node_num}, "
                  f"short_name: {short_name}, long_name: {long_name}")

        # Rather than fiddle around trying to see if the node data already exists in the list, just reload it
        self._populate_node_list()

        return

    # noinspection PyUnusedLocal
    def receive_message_event(self, event):
        # direct_messages panel will handle updating the shared message buffer, just tell children to refresh
        for child in self.active_subpanels:
            wx.PostEvent(child, refresh_panel())

    def child_closed_event(self, event):
        pass  # Nothing in particular to do
