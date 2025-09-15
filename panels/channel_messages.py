from datetime import datetime

import wx
from ObjectListView3 import ObjectListView, ColumnDefn

from gui_events import EVT_REFRESH_PANEL, EVT_PROCESS_RECEIVED_MESSAGE, EVT_ADD_DEVICE

class ChannelMessagesPanel(wx.Panel):
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

        channel_list_label = wx.StaticText(self, wx.ID_ANY, "Channels")
        self.msg_channel_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.msg_channel_list.SetMinSize(wx.Size(-1,100))
        self.msg_channel_list.SetMaxSize(wx.Size(-1,150))  # May want to adjust max size later
        self.msg_channel_list.InsertColumn(0, '#', width=20)
        self.msg_channel_list.InsertColumn(1, 'Name', width=300)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onChannelSelected, self.msg_channel_list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onChannelDeselected, self.msg_channel_list)
        sizer.Add(channel_list_label, 0, flag=wx.LEFT)
        sizer.Add(self.msg_channel_list, 1)

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

        send_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.send_button = wx.Button(self, wx.ID_ANY, "Send")
        self.send_text = wx.TextCtrl(self, wx.ID_ANY)
        self.Bind(wx.EVT_BUTTON, self.onSendButton, self.send_button)
        send_sizer.Add(self.send_button, 0, flag=wx.LEFT)
        send_sizer.Add(self.send_text, 1, flag=wx.EXPAND)
        sizer.Add(send_sizer, 0, flag=wx.EXPAND)

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
        message_buffer[devicename][channel] is a list of messages: 
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
        # TODO: How to handle channels with still-unread messages
        # Note that this also fires when the first item is added
        self.selected_device = self.msg_device_picker.GetString(evt.GetSelection())

        # Repopulate the channel list with the new device's channels
        # DeleteAllItems doesn't seem to generate a deselect event, force deselect so messages get cleared
        selected_channel = self.msg_channel_list.GetFirstSelected()
        if selected_channel != -1:
            self.msg_channel_list.Select(selected_channel, 0)
        self.msg_channel_list.DeleteAllItems()
        channel_list = self.interfaces[self.selected_device].localNode.channels
        for chan in channel_list:
            if chan.role != 0:
                self.msg_channel_list.Append((chan.index, chan.settings.name))

    def onChannelSelected(self, evt):
        # TODO: un-highlight the channel when selected
        # It seems like this could fire before the first device selection event
        self.selected_channel = evt.GetIndex()
        if self.selected_channel not in self.message_buffer[self.selected_device]:
            self.message_buffer[self.selected_device][self.selected_channel] = []
        self.messages.SetObjects(self.message_buffer[self.selected_device][self.selected_channel])

    # noinspection PyUnusedLocal
    def onChannelDeselected(self, evt):
        self.messages.SetObjects([])

    # noinspection PyUnusedLocal
    def onSendButton(self, evt):
        # TODO: Disable the Send button until and unless device and channel are selected and there is text to send
        text_to_send = self.send_text.GetValue()
        if text_to_send is None or text_to_send.strip() == "":
            wx.RichMessageDialog(self, "No text to send",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        if self.selected_device is None or self.selected_device == "":
            wx.RichMessageDialog(self, "No device selected",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        if self.selected_channel is None or self.selected_channel == -1:
            wx.RichMessageDialog(self, "No channel selected",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        channel_index = int(self.msg_channel_list.GetItemText(self.selected_channel, 0))
        self.interfaces[self.selected_device].sendText(text_to_send, channelIndex=channel_index)
        self.message_buffer[self.selected_device][self.selected_channel].append(
            {"timestamp": now, "sender": self.selected_device, "message": text_to_send})
        self.messages.SetObjects(self.message_buffer[self.selected_device][self.selected_channel])
        self.send_text.Clear()

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
        if self.msg_device_picker.GetCount() == 1:  # this is the first device, auto-select it
            self.selected_device = device_name
            self.msg_device_picker.Select(0)
        if device_name not in self.message_buffer:
            self.message_buffer[device_name] = {}

        # Add the channels to the message buffer
        for chan in channel_list:
            if chan.index not in self.message_buffer[device_name]:
                self.message_buffer[device_name][chan.index] = []

        # Populate the channel list
        for chan in channel_list:
            if chan.role != 0:
                self.msg_channel_list.Append((chan.index, chan.settings.name))

    # Channel (non-direct) message received (event sent here from pub/sub handler in main app)
    def receive_message_event(self, event):
        # TODO: Highlight the channel that got the message
        device = event.device
        channel = event.channel
        sender = event.sender
        timestamp = event.timestamp
        text = event.message
        if device not in self.message_buffer:
            self.message_buffer[device] = {}
        if channel not in self.message_buffer[device]:
            self.message_buffer[device][channel] = []
        message_dict = {"timestamp": timestamp, "sender": sender, "message": text}
        self.message_buffer[device][channel].append(message_dict)
        if device == self.selected_device and channel == self.selected_channel:
            self.messages.SetObjects(self.message_buffer[device][channel])
