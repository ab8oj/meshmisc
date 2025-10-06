# "Conversation view" of direct messages between a local local_node_name and a remote node
import csv
import wx
from ObjectListView3 import ObjectListView, ColumnDefn
from datetime import datetime

import shared
from gui_events import child_closed, EVT_REFRESH_PANEL, refresh_panel, refresh_specific_panel


class NodeConvoFrame(wx.Frame):
    def __init__(self, parent, app_frame, interface, remote_node_name, remote_node_id):
        wx.Frame.__init__(self, parent, -1, f"Direct message conversation with {remote_node_name}")
        self.app_frame = app_frame
        self.interface = interface
        self.remote_node_name = remote_node_name
        self.remote_node_id = remote_node_id
        self.local_node_name = interface.getShortName()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, f"Device: {self.local_node_name}"))
        messages_label = wx.StaticText(self, wx.ID_ANY, "Messages")
        sizer.Add(messages_label, 0, flag=wx.LEFT)

        self.messages = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.messages.SetColumns([
            ColumnDefn("Timestamp", "left", 150, "timestamp", isEditable=False),
            ColumnDefn("From", "left", 50, "from", isEditable=False),
            ColumnDefn("To", "left", 50, "to", isEditable=False),
            ColumnDefn("Message", "left", -1, "message", isEditable=False, isSpaceFilling=True),
        ])
        self.messages.SetEmptyListMsg("No messages")
        self.messages.SetObjects(shared.node_conversations[self.local_node_name][self.remote_node_name],
                                 preserveSelection=True)
        sizer.Add(self.messages, 4, flag=wx.EXPAND)

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

        self.Bind(wx.EVT_CLOSE, self.closeEvent)
        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)

    # === wxPython events

    # noinspection PyUnusedLocal
    def onSendButton(self, evt):
        # TODO: Disable the Send button until and unless there is text to send
        text_to_send = self.send_text.GetValue()
        if text_to_send is None or text_to_send.strip() == "":
            wx.RichMessageDialog(self, "No text to send",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        self.interface.sendText(text_to_send, destinationId=self.remote_node_id)
        self.send_text.Clear()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_dict = {"timestamp": now, "from": self.local_node_name, "to": self.remote_node_name,
                        "message": text_to_send}
        shared.node_conversations[self.local_node_name][self.remote_node_name].append(message_dict)
        self.messages.SetObjects(shared.node_conversations[self.local_node_name][self.remote_node_name],
                                 preserveSelection=True)
        self.messages.EnsureVisible(self.messages.GetItemCount() - 1)

        shared.direct_messages[self.local_node_name].append(message_dict)
        wx.PostEvent(self.GetParent(), refresh_panel())
        wx.PostEvent(self.app_frame, refresh_specific_panel(panel_name="dm"))
        wx.PostEvent(self.app_frame, refresh_specific_panel(panel_name="node"))

        log_dict = {"device": self.local_node_name, "remote": self.remote_node_name, "timestamp": now,
                       "from": self.local_node_name, "to": self.remote_node_name, "message": text_to_send}
        self._log_message(log_dict)

        return

    @staticmethod
    def _log_message(message_dict):
        with (open(shared.config.get("DIRECT_MESSAGE_LOG", "direct-messages.csv"), "a") as lf):
            csv.DictWriter(lf, fieldnames=["device", "remote", "timestamp", "from", "to", "message"]
                           ).writerow(message_dict)

    # noinspection PyUnusedLocal
    def closeEvent(self, event):
        # Tell parent this window is closing
        wx.PostEvent(self.GetParent(), child_closed(child=self))
        self.Destroy()

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.messages.SetObjects(shared.node_conversations[self.local_node_name][self.remote_node_name],
                                 preserveSelection=True)
        self.messages.EnsureVisible(self.messages.GetItemCount() - 1)
