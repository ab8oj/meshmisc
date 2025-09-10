import wx
from ObjectListView3 import ObjectListView, ColumnDefn

from gui_events import EVT_REFRESH_PANEL, EVT_PROCESS_RECEIVED_MESSAGE


class ChannelMessagesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY, style=wx.LC_REPORT)
        sizer = wx.BoxSizer(wx.VERTICAL)  # Outer box

        # TODO: Add visible labels to choice boxes
        self.msg_device_picker = wx.Choice(self, wx.ID_ANY, choices=[], name="Device")
        """
        When device is selected:
        - populate channel picker and reset channel choice to none and set self.selected_device
        """
        self.msg_device_picker.SetSelection(wx.NOT_FOUND)
        sizer.Add(self.msg_device_picker, 0, flag=wx.EXPAND)

        self.msg_channel_picker = wx.Choice(self, wx.ID_ANY, choices=[], name="Channel")
        """
        When channel is selected:
        - add channel buffer if it does not exist
        - set self.selected_channel
        - self.messages.SetObjects(this channel's message dict)  Will a list work? or must it be a dict?
        """
        self.msg_channel_picker.SetSelection(wx.NOT_FOUND)
        sizer.Add(self.msg_channel_picker, 0, flag=wx.EXPAND)

        # TODO: expand to full size
        # TODO: column widths (make 'message' take up the rest of the space after sender)
        self.messages = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.messages.SetColumns([
            ColumnDefn("Timestamp", "left", -1, isEditable=False),
            ColumnDefn("Sender", "left", -1, isEditable=False),
            ColumnDefn("Message", "left", -1, isEditable=False),
        ])
        sizer.Add(self.messages, 0, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_PROCESS_RECEIVED_MESSAGE, self.receive_message_event)

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

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.Layout()

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
