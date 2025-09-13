# Meshtastic client GUI
from datetime import datetime

import wx
from pubsub import pub

from panels.app_config import AppConfigPanel
from panels.devices import DevicesPanel
from panels.nodes import NodesPanel
from panels.channel_messages import ChannelMessagesPanel
from gui_events import EVT_SET_STATUS_BAR, process_received_message, EVT_ANNOUNCE_NEW_DEVICE, add_device


# TODO: Implement logging
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
        self.lb.AddPage(DevicesPanel(self.lb), "Devices", select=True)
        self.devices_panel = self.lb.GetPage(0)
        self.lb.AddPage(ChannelMessagesPanel(self.lb), "Channel Messages")
        self.chm_panel = self.lb.GetPage(1)
        # TODO: Direct messages panel goes here
        self.lb.AddPage(NodesPanel(self.lb), "Nodes")
        self.lb.AddPage(AppConfigPanel(self.lb), "Application configuration")

        self.Show(True)

        pub.subscribe(self.onIncomingMessage, "meshtastic.receive.text")

        self.Bind(EVT_ANNOUNCE_NEW_DEVICE, self.announceNewDevice)

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
        wx.PostEvent(self.chm_panel, add_device(name=event.name, interface=event.interface))

    # === Meshtastic pub/sub topic handlers
    """
    IMPORTANT NOTE: See README.md for important details about handling Meshtastic pub/sub messages.
    """

    def onIncomingMessage(self, packet, interface):
        # TODO: Implement wantAck (see https://deepwiki.com/meshtastic/Meshtastic-Apple/2.2-mesh-packets)
        # TODO: when direct message panel gets implemented, split direct messages to that and ^all to channel panel
        our_shortname = interface.getShortName()
        if "raw" in packet and hasattr(packet["raw"], "channel"):
            channel = packet["raw"].channel
        else:
            channel = "Unknown"
        text_message = packet.get("decoded", {}).get("text", "Unknown text")
        if "fromId" in packet:
            if packet["fromId"] in interface.nodes:
                from_shortname = interface.nodes[packet["fromId"]].get("user", {}).get("shortName", "Unknown")
            else:
                from_shortname = "????"
        else:
            from_shortname = "UNK?"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        wx.PostEvent(self.chm_panel, process_received_message(device=our_shortname, channel=channel,
                                                              sender=from_shortname, timestamp=now,
                                                              message=text_message))


def main():
    client_app = wx.App(False)  # Do not redirect stdin.stdout to a window yet
    MainFrame(None)
    client_app.MainLoop()
    # TODO: disconnect from any connected devices
    client_app.Destroy()
    # TODO: other cleanup here


if __name__ == "__main__":
    main()
