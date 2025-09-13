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

        # TODO: set length to no more than 8 rows
        # TODO: set column widths
        # TODO: Break up channel part into channel list on the left and channel info on the right
        channel_list_label = wx.StaticText(self, wx.ID_ANY, "Channels")
        self.msg_channel_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.msg_channel_list.InsertColumn(0, '#', width=wx.LIST_AUTOSIZE)
        self.msg_channel_list.InsertColumn(1, 'Name', width=wx.LIST_AUTOSIZE)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onChannelSelected, self.msg_channel_list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onChannelDeselected, self.msg_channel_list)
        sizer.Add(channel_list_label, 0, flag=wx.LEFT)
        sizer.Add(self.msg_channel_list, 1, flag=wx.EXPAND)

        # TODO: column widths (make 'message' take up the rest of the space after sender)
        messages_label = wx.StaticText(self, wx.ID_ANY, "Messages")
        self.messages = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.messages.SetColumns([
            ColumnDefn("Timestamp", "left", -1, "timestamp", isEditable=False),
            ColumnDefn("Sender", "left", -1, "sender", isEditable=False),
            ColumnDefn("Message", "left", -1, "message", isEditable=False),
        ])
        sizer.Add(messages_label, 0, flag=wx.LEFT)
        sizer.Add(self.messages, 1, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_PROCESS_RECEIVED_MESSAGE, self.receive_message_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time
        self.selected_channel = None  # Ditto for channel last selected
        self.interfaces = {}  # key = shortname, value is an interface object
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

    def onDevicePickerChoice(self, evt):
        self.selected_device = evt.GetSelection()

        # Repopulate the channel list with the new device's channels
        self.msg_channel_list.ClearAll()
        channel_list = self.interfaces[self.selected_device].localNode.channels
        for chan in channel_list:
            if chan.role != 0:
                self.msg_channel_list.Append((chan.index, chan.settings.name))
        self.msg_channel_list.Select(0)

    # TODO NEXT: implement message display for each channel
    def onChannelSelected(self, evt):
        pass
        """
        When channel is selected:
        - add channel buffer if it does not exist
        - set self.selected_channel
        - self.messages.SetObjects(this channel's message dict)  Will a list work? or must it be a dict?
        """

    def onChannelDeselected(self, evt):
        # A channel should always be selected. wx.ListCtrl does not have a built-in way to enforce that.
        # If a channel is deselected and there's no following selection event, re-select the last one
        wx.CallAfter(self.doForcedSelection, evt.GetIndex())

    def doForcedSelection(self, sel):
        # If nothing is selected after a deselect event, re-select the last one
        if self.msg_channel_list.GetSelectedItemCount() == 0:
            self.msg_channel_list.Select(sel)

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.Layout()

    def add_device_event(self, evt):
        device_name = evt.name
        interface = evt.interface
        channel_list = interface.localNode.channels

        # Store the interface object in this panel's list of interfaces
        if device_name not in self.interfaces:
            self.interfaces[device_name] = interface

        # Add the new device to the device picker and message buffer
        self.msg_device_picker.Append(device_name)
        if device_name not in self.message_buffer:
            self.message_buffer[device_name] = {}

        # Add the channels to the message buffer
        for chan in channel_list:
            if chan.index not in self.message_buffer[device_name]:
                self.message_buffer[device_name][chan.index] = []

        # Populate the channel list and select the first channel by default
        for chan in channel_list:
            if chan.role != 0:
                self.msg_channel_list.Append((chan.index, chan.settings.name))
        self.msg_channel_list.Select(0)

    # TODO NEXT: finish this.
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
