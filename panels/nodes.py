import wx
from datetime import datetime

import shared
from gui_events import (EVT_REFRESH_PANEL, EVT_ADD_DEVICE, EVT_NODE_UPDATED, EVT_CHILD_CLOSED,
                        EVT_PROCESS_RECEIVED_MESSAGE, refresh_panel)
from panels.node_convo_frame import NodeConvoFrame


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
        sizer.Add(self.msg_device_picker, 0)

        self.node_list_label = wx.StaticText(self, wx.ID_ANY, "Nodes")
        self.node_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.node_list.SetMinSize(wx.Size(-1, 300))
        self.node_list.SetMaxSize(wx.Size(-1, 300))
        self.node_list.InsertColumn(0, "Node ID", width=wx.LIST_AUTOSIZE)
        self.node_list.InsertColumn(1, "Name", width=50)
        self.node_list.InsertColumn(2, "Long Name", width=400)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onNodeSelected, self.node_list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onNodeDeselected, self.node_list)
        sizer.Add(self.node_list_label, 0, flag=wx.LEFT)
        sizer.Add(self.node_list, 0, flag=wx.EXPAND)

        self.convo_button = wx.Button(self, wx.ID_ANY, "Show direct message conversation")
        self.convo_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.onConvoButton, self.convo_button)
        sizer.Add(self.convo_button, 0)

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
        sizer.Add(self.node_details_grid, 0)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)
        self.Bind(EVT_NODE_UPDATED, self.receive_node_event)
        self.Bind(EVT_CHILD_CLOSED, self.child_closed_event)
        self.Bind(EVT_PROCESS_RECEIVED_MESSAGE, self.receive_message_event)

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time
        self.selected_node = None  # Ditto for node last selected
        self.active_subpanels = []  # List of active node conversation frames that will get refreshed on new messages

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

    # === wxPython events

    def onDevicePickerChoice(self, evt):
        # Note that this also fires when the first item is added
        self.selected_device = self.msg_device_picker.GetString(evt.GetSelection())

        # Repopulate the node list with the new device's nodes
        # DeleteAllItems doesn't seem to generate a deselect event, force deselect so nodes get cleared
        selected_node = self.node_list.GetFirstSelected()
        if selected_node != -1:
            self.node_list.Select(selected_node, 0)
        self.node_list.DeleteAllItems()
        node_dict = shared.connected_interfaces[self.selected_device].nodes
        for node in node_dict:
            # TODO: change to using .get() for key error avoidance
            self.node_list.Append((node, node_dict[node]["user"]["shortName"],
                                   node_dict[node]["user"]["longName"]))

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
    def refresh_panel_event(self, event):
        self.Layout()
        for child in self.active_subpanels:
            wx.PostEvent(child, refresh_panel())

    def add_device_event(self, evt):
        device_name = evt.name
        interface = evt.interface
        node_dict = interface.nodes

        # Add the new device to the device picker
        self.msg_device_picker.Append(device_name)
        if self.msg_device_picker.GetCount() == 1:  # this is the first device, auto-select it
            self.selected_device = device_name
            self.msg_device_picker.Select(0)

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

        # Find the node in the list
        matching_list_item = self.node_list.FindItem(-1, node_id)

        # If the node is not in the list, add it. If it is, replace it
        if matching_list_item == wx.NOT_FOUND:
            self.node_list.Append((node_id, short_name, long_name))
        else:
            self.node_list.DeleteItem(matching_list_item)
            self.node_list.Append((node_id, short_name, long_name))

        # Update node count
        self.node_list_label.SetLabel(f"Nodes ({self.node_list.GetItemCount()})")
        self.Layout()

        return

    # noinspection PyUnusedLocal
    def receive_message_event(self, event):
        # direct_messages panel will handle updating the shared message buffer, just tell children to refresh
        for child in self.active_subpanels:
            wx.PostEvent(child, refresh_panel())

    def child_closed_event(self, event):
        pass  # Nothing in particular to do that
