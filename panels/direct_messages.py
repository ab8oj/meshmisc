import wx
from datetime import datetime
from ObjectListView3 import ObjectListView, ColumnDefn

import shared
from gui_events import EVT_REFRESH_PANEL, EVT_PROCESS_RECEIVED_MESSAGE, EVT_ADD_DEVICE, EVT_CHILD_CLOSED, refresh_panel
from panels.node_convo_frame import NodeConvoFrame


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
        sizer.Add(messages_label, 0, flag=wx.LEFT)

        message_button_box = wx.BoxSizer(wx.HORIZONTAL)
        self.quick_msg_button = wx.Button(self, wx.ID_ANY, "Send direct message")
        self.convo_button = wx.Button(self, wx.ID_ANY, "Show conversation")
        self.quick_msg_button.Disable()
        self.convo_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.onQuickMsgButton, self.quick_msg_button)
        self.Bind(wx.EVT_BUTTON, self.onConvoButton, self.convo_button)
        message_button_box.Add(self.quick_msg_button)
        message_button_box.Add(self.convo_button)
        sizer.Add(message_button_box, 0)

        # TODO: Change sender column to To and From columns
        self.messages = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.messages.SetColumns([
            ColumnDefn("Timestamp", "left", 150, "timestamp", isEditable=False),
            ColumnDefn("From", "left", 50, "from", isEditable=False),
            ColumnDefn("To", "left", 50, "to", isEditable=False),
            ColumnDefn("Message", "left", -1, "message", isEditable=False, isSpaceFilling=True),
        ])
        self.messages.SetEmptyListMsg("No messages")
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onMessageSelected, self.messages)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onMessageDeselected, self.messages)
        sizer.Add(self.messages, 4, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_PROCESS_RECEIVED_MESSAGE, self.receive_message_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)
        self.Bind(EVT_CHILD_CLOSED, self.child_closed_event)

        self.active_subpanels = []  # List of active node conversation frames that will get refreshed on new messages
        self.selected_device = None  # Device last selected , so we don't have to call control's method every time
        self.interfaces = {}  # key = shortname, value is an interface object

    def _find_nodeid_from_shortname(self, shortname):
        # Brute force for now: shuffle through the interface's node list looking for the shortname
        for node, node_info in self.interfaces[self.selected_device].nodes.items():
            if node_info["user"]["shortName"] == shortname:
                return node
        return None

    # === wxPython events

    def onDevicePickerChoice(self, evt):
        # Note that this also fires when the first item is added
        self.selected_device = self.msg_device_picker.GetString(evt.GetSelection())

    # noinspection PyUnusedLocal
    def onQuickMsgButton(self, evt):
        selected_item = self.messages.GetFirstSelected()
        if self.messages[selected_item]["from"] != self.selected_device:  # Remote node name could be in either column
            selected_sender = self.messages[selected_item]["from"]
        else:
            selected_sender = self.messages[selected_item]["to"]
        sender_node_id = self._find_nodeid_from_shortname(selected_sender)
        if not sender_node_id:
            wx.RichMessageDialog(self, f"Sender {selected_sender} not found in device node list, cannot send message",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        text_prompt = wx.TextEntryDialog(self, "Text to send", "caption", "", style=wx.OK | wx.CANCEL)
        text_prompt.ShowModal()
        text_to_send = text_prompt.GetValue()
        if text_to_send.strip() == "":  # No text entered or cancel was selected
            return

        self.interfaces[self.selected_device].sendText(text_to_send, destinationId=sender_node_id)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_dict = {"timestamp": now, "from": self.selected_device, "to": selected_sender,
                        "message": text_to_send}
        shared.direct_messages[self.selected_device].append(message_dict)
        self.messages.SetObjects(shared.direct_messages[self.selected_device], preserveSelection=True)
        shared.node_conversations[self.selected_device][selected_sender].append(message_dict)
        for child in self.active_subpanels:
            wx.PostEvent(child, refresh_panel())

    # noinspection PyUnusedLocal
    def onConvoButton(self, evt):
        selected_item = self.messages.GetFirstSelected()
        if self.messages[selected_item]["from"] != self.selected_device:  # Remote node name could be in either column
            selected_sender = self.messages[selected_item]["from"]
        else:
            selected_sender = self.messages[selected_item]["to"]
        sender_node_id = self._find_nodeid_from_shortname(selected_sender)
        if not sender_node_id:
            wx.RichMessageDialog(self, f"Sender {selected_sender} not found in device node list, cannot send message",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return
        node_convo_frame = NodeConvoFrame(self, self.interfaces[self.selected_device], selected_sender, sender_node_id)
        self.active_subpanels.append(node_convo_frame)
        node_convo_frame.Show(True)

    # noinspection PyUnusedLocal
    def onMessageSelected(self, evt):
        self.quick_msg_button.Enable()
        self.convo_button.Enable()

    # noinspection PyUnusedLocal
    def onMessageDeselected(self, evt):
        self.quick_msg_button.Disable()
        self.convo_button.Disable()

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.messages.SetObjects(shared.direct_messages[self.selected_device], preserveSelection=True)

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
        if device_name not in shared.direct_messages:
            shared.direct_messages[device_name] = []

    def receive_message_event(self, event):
        device = event.device
        sender = event.sender
        timestamp = event.timestamp
        text = event.message
        message_dict = {"timestamp": timestamp, "from": sender, "to": device, "message": text}

        # Add message to this panel's "all direct messages" buffer
        if device not in shared.direct_messages:
            shared.direct_messages[device] = []
        shared.direct_messages[device].append(message_dict)
        if device == self.selected_device:
            self.messages.SetObjects(shared.direct_messages[device], preserveSelection=True)

        # Add message to the shared node_conversations buffer
        if device not in shared.node_conversations:
            shared.node_conversations[device] = {}
        if sender not in shared.node_conversations[device]:
            shared.node_conversations[device][sender] = []
        shared.node_conversations[device][sender].append(message_dict)

        # Tell child windows to update themselves
        for child in self.active_subpanels:
            wx.PostEvent(child, refresh_panel())

    def child_closed_event(self, event):
        child = event.child
        if child in self.active_subpanels:
            self.active_subpanels.remove(child)
