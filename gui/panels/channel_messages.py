import logging
import csv
from datetime import datetime

import wx
from ObjectListView3 import ObjectListView, ColumnDefn

from gui import shared
from gui.gui_events import EVT_REFRESH_PANEL, EVT_PROCESS_RECEIVED_MESSAGE, EVT_ADD_DEVICE, EVT_REMOVE_DEVICE

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)  # Set our own level separately

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
        sizer.Add(self.msg_device_picker, 0, wx.BOTTOM | wx.TOP, 2)
        sizer.Add(wx.StaticLine(self, wx.ID_ANY), 0, wx.EXPAND | wx.BOTTOM | wx.TOP, 5)

        channel_list_label = wx.StaticText(self, wx.ID_ANY, "Channels")
        self.msg_channel_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.msg_channel_list.SetMinSize(wx.Size(-1,100))
        self.msg_channel_list.SetMaxSize(wx.Size(-1,150))  # May want to adjust max size later
        self.msg_channel_list.InsertColumn(0, '#', width=20)
        self.msg_channel_list.InsertColumn(1, 'Name', width=300)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onChannelSelected, self.msg_channel_list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onChannelDeselected, self.msg_channel_list)
        sizer.Add(channel_list_label, 0, flag=wx.LEFT)
        sizer.Add(self.msg_channel_list, 1, wx.TOP | wx.BOTTOM, 5)

        self.messages_label = wx.StaticText(self, wx.ID_ANY, "Messages")
        self.messages = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.messages.SetColumns([
            ColumnDefn("Timestamp", "left", 150, "timestamp", isEditable=False),
            ColumnDefn("Sender", "left", 50, "sender", isEditable=False),
            ColumnDefn("", "left", -1, "message", isEditable=False),
        ])
        self.messages.SetEmptyListMsg("No messages")
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onMessageSelected, self.messages)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onMessageDeselected, self.messages)
        sizer.Add(self.messages_label, 0, flag=wx.LEFT)
        sizer.Add(self.messages, 4, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        send_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.send_button = wx.Button(self, wx.ID_ANY, "Send")
        self.send_text = wx.TextCtrl(self, wx.ID_ANY, style = wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_BUTTON, self.onSendButton, self.send_button)
        self.Bind(wx.EVT_TEXT_ENTER, self.onSendButton, self.send_text)
        send_sizer.Add(self.send_button, 0, flag=wx.LEFT)
        send_sizer.Add(self.send_text, 1, flag=wx.EXPAND)
        sizer.Add(send_sizer, 0, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_PROCESS_RECEIVED_MESSAGE, self.receive_message_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)
        self.Bind(EVT_REMOVE_DEVICE, self.remove_device_event)

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time
        self.selected_channel = None  # Ditto for channel last selected

    # === wxPython events

    def onDevicePickerChoice(self, evt):
        log.debug("Device picker choice event")
        self.selected_device = self.msg_device_picker.GetString(evt.GetSelection())

        # If a channel is selected, deselect it so the message list for that channel gets cleared
        selected_channel = self.msg_channel_list.GetFirstSelected()
        if selected_channel != -1:
            self.msg_channel_list.Select(selected_channel, 0)

        # Repopulate the channel list with the new device's channels
        self.msg_channel_list.DeleteAllItems()
        channel_list = shared.connected_interfaces[self.selected_device].localNode.channels
        for chan in channel_list:
            if chan.role != 0:
                self.msg_channel_list.Append((chan.index, chan.settings.name))
                log.debug(f"Adding channel {chan.settings.name} at index {chan.index}")

    def onChannelSelected(self, evt):
        log.debug("Channel selected event")
        # It seems like this could fire before the first device selection event
        selected_index = evt.GetIndex()
        if selected_index == -1:
            self.selected_channel = None
        else:
            self.selected_channel = str(self.msg_channel_list.GetItemText(selected_index, 1))
        if self.selected_channel not in shared.channel_messages[self.selected_device]:
            shared.channel_messages[self.selected_device][self.selected_channel] = []
        self.messages.SetObjects(shared.channel_messages[self.selected_device][self.selected_channel])
        if self.messages.GetItemCount() > 0:
            self.messages.EnsureVisible(self.messages.GetItemCount() - 1)

    # noinspection PyUnusedLocal
    def onChannelDeselected(self, evt):
        log.debug("Channel deselected event")
        self.messages.SetObjects([])

    # noinspection PyUnusedLocal
    def onMessageSelected(self, evt):
        log.debug("Message selected event")
        shortname = self.messages.GetItemText(self.messages.GetFirstSelected(), 1)
        longname = shared.find_longname_from_shortname(self.selected_device, shortname)
        self.messages_label.SetLabel(f"Message from {longname} ({shortname})")

    # noinspection PyUnusedLocal
    def onMessageDeselected(self, evt):
        self.messages_label.SetLabel("Messages")

    # noinspection PyUnusedLocal
    def onSendButton(self, evt):
        log.debug("Send button event")
        text_to_send = self.send_text.GetValue()
        if text_to_send is None or text_to_send.strip() == "":
            wx.RichMessageDialog(self, "No text to send",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        if self.selected_device is None or self.selected_device == "":
            wx.RichMessageDialog(self, "No device selected",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        if self.selected_channel is None:
            wx.RichMessageDialog(self, "No channel selected",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_dict = {"timestamp": now, "sender": self.selected_device, "message": text_to_send}

        channel_index = self.msg_channel_list.GetFirstSelected()
        if channel_index == -1:
            log.error("Channel list does not have a selected item, but self.selected_channel is not None")
            wx.RichMessageDialog(self, "Client logic error: no selected channel but "
                                       "self.selected_channel is not None"
                                       "\nMessage will not be sent", style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        if ("WANT_ACK_BROADCAST" in shared.config.keys()
                and shared.config["WANT_ACK_BROADCAST"].lower() in ("true", "yes")):
            want_ack = True
        else:
            want_ack = False

        log.debug(f"Sending message on channel {channel_index}, wantAck={want_ack}")
        try:
            shared.connected_interfaces[self.selected_device].sendText(text_to_send, channelIndex=channel_index,
                                                                       wantAck=want_ack)
        except Exception as e:
            log.error(f"Error sending message on channel {channel_index}: {e}")
            wx.RichMessageDialog(self, "Error sending message, see log for details",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        shared.channel_messages[self.selected_device][self.selected_channel].append(message_dict)
        self.messages.SetObjects(shared.channel_messages[self.selected_device][self.selected_channel])
        self.messages.EnsureVisible(self.messages.GetItemCount() - 1)
        self.send_text.Clear()

        log_dict = {"device": self.selected_device, "channel": self.selected_channel,
                    "timestamp": now, "sender": self.selected_device, "message": text_to_send}
        self._log_message(log_dict)

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        log.debug("Refresh panel event")
        # Repopulate channel list, in case channels were edited
        if self.selected_device:
            channel_list = shared.connected_interfaces[self.selected_device].localNode.channels
            self.msg_channel_list.DeleteAllItems()
            for chan in channel_list:
                if chan.role != 0:
                    self.msg_channel_list.Append((chan.index, chan.settings.name))
        else:
            self.msg_channel_list.DeleteAllItems()  # Make sure channel list is cleared if no selected device
        self.Layout()

    def add_device_event(self, evt):
        log.debug(f"Add device event for {evt.name}")
        device_name = evt.name
        interface = evt.interface
        channel_list = interface.localNode.channels

        # Add the new device to the device picker if it isn't already there
        index = self.msg_device_picker.FindString(device_name)
        if index == wx.NOT_FOUND:
            self.msg_device_picker.Append(device_name)

        # If this is the first device, auto-select it
        if self.msg_device_picker.GetCount() == 1:  # this is the first device, auto-select it
            self.selected_device = device_name
            self.msg_device_picker.Select(0)

        # Add the new device and channels to the channel message buffer if needed
        if device_name not in shared.channel_messages:
            shared.channel_messages[device_name] = {}
        for chan in channel_list:
            if chan.settings.name not in shared.channel_messages[device_name]:
                shared.channel_messages[device_name][chan.settings.name] = []

        # Populate the channel list
        for chan in channel_list:
            if chan.role != 0:
                self.msg_channel_list.Append((chan.index, chan.settings.name))

    def remove_device_event(self, evt):
        log.debug(f"Remove device event for {evt.name}")
        device_name = evt.name

        index = self.msg_device_picker.FindString(device_name)
        if index != wx.NOT_FOUND:
            self.msg_device_picker.Delete(index)
        if self.selected_device == device_name:
            self.selected_device = None
            self.msg_channel_list.DeleteAllItems()
            self.selected_channel = None
            self.messages.SetObjects([])

    # Channel (non-direct) message received (event sent here from pub/sub handler in main app)
    def receive_message_event(self, event):
        log.debug(f"Receive message event on device {event.device}")
        device = event.device
        channel_number = event.channel
        sender = event.sender
        timestamp = event.timestamp
        text = event.message

        # Translate channel index from message packet to channel name
        channel = self.msg_channel_list.GetItemText(int(channel_number), 1)

        if device not in shared.channel_messages:
            shared.channel_messages[device] = {}
        if channel not in shared.channel_messages[device]:
            shared.channel_messages[device][channel] = []
        message_dict = {"timestamp": timestamp, "sender": sender, "message": text}
        shared.channel_messages[device][channel].append(message_dict)
        if device == self.selected_device and channel == self.selected_channel:
            self.messages.SetObjects(shared.channel_messages[device][channel])
            self.messages.EnsureVisible(self.messages.GetItemCount() - 1)

        log_dict = {"device": device, "channel": channel, "timestamp": timestamp, "sender": sender, "message": text}
        self._log_message(log_dict)

    # === Helpers and private functions

    @staticmethod
    def _log_message(message_dict):
        log.debug("Logging message")
        with (open(shared.config.get("CHANNEL_MESSAGE_LOG", "channel-messages.csv"), "a") as lf):
            csv.DictWriter(lf, fieldnames=["device", "channel", "timestamp", "sender", "message"],
                           quoting=csv.QUOTE_ALL).writerow(message_dict)
