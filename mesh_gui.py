# Meshtastic client GUI
import csv
from datetime import datetime

import dotenv
import wx
from pubsub import pub

import shared
from panels.app_config import AppConfigPanel
from panels.device_config import DevConfigPanel
from panels.devices import DevicesPanel
from panels.nodes import NodesPanel
from panels.channel_messages import ChannelMessagesPanel
from panels.direct_messages import DirectMessagesPanel
from gui_events import EVT_SET_STATUS_BAR, process_received_message, EVT_ANNOUNCE_NEW_DEVICE, add_device, node_updated, \
    refresh_panel, EVT_REFRESH_SPECIFIC_PANEL


# TODO: Implement logging
# TODO: Is interface.nodes really a reliable node database? Perhaps it has some gaps
class MainFrame(wx.Frame):
    def __init__(self, parent):
        # noinspection PyTypeChecker
        wx.Frame.__init__(self, parent, wx.ID_ANY, "AB8OJ Meshtastic Client", size=(800, 600))  # TODO: size tweaking
        self.CreateStatusBar()
        self.Bind(EVT_SET_STATUS_BAR, self.setStatusBar)

        # === Menus
        # Note that some IDs don't display in these menus if the host platform provides it in another menu (e.g. Mac)
        filemenu = wx.Menu()
        filemenu_exit = filemenu.Append(wx.ID_EXIT, "Exit", " Exit")
        self.Bind(wx.EVT_MENU, self.onExit, filemenu_exit)
        filemenu_fruit = filemenu.Append(wx.ID_ANY, "Banana")  # TODO: Obviously, replace with something more useful
        self.Bind(wx.EVT_MENU, self.onFruitSelected, filemenu_fruit)

        aboutmenu = wx.Menu()
        aboutmenu.Append(wx.ID_ABOUT, "About", " Aboout this program")
        aboutmenu.Append(wx.ID_ANY, "Version")

        menubar = wx.MenuBar()
        menubar.Append(filemenu, "File")
        menubar.Append(aboutmenu, "About")
        self.SetMenuBar(menubar)

        self.toolbar = self.CreateToolBar(wx.ID_ANY)
        plus_icon = wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_TOOLBAR)
        plus_tool = self.toolbar.AddTool(wx.ID_ANY, "+", wx.BitmapBundle.FromBitmap(plus_icon), "Increase font")
        self.Bind(wx.EVT_MENU, self.onFontIncrease, plus_tool)
        minus_icon = wx.ArtProvider.GetBitmap(wx.ART_MINUS, wx.ART_TOOLBAR)
        minus_tool = self.toolbar.AddTool(wx.ID_ANY, "-", wx.BitmapBundle.FromBitmap(minus_icon), "Decrease font")
        self.Bind(wx.EVT_MENU, self.onFontDecrease, minus_tool)
        self.toolbar.Realize()

        accel_table = wx.AcceleratorTable([ (wx.ACCEL_CMD, ord('='), plus_tool.GetId()),
                                            (wx.ACCEL_CMD, ord('-'), minus_tool.GetId()),
                                            ])
        self.SetAcceleratorTable(accel_table)

        # === Listbook and panels
        self.lb = wx.Listbook(self, style=wx.LB_LEFT)
        self.panel_pointers = {}
        self.lb.AddPage(DevicesPanel(self.lb), "Devices", select=True)
        self.panel_pointers["devices"] = self.lb.GetPage(0)
        self.lb.AddPage(ChannelMessagesPanel(self.lb), "Channel Messages")
        self.panel_pointers["chm"] = self.lb.GetPage(1)
        self.lb.AddPage(DirectMessagesPanel(self.lb), "Direct Messages")
        self.panel_pointers["dm"] = self.lb.GetPage(2)
        self.lb.AddPage(NodesPanel(self.lb), "Nodes")
        self.panel_pointers["node"] = self.lb.GetPage(3)
        self.lb.AddPage(AppConfigPanel(self.lb), "Application configuration")
        self.panel_pointers["ac"] = self.lb.GetPage(4)
        self.lb.AddPage(DevConfigPanel(self.lb), "Device configuration")
        self.panel_pointers["devconfig"] = self.lb.GetPage(5)

        self.Show(True)

        pub.subscribe(self.onIncomingMessage, "meshtastic.receive.text")
        pub.subscribe(self.onNodeUpdated, "meshtastic.node.updated")

        self.Bind(EVT_ANNOUNCE_NEW_DEVICE, self.announceNewDevice)
        self.Bind(EVT_REFRESH_SPECIFIC_PANEL, self.refreshSpecifcPanel)

        return

    # === Menu events
    # noinspection PyUnusedLocal
    def onFruitSelected(self, event):
        # NOTE: standard MessageDialog always displays a folder icon on Mac OS X, so use RichMessageDialog instead
        dlg = wx.RichMessageDialog(self, "Banana for scale", "",
                                   wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    # noinspection PyUnusedLocal
    def onExit(self, event):
        # TODO: Exit confirmation if configured to do so
        self.Close(True)

    # === Toolbar events

    # noinspection PyUnusedLocal
    def onFontIncrease(self, event):
        self._make_all_children_larger(self)
        self.lb.Fit()
        self.SendSizeEvent()

    def _make_all_children_larger(self, window):
        # Preserve wx.Choice selection across font change
        if isinstance(window, wx.Choice):
            choice_selection = window.GetSelection()
            window.SetFont(window.GetFont().MakeLarger())
            window.SetSelection(choice_selection)
        else:
            window.SetFont(window.GetFont().MakeLarger())

        for child in window.GetChildren():
            self._make_all_children_larger(child)

    # noinspection PyUnusedLocal
    def onFontDecrease(self, event):
        self._make_all_children_smaller(self)
        self.lb.Fit()
        self.SendSizeEvent()

    def _make_all_children_smaller(self, window):
        # Preserve wx.Choice selection across font change
        if isinstance(window, wx.Choice):
            choice_selection = window.GetSelection()
            window.SetFont(window.GetFont().MakeSmaller())
            window.SetSelection(choice_selection)
        else:
            window.SetFont(window.GetFont().MakeSmaller())

        for child in window.GetChildren():
            self._make_all_children_smaller(child)

    # === wxPython events
    def setStatusBar(self, event):
        self.SetStatusText(event.text)

    def announceNewDevice(self, event):
        # send events to children that need to know about new devices
        wx.PostEvent(self.panel_pointers["chm"], add_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["dm"], add_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["node"], add_device(name=event.name, interface=event.interface))

    def refreshSpecifcPanel(self, event):
        panel_name = event.panel_name
        if panel_name in self.panel_pointers:
            wx.PostEvent(self.panel_pointers[panel_name], refresh_panel())
        else:
            # TODO: Change to logging
            print("Invalid panel name received from EVT_REFRESH_SPECIFIC_PANEL")

    # === Meshtastic pub/sub topic handlers
    """
    IMPORTANT NOTE: See README.md for important details about handling Meshtastic pub/sub messages.
    """

    def onIncomingMessage(self, packet, interface):
        # TODO: Implement wantAck (see https://deepwiki.com/meshtastic/Meshtastic-Apple/2.2-mesh-packets)
        my_shortname = interface.getShortName()
        my_node_id = interface.getMyNodeInfo().get("user", {}).get("id", "unknown")

        if "raw" in packet and hasattr(packet["raw"], "channel"):
            channel = str(packet["raw"].channel)
        else:
            channel = "Unknown"

        text_message = packet.get("decoded", {}).get("text", "Unknown text")

        from_id = packet.get("fromId", None)
        from_num = packet.get("from", None)
        from_shortname = None
        # Start by looking up the sender's shortname in interface.nodes
        if from_id in interface.nodes:
            from_shortname = interface.nodes[from_id].get("user", {}).get("shortName", None)
        # If we didn't get shortname from interface.nodes, try interface.nodesByNum
        if not from_shortname:
            if from_num in interface.nodesByNum:
                from_shortname = interface.nodesByNum[from_num].get("user", {}).get("shortName", None)
        # Didn't get it either place
        if not from_shortname:
            from_shortname = "????"

        to_id = packet.get("toId", "Unknown ToId")

        rx_timestamp = packet.get("rxTime", None)
        if rx_timestamp:
            rx_time = datetime.fromtimestamp(int(rx_timestamp))
        else:
            rx_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if to_id == my_node_id:
            wx.PostEvent(self.panel_pointers["dm"], process_received_message(device=my_shortname, channel=channel,
                                                                  sender=from_shortname, timestamp=rx_time,
                                                                  message=text_message))
            wx.PostEvent(self.panel_pointers["node"], process_received_message(device=my_shortname, channel=channel,
                                                                 sender=from_shortname, timestamp=rx_time,
                                                                 message=text_message))
        elif to_id == "^all":
            wx.PostEvent(self.panel_pointers["chm"], process_received_message(device=my_shortname, channel=channel,
                                                                  sender=from_shortname, timestamp=rx_time,
                                                                  message=text_message))
        else:
            print("to_id is neither my noode ID nor ^all, that should not have happened")

        return

    def onNodeUpdated(self, node, interface):
        my_shortname = interface.getShortName()
        nodeid = node.get("user", {}).get("id", None)
        nodenum = node.get("num", None)
        wx.PostEvent(self.panel_pointers["node"], node_updated(device=my_shortname, nodeid=nodeid, nodenum=nodenum,
                                                               node=node, interface=interface))
        return

def _load_channel_message_log():
    try:
        lf = open(shared.config.get("CHANNEL_MESSAGE_LOG", "channel-messages.csv"), "r")
    except FileNotFoundError:
        return  # Silently ignore no log file found yet

    with lf:
        reader = csv.DictReader(lf, fieldnames=["device", "channel", "timestamp", "sender", "message"])
        for row in reader:
            device = row["device"]
            channel = row["channel"]
            timestamp = row["timestamp"]
            sender = row["sender"]
            message = row["message"]
            if device not in shared.channel_messages:
                shared.channel_messages[device] = {}
            if channel not in shared.channel_messages[device]:
                shared.channel_messages[device][channel] = []
            shared.channel_messages[device][channel].append({"timestamp": timestamp, "sender": sender,
                                                         "message":message})

def _load_direct_message_log():
    try:
        lf = open(shared.config.get("DIRECT_MESSAGE_LOG", "direct-messages.csv"), "r")
    except FileNotFoundError:
        return  # Silently ignore no log file found yet

    with lf:
        reader = csv.DictReader(lf, fieldnames=["device", "remote", "timestamp", "from", "to", "message"])
        for row in reader:
            device = row["device"]
            remote = row["remote"]
            timestamp = row["timestamp"]
            from_shortname = row["from"]
            to_shortname = row["to"]
            message = row["message"]
            if device not in shared.direct_messages:
                shared.direct_messages[device] = []
            if device not in shared.node_conversations:
                shared.node_conversations[device] = {}
            if remote not in shared.node_conversations[device]:
                shared.node_conversations[device][remote] = []
            shared.direct_messages[device].append({"timestamp": timestamp, "from": from_shortname,
                                                         "to": to_shortname, "message":message})
            shared.node_conversations[device][remote].append({"timestamp": timestamp, "from": from_shortname,
                                                   "to": to_shortname, "message": message})

def main():
    """
    Load environment configuration (usually named .env in the app directory)
    By default, dotenv would load values into an OrderedDict, but SetPropertyValues() cannot handle those.
    Instead, load environment config file into a plain dict instead. Starting with Python 3.7,
    plain dicts retain insertion order, so this will maintain environment file order.
    """
    shared.dotenv_file = dotenv.find_dotenv()
    shared.config = {key: value for key, value in dotenv.dotenv_values(".env").items()}

    # Load saved message logs into the message buffers
    _load_channel_message_log()
    _load_direct_message_log()

    # Fire up the app
    client_app = wx.App(False)  # Do not redirect stdin.stdout to a window yet
    MainFrame(None)
    client_app.MainLoop()

    # TODO: disconnect from any connected devices
    client_app.Destroy()
    # TODO: other cleanup here


if __name__ == "__main__":
    main()
