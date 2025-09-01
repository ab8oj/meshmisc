import wx

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
        discover_ble = wx.CheckBox(self, wx.ID_ANY, "Discover BLE")
        discover_serial = wx.CheckBox(self, wx.ID_ANY, "Discover Serial")
        discover_tcp = wx.CheckBox(self, wx.ID_ANY, "Discover TCP")
        connect_button = wx.Button(self, wx.ID_ANY, "Connect")
        disconnect_button = wx.Button(self, wx.ID_ANY, "Disconnect")
        device_button_box.Add(discover_button)
        device_button_box.Add(discover_ble)
        device_button_box.Add(discover_serial)
        device_button_box.Add(discover_tcp)
        device_button_box.Add(connect_button)
        device_button_box.Add(disconnect_button)
        device_box.Add(device_button_box)

        # TODO: Make the device list box expand to the right as frame expands
        device_list_box = wx.BoxSizer(wx.VERTICAL)  # Right side of device box: device list
        self.device_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.device_list.InsertColumn(0, 'Status')
        self.device_list.InsertColumn(1, 'Short name')
        self.device_list.InsertColumn(2, 'Long name')
        device_list_box.Add(self.device_list, 1, flag=wx.EXPAND)
        device_box.Add(device_list_box)

        self.SetSizer(device_box)
        self.SetAutoLayout(True)
        device_box.Fit(self)

class BottomPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        wx.StaticText(self, wx.ID_ANY, "Device details go here")
