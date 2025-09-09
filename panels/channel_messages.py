import wx
from ObjectListView3 import ObjectListView, ColumnDefn

from gui_events import EVT_REFRESH_PANEL


class ChannelMessagesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY, style=wx.LC_REPORT)
        sizer = wx.BoxSizer(wx.VERTICAL)  # Outer box

        # TODO: Add visible labels to choice boxes
        self.msg_device_picker = wx.Choice(self, wx.ID_ANY, choices=[], name="Device")
        """
        When device is selected:
        - populate channel picker and reset channel choice to none and set self.selected_node
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
        # TODO: column widths (make 'message' take up the rest of the space after timestamp)
        self.messages = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.messages.SetColumns([
            ColumnDefn("Timestamp", "left", -1, isEditable=False),
            ColumnDefn("Message", "left", -1, isEditable=False),
        ])
        sizer.Add(self.messages, 0, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        """
        Picture this:
        main program gets message events
        message event handler:
        - uses an event to send direct messages to direct msg panel
        - used an event to send channel messages to channel msg panel
        - event:    fromnode=node coming from, timestamp=timestamp received by device, not by client app
        -           message=message text, channel=channel
        receiving panel:
        - puts message into backing store e.g. messages[node][channel]  or direct_messages[node][fromnode]
        """

        """
        Backing store: 
        messages[nodename][channel] is a list of {timestamp: ts, message: text}
        
        {nodename:
            {channel:[           
                {"timestamp": timestamp,
                 "message": message}
            ]}
        }
        """

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)

        self.selected_node = None
        self.selected_channel = None
        self.message_buffer = {}

    # === wxPython events

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.Layout()

    # Channel (non-direct) message received
    def receive_message_event(self, event):
        node = event.node
        channel = event.channel
        timestamp = event.timestamp
        text = event.message
        if not node or not channel:
            # TODO: log the error
            return
        if node not in self.message_buffer:
            self.message_buffer[node] = {}
        if channel not in self.message_buffer[node]:
            self.message_buffer[node][channel] = []
        message_dict = {"timestamp": timestamp, "message": text}
        self.message_buffer[node][channel].append(message_dict)
        if node == self.selected_node and channel == self.selected_channel:
            self.messages.SetObjects(self.message_buffer[node][channel])
