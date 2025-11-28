# Meshtastic client GUI
import logging
import csv
from datetime import datetime

import dotenv
import wx
from pubsub import pub

from gui import shared
from panels.app_config import AppConfigPanel
from panels.device_config import DevConfigPanel
from panels.devices import DevicesPanel
from panels.nodes import NodesPanel
from panels.channel_messages import ChannelMessagesPanel
from panels.direct_messages import DirectMessagesPanel
from gui.gui_events import EVT_SET_STATUS_BAR, process_received_message, EVT_ANNOUNCE_NEW_DEVICE, add_device, node_updated, \
    refresh_panel, EVT_REFRESH_SPECIFIC_PANEL, EVT_FAKE_DEVICE_DISCONNECT, remove_device, fake_device_disconnect, \
    EVT_DISCONNECT_DEVICE, disconnect_device, EVT_REMOVE_DEVICE


class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, "AB8OJ Meshtastic Client")
        this_display = wx.Display(self)  # Get the display this frame is displayed upon
        this_display_height = max(this_display.GetGeometry().GetHeight(), 800)
        this_display_width = max(this_display.GetGeometry().GetWidth(), 600)
        self.SetSize(wx.Size(int(this_display_width/2), int(this_display_height/2)))
        self.CreateStatusBar()
        self.Bind(EVT_SET_STATUS_BAR, self.setStatusBar)

        # === Menus
        # Note that some IDs don't display in these menus if the host platform provides it in another menu (e.g. Mac)
        filemenu = wx.Menu()
        filemenu_exit = filemenu.Append(wx.ID_EXIT, "Exit", " Exit")
        self.Bind(wx.EVT_MENU, self.onExit, filemenu_exit)

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
        self.Bind(EVT_FAKE_DEVICE_DISCONNECT, self.fake_device_disconnect)
        self.Bind(EVT_DISCONNECT_DEVICE, self.reflect_device_disconnect_to_device_panel)
        self.Bind(EVT_REMOVE_DEVICE, self.real_device_disconnect)

        return

    # === Menu events
    # noinspection PyUnusedLocal
    def onExit(self, event):
        if "CONFIRM_ON_EXIT" in shared.config.keys() and shared.config["CONFIRM_ON_EXIT"].lower() in ("true", "yes"):
            result = wx.RichMessageDialog(self, "Exit client?", style=wx.YES_NO | wx.ICON_QUESTION).ShowModal()
            if result == wx.ID_NO:
                return

        self.Close(True)

    # === Toolbar events
    # noinspection PyUnusedLocal
    def onFontIncrease(self, event):
        log.debug("Font increase")
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
        log.debug("Font decrease")
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
        log.debug("Set status bar text")
        self.SetStatusText(event.text)

    def announceNewDevice(self, event):
        log.debug(f"Announce new device: {event.name}")
        # send events to children that need to know about new devices
        wx.PostEvent(self.panel_pointers["chm"], add_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["dm"], add_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["node"], add_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["devconfig"], add_device(name=event.name, interface=event.interface))

    def fake_device_disconnect(self, event):
        log.debug(f"Fake device disconnect: {event.name}")
        # If a device disconnection isn't likely to go through the pub/sub topic, fake it here
        wx.PostEvent(self.panel_pointers["devices"], fake_device_disconnect(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["chm"], remove_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["dm"], remove_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["node"], remove_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["devconfig"], remove_device(name=event.name, interface=event.interface))

    def real_device_disconnect(self, event):
        log.debug(f"Real device disconnect: {event.name}")
        # Send events to children that need to know when a device disconnects
        wx.PostEvent(self.panel_pointers["chm"], remove_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["dm"], remove_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["node"], remove_device(name=event.name, interface=event.interface))
        wx.PostEvent(self.panel_pointers["devconfig"], remove_device(name=event.name, interface=event.interface))

    def reflect_device_disconnect_to_device_panel(self, event):
        log.debug(f"Reflect device disconnect to device panel for device: {event.name}")
        # A panel needs a device to be disconnected. Send that on to the devices panel
        wx.PostEvent(self.panel_pointers["devices"], disconnect_device(name=event.name))

    def refreshSpecifcPanel(self, event):
        log.debug(f"Refresh Specific Panel: {event.panel_name}")
        # A child panel is asking another child panel to refresh
        panel_name = event.panel_name
        if panel_name in self.panel_pointers:
            wx.PostEvent(self.panel_pointers[panel_name], refresh_panel())
        else:
            log.error(f"Invalid panel name received from EVT_REFRESH_SPECIFIC_PANEL: {panel_name}")

    # === Meshtastic pub/sub topic handlers
    """
    IMPORTANT NOTE: See README.md for important details about handling Meshtastic pub/sub messages.
    """

    def onIncomingMessage(self, packet, interface):
        # TODO: Implement wantAck (see https://deepwiki.com/meshtastic/Meshtastic-Apple/2.2-mesh-packets)
        log.debug("Incoming message")
        my_shortname = interface.getShortName()
        my_node_id = interface.getMyNodeInfo().get("user", {}).get("id", "unknown")

        if "raw" in packet and hasattr(packet["raw"], "channel"):
            channel = str(packet["raw"].channel)
        else:
            channel = "Unknown"
            log.debug("Unknown channel")

        text_message = packet.get("decoded", {}).get("text", "Unknown text")

        from_id = packet.get("fromId", None)
        from_num = packet.get("from", None)
        from_shortname = None
        # Start by looking up the sender's shortname in interface.nodes
        if from_id in interface.nodes:
            from_shortname = interface.nodes[from_id].get("user", {}).get("shortName", None)
            log.debug("fromId found in interface.nodes")
        # If we didn't get shortname from interface.nodes, try interface.nodesByNum
        if not from_shortname:
            if from_num in interface.nodesByNum:
                from_shortname = interface.nodesByNum[from_num].get("user", {}).get("shortName", None)
                log.debug("from node found in interface.nodesByNum")
        # Didn't get it either place
        if not from_shortname:
            from_shortname = "????"
            log.debug("Did not find node in either interface.nodes or interface.nodesByNum")

        to_id = packet.get("toId", "Unknown ToId")

        rx_timestamp = packet.get("rxTime", None)
        if rx_timestamp:
            rx_time = datetime.fromtimestamp(int(rx_timestamp))
        else:
            rx_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.debug("No rx timestamp found in packet")

        if to_id == my_node_id:
            log.debug("Direct message")
            wx.PostEvent(self.panel_pointers["dm"], process_received_message(device=my_shortname, channel=channel,
                                                                  sender=from_shortname, timestamp=rx_time,
                                                                  message=text_message))
            wx.PostEvent(self.panel_pointers["node"], process_received_message(device=my_shortname, channel=channel,
                                                                 sender=from_shortname, timestamp=rx_time,
                                                                 message=text_message))
        elif to_id == "^all":
            log.debug("Broadcast message")
            wx.PostEvent(self.panel_pointers["chm"], process_received_message(device=my_shortname, channel=channel,
                                                                  sender=from_shortname, timestamp=rx_time,
                                                                  message=text_message))
        else:
            log.error(f"to_id {to_id} is neither my noode ID nor ^all, that should not have happened")

        return

    def onNodeUpdated(self, node, interface):
        my_shortname = interface.getShortName()
        nodeid = node.get("user", {}).get("id", None)
        nodenum = node.get("num", None)
        log.debug(f"Node update message from nodeid {nodeid} nodenum {nodenum}")
        wx.PostEvent(self.panel_pointers["node"], node_updated(device=my_shortname, nodeid=nodeid, nodenum=nodenum,
                                                               node=node, interface=interface))
        return

def _load_channel_message_log():
    log.debug("Loading channel message log")
    try:
        lf = open(shared.config.get("CHANNEL_MESSAGE_LOG", "channel-messages.csv"), "r")
    except FileNotFoundError:
        log.info("Channel message log file not found, it will be created by incoming messages")
        return

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

    lf.close()

def _load_direct_message_log():
    log.debug("Loading direct message log")
    try:
        lf = open(shared.config.get("DIRECT_MESSAGE_LOG", "direct-messages.csv"), "r")
    except FileNotFoundError:
        log.info("Direct message log file not found, it will be created by incoming messages")
        return

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

    lf.close()

# === Main program ===

"""
Why no main()? 
- Environment configuration needs to be loaded outside of main() so it can be used by the logger and other things
- Logging needs to be set up outside of main() so other things can use it
- That leaves little for a main() function to do, so just do everything here

Why is shared.config populated through iteration?
- By default, dotenv would load values into an OrderedDict, but SetPropertyValues() cannot handle those.
- Instead, load environment config file into a plain dict. 
- Starting with Python 3.7, plain dicts retain insertion order, so this will maintain environment file order.
"""
shared.dotenv_file = dotenv.find_dotenv()
shared.config = {key: value for key, value in dotenv.dotenv_values(shared.dotenv_file).items()}

# Set up logging globally (outside of main()) so everything can access it
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: [%(name)s] [%(module)s.%(funcName)s] %(message)s',
                    filename=shared.config["APP_LOG_NAME"], filemode='a')  # Configure root logger
log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)  # Set our own level separately
logging.getLogger("bleak").setLevel(logging.INFO)  # Turn off BLE debug info
# Sadly, meshtastic logging runs from the root logger, so there's likely no way to set that separately

# Load saved message logs into the message buffers
log.debug("Loading saved message logs")
_load_channel_message_log()
_load_direct_message_log()

# Fire up the app
log.info("Starting GUI")
client_app = wx.App(False)  # Do not redirect stdin.stdout to a window yet
MainFrame(None)
client_app.MainLoop()

log.info("Exiting GUI")
client_app.Destroy()
