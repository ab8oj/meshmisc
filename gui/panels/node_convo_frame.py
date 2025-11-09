# "Conversation view" of direct messages between a local local_node_name and a remote node
import logging
import csv
import wx
from ObjectListView3 import ObjectListView, ColumnDefn
from datetime import datetime

from gui import shared
from gui.gui_events import child_closed, EVT_REFRESH_PANEL, refresh_panel, refresh_specific_panel

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)  # Set our own level separately


class NodeConvoFrame(wx.Frame):
    def __init__(self, parent, app_frame, interface, remote_node_name, remote_node_id):
        wx.Frame.__init__(self, parent, -1, f"Direct message conversation with {remote_node_name}")
        self.app_frame = app_frame
        self.interface = interface
        self.remote_node_name = remote_node_name
        self.remote_node_id = remote_node_id
        self.remote_long_name = interface.nodes[remote_node_id].get("user", {}).get("longName", None)
        self.local_node_name = interface.getShortName()
        self.local_long_name = interface.getLongName()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, f"Device: {self.local_long_name} ({self.local_node_name})"),
                  0, wx.BOTTOM | wx.LEFT, 3)
        sizer.Add(wx.StaticText(self, -1, f"Remote: {self.remote_long_name} ({self.remote_node_name})"),
                  0, wx.BOTTOM | wx.LEFT, 5)
        messages_label = wx.StaticText(self, wx.ID_ANY, "Messages")
        sizer.Add(messages_label, 0, wx.LEFT | wx.BOTTOM | wx.LEFT, 5)

        self.messages = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.messages.SetColumns([
            ColumnDefn("Timestamp", "left", 150, "timestamp", isEditable=False),
            ColumnDefn("From", "left", 50, "from", isEditable=False),
            ColumnDefn("To", "left", 50, "to", isEditable=False),
            ColumnDefn("", "left", -1, "message", isEditable=False),
        ])
        self.messages.SetEmptyListMsg("No messages")
        self.messages.SetObjects(shared.node_conversations[self.local_node_name][self.remote_node_name],
                                 preserveSelection=True)
        sizer.Add(self.messages, 4, wx.EXPAND)

        send_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.send_button = wx.Button(self, wx.ID_ANY, "Send")
        self.send_text = wx.TextCtrl(self, wx.ID_ANY, style = wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_BUTTON, self.onSendButton, self.send_button)
        self.Bind(wx.EVT_TEXT_ENTER, self.onSendButton, self.send_text)
        send_sizer.Add(self.send_button, 0, flag=wx.LEFT)
        send_sizer.Add(self.send_text, 1, flag=wx.EXPAND)
        sizer.Add(send_sizer, 0, flag=wx.EXPAND)

        self.SetSizerAndFit(sizer)
        self.SetAutoLayout(True)

        self.Bind(wx.EVT_CLOSE, self.closeEvent)
        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)

    # === wxPython events

    # noinspection PyUnusedLocal
    def onSendButton(self, evt):
        log.debug("Send button event")
        # TODO: Disable the Send button until and unless there is text to send
        text_to_send = self.send_text.GetValue()
        if text_to_send is None or text_to_send.strip() == "":
            wx.RichMessageDialog(self, "No text to send",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

        log.debug(f"Sending text to node {self.remote_node_id}")
        try:
            self.interface.sendText(text_to_send, destinationId=self.remote_node_id)
        except Exception as e:
            log.error(f"Error sending message: {e}")
            wx.RichMessageDialog(self, "Error sending message, see log for details",
                                 style=wx.OK | wx.ICON_ERROR).ShowModal()
            return

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
        log.debug("Logging message")
        with (open(shared.config.get("DIRECT_MESSAGE_LOG", "direct-messages.csv"), "a") as lf):
            csv.DictWriter(lf, fieldnames=["device", "remote", "timestamp", "from", "to", "message"],
                           quoting=csv.QUOTE_ALL).writerow(message_dict)

    # noinspection PyUnusedLocal
    def closeEvent(self, event):
        log.debug("Frame close event")
        # Tell parent this window is closing
        wx.PostEvent(self.GetParent(), child_closed(child=self))
        self.Destroy()

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        log.debug("Refresh panel event")
        self.messages.SetObjects(shared.node_conversations[self.local_node_name][self.remote_node_name],
                                 preserveSelection=True)
        item_count = self.messages.GetItemCount()
        if item_count > 0:
            self.messages.EnsureVisible(item_count - 1)
