import wx
from ObjectListView3 import ObjectListView, ColumnDefn

from gui_events import EVT_REFRESH_PANEL, EVT_PROCESS_RECEIVED_MESSAGE, EVT_ADD_DEVICE

class DirectMessagesPanel(wx.Panel):
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

        messages_label = wx.StaticText(self, wx.ID_ANY, "Messages")
        self.messages = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.messages.SetColumns([
            ColumnDefn("Timestamp", "left", 150, "timestamp", isEditable=False),
            ColumnDefn("Sender", "left", 50, "sender", isEditable=False),
            ColumnDefn("Message", "left", -1, "message", isEditable=False, isSpaceFilling=True),
        ])
        self.messages.SetEmptyListMsg("No messages")
        sizer.Add(messages_label, 0, flag=wx.LEFT)
        sizer.Add(self.messages, 4, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_PROCESS_RECEIVED_MESSAGE, self.receive_message_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time
        self.interfaces = {}  # key = shortname, value is an interface object
        self.message_buffer = {}
        """
        message_buffer[devicename] is a list of messages:
        {devicename:[           
            {"Timestamp": timestamp,
             "Sender": sender,
             "Message": message}
            ]
        }
        """

    # === wxPython events

    def onDevicePickerChoice(self, evt):
        # Note that this also fires when the first item is added
        self.selected_device = self.msg_device_picker.GetString(evt.GetSelection())

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.Layout()

    def add_device_event(self, evt):
        device_name = evt.name
        interface = evt.interface

        # Store the interface object in this panel's list of interfaces
        if device_name not in self.interfaces:
            self.interfaces[device_name] = interface

        # Add the new device to the device picker and message buffer
        self.msg_device_picker.Append(device_name)
        if self.msg_device_picker.GetCount() == 1:  # this is the first device, auto-select it
            self.selected_device = device_name
            self.msg_device_picker.Select(0)
        if device_name not in self.message_buffer:
            self.message_buffer[device_name] = []

    def receive_message_event(self, event):
        # TODO: Add message to the new per-sender message buffer, to support sender conversations
        #   Which means sent direct messages will also have to go there, remember to do that as well
        device = event.device
        sender = event.sender
        timestamp = event.timestamp
        text = event.message
        if device not in self.message_buffer:
            self.message_buffer[device] = []
        message_dict = {"timestamp": timestamp, "sender": sender, "message": text}
        self.message_buffer[device].append(message_dict)
        if device == self.selected_device:
            self.messages.SetObjects(self.message_buffer[device])
