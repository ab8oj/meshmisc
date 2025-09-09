# Meshtastic client GUI

from panels.app_config import AppConfigPanel
from panels.devices import DevicesPanel
from panels.nodes import NodesPanel
from panels.channel_messages import ChannelMessagesPanel
from gui_events import EVT_SET_STATUS_BAR


import wx


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
        lb = wx.Listbook(self, style=wx.LB_LEFT)
        lb.AddPage(DevicesPanel(lb), "Devices", select=True)
        lb.AddPage(ChannelMessagesPanel(lb), "Channel Messages")
        # TODO: Direct messages panel goes here
        lb.AddPage(NodesPanel(lb), "Nodes")
        lb.AddPage(AppConfigPanel(lb), "Application configuration")

        self.Show(True)

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


def main():
    client_app = wx.App(False)  # Do not redirect stdin.stdout to a window yet
    MainFrame(None)
    client_app.MainLoop()
    # TODO: disconnect from any connected devices
    client_app.Destroy()
    # TODO: other cleanup here


if __name__ == "__main__":
    main()
