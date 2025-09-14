import wx

from gui_events import EVT_REFRESH_PANEL, EVT_ADD_DEVICE

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

        self.node_info_placeholder = wx.StaticText(self, wx.ID_ANY, "Node info goes here, grid sizer?")
        sizer.Add(self.node_info_placeholder, 0, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time
        self.selected_node = None  # Ditto for node last selected
        self.interfaces = {}  # key = shortname, value is an interface object

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
        node_dict = self.interfaces[self.selected_device].nodes
        for node in node_dict:
            # TODO: change to using .get() for key error avoidance
            self.node_list.Append((node, node_dict[node]["user"]["shortName"],
                                   node_dict[node]["user"]["longName"]))

    def onNodeSelected(self, evt):
        self.selected_node = evt.GetIndex()
        self.node_info_placeholder.SetLabel(f"Node info for {self.selected_node}")

    # noinspection PyUnusedLocal
    def onNodeDeselected(self, evt):
        self.node_info_placeholder.SetLabel(f"Cleared node info for {self.selected_node}")

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.Layout()

    def add_device_event(self, evt):
        device_name = evt.name
        interface = evt.interface
        node_dict = interface.nodes

        # Store the interface object in this panel's list of interfaces
        if device_name not in self.interfaces:
            self.interfaces[device_name] = interface

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

    def receive_node_event(self, event):
        # *** Add node message pubsub handler in main app and dispatch it here, interface and maybe the name
        # *** Make sure node doesn't already exist before adding it to the node list
        pass
