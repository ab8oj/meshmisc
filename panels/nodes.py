import wx

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

        node_list_label = wx.StaticText(self, wx.ID_ANY, "Nodes")
        self.node_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.node_list.SetMinSize(wx.Size(-1, 100))
        self.node_list.SetMaxSize(wx.Size(-1, 150))
        self.node_list.InsertColumn(0, "Node ID", width=wx.LIST_AUTOSIZE)
        self.node_list.InsertColumn(1, "Name", width=50)
        self.node_list.InsertColumn(2, "Long Name", width=400)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onNodeSelected, self.node_list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onNodeDeselected, self.node_list)
        sizer.Add(node_list_label, 0, flag=wx.LEFT)
        sizer.Add(self.node_list, 1, flag=wx.EXPAND)

        self.convo_button = wx.Button(self, wx.ID_ANY, "Show direct message conversation")
        self.convo_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.onConvoButton, self.convo_button)
        sizer.Add(self.convo_button, 0)

        self.node_info_placeholder = wx.StaticText(self, wx.ID_ANY, "Node info goes here, grid sizer?")
        sizer.Add(self.node_info_placeholder, 0, flag=wx.EXPAND)

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
        self.node_info_placeholder.SetLabel(f"Node info for {self.selected_node}")
        self.convo_button.Enable()

    # noinspection PyUnusedLocal
    def onNodeDeselected(self, evt):
        self.node_info_placeholder.SetLabel(f"Cleared node info for {self.selected_node}")
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

        # Populate the node list
        for node in node_dict:
            # TODO: change to using .get() for key error avoidance
            self.node_list.Append((node, node_dict[node]["user"]["shortName"],
                                   node_dict[node]["user"]["longName"]))

    # noinspection PyUnusedLocal
    def receive_node_event(self, event):
        # TODO: Doesn't look like we get an immediate node change event on a name change, dig deeper
        # TODO: change to using .get() for key error avoidance
        node = event.node
        interface = event.interface  # Not used here, just document its existence

        node_id = node["user"]["id"]
        short_name = node["user"]["shortName"]
        long_name = node["user"]["longName"]
        matching_list_item = self.node_list.FindItem(-1, node_id)

        # If the node is not in the list, add it. If it is, update it if shortname or longname has changed
        if matching_list_item == wx.NOT_FOUND:
            self.node_list.Append((node_id, short_name, long_name))
        else:
            list_shortname = self.node_list.GetItem(matching_list_item, 1)
            list_longname = self.node_list.GetItem(matching_list_item, 2)
            if list_shortname != short_name or list_longname != long_name:
                self.node_list.DeleteItem(matching_list_item)
                self.node_list.Append((node_id, short_name, long_name))
            # If the node is currently selected, update the node info the easy way: deselect and reselect it
            # This will cause a re-read of that node's info from the selected device
            if self.node_list.IsSelected(matching_list_item):
                self.node_list.Select(matching_list_item, 0)
                self.node_list.Select(matching_list_item, 1)

        return

    # noinspection PyUnusedLocal
    def receive_message_event(self, event):
        # direct_messages panel will handle updating the shared message buffer, just tell children to refresh
        for child in self.active_subpanels:
            wx.PostEvent(child, refresh_panel())

    def child_closed_event(self, event):
        pass  # Nothing in particular to do that
