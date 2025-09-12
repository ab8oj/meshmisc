import wx
from ObjectListView3 import ObjectListView, ColumnDefn

from gui_events import EVT_REFRESH_PANEL, EVT_PROCESS_RECEIVED_MESSAGE, EVT_ADD_DEVICE

class ChannelMessagesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)  # Outer box

        dev_picker_label = wx.StaticText(self, wx.ID_ANY, "Devices")
        self.msg_device_picker = wx.Choice(self, wx.ID_ANY, choices=[], name="Device", style=wx.CB_SORT)
        self.msg_device_picker.SetSelection(wx.NOT_FOUND)
        self.Bind(wx.EVT_CHOICE, self.onDevicePickerChoice, self.msg_device_picker)
        sizer.Add(dev_picker_label, 0, flag=wx.LEFT)
        sizer.Add(self.msg_device_picker, 0, flag=wx.EXPAND)

        channel_picker_label = wx.StaticText(self, wx.ID_ANY, "Channels")
        self.msg_channel_picker = wx.Choice(self, wx.ID_ANY, choices=[], name="Channel", style=wx.CB_SORT)
        self.msg_channel_picker.SetSelection(wx.NOT_FOUND)
        self.Bind(wx.EVT_CHOICE, self.onChannelPickerChoice, self.msg_channel_picker)
        sizer.Add(channel_picker_label, 0, flag=wx.LEFT)
        sizer.Add(self.msg_channel_picker, 0, flag=wx.EXPAND)

        # TODO: column widths (make 'message' take up the rest of the space after sender)
        self.messages = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.messages.SetColumns([
            ColumnDefn("Timestamp", "left", -1, "timestamp", isEditable=False),
            ColumnDefn("Sender", "left", -1, "sender", isEditable=False),
            ColumnDefn("Message", "left", -1, "message", isEditable=False),
        ])
        sizer.Add(self.messages, 1, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_PROCESS_RECEIVED_MESSAGE, self.receive_message_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time
        self.selected_channel = None  # Ditto for channel last selected
        self.message_buffer = {}
        """
        message_buffer[devicename][channel] is a list of messages: {timestamp: ts, message: text}
        
        {devicename:
            {channel number:[           
                {"Timestamp": timestamp,
                 "Sender": sender,
                 "Message": message}
                ]
            }
        }
        """

    # === wxPython events

    # TODO: Must move device info to top level so all the subpanels can get to it
    # TODO: with one node, when device is reselected, device list goes blank
    def onDevicePickerChoice(self, evt):
        self.selected_device = evt.GetSelection()
        self.msg_channel_picker.Clear()
        # get channels
        # use Append()
        self.msg_channel_picker.SetSelection(wx.NOT_FOUND)

    def onChannelPickerChoice(self, evt):
        self.selected_channel = evt.GetSelection()
        """
        When channel is selected:
        - add channel buffer if it does not exist
        - set self.selected_channel
        - self.messages.SetObjects(this channel's message dict)  Will a list work? or must it be a dict?
        """

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.Layout()

    def add_device_event(self, evt):
        self.msg_device_picker.Append(evt.name)

    # Channel (non-direct) message received (event sent here from pub/sub handler in main app)
    def receive_message_event(self, event):
        node = event.node
        channel = event.channel
        sender = event.sender
        timestamp = event.timestamp
        text = event.message
        if node not in self.message_buffer:
            self.message_buffer[node] = {}
        if channel not in self.message_buffer[node]:
            self.message_buffer[node][channel] = []
        message_dict = {"timestamp": timestamp, "sender": sender, "message": text}
        self.message_buffer[node][channel].append(message_dict)
        # if node == self.selected_device and channel == self.selected_channel:
        self.messages.SetObjects(self.message_buffer[node][channel])
