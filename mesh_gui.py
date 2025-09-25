# Meshtastic client GUI
from datetime import datetime

import wx
from pubsub import pub

from panels.app_config import AppConfigPanel
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        my_shortname = interface.getShortName()
        my_node_id = interface.getMyNodeInfo().get("user", {}).get("id", "unknown")

        if "raw" in packet and hasattr(packet["raw"], "channel"):
            channel = packet["raw"].channel
        else:
            channel = "Unknown"

        text_message = packet.get("decoded", {}).get("text", "Unknown text")

        if "fromId" in packet:
            if packet["fromId"] in interface.nodes:
                from_shortname = interface.nodes[packet["fromId"]].get("user", {}).get("shortName", "None")
            elif packet["fromId"] is None:
                # We didn't get a fromId in the message, how rude.
                # TODO: Log this
                if packet.get("viaMqtt", False):
                    from_shortname = "MQTT"
                else:
                    from_shortname = "----"  # Differentiate this from the fall-thru default case
            else:
                # We got a fromId but it's not in the MeshInterface node list
                # TODO: Log this
                from_shortname = "????"
        else:  # fromId key is not even in the packat
            from_shortname = "UNK?"

        to_id = packet.get("toId", "Unknown ToId")
        if to_id == my_node_id:
            wx.PostEvent(self.panel_pointers["dm"], process_received_message(device=my_shortname, channel=channel,
                                                                  sender=from_shortname, timestamp=now,
                                                                  message=text_message))
            wx.PostEvent(self.panel_pointers["node"], process_received_message(device=my_shortname, channel=channel,
                                                                 sender=from_shortname, timestamp=now,
                                                                 message=text_message))
        elif to_id == "^all":
            wx.PostEvent(self.panel_pointers["chm"], process_received_message(device=my_shortname, channel=channel,
                                                                  sender=from_shortname, timestamp=now,
                                                                  message=text_message))
        else:
            print("to_id is neither my noode ID nor ^all, that should not have happened")

        return

    def onNodeUpdated(self, node, interface):
        wx.PostEvent(self.panel_pointers["node"], node_updated(node=node, interface=interface))
        return


def main():
    client_app = wx.App(False)  # Do not redirect stdin.stdout to a window yet
    MainFrame(None)
    client_app.MainLoop()
    # TODO: disconnect from any connected devices
    client_app.Destroy()
    # TODO: other cleanup here


if __name__ == "__main__":
    main()
