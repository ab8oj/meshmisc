# Meshtastic client GUI

import wx

class MainFrame(wx.Frame):
    def __init__(self, parent):
        # noinspection PyTypeChecker
        # TODO: think through size - hardcode, percentage of screen, go with default?
        wx.Frame.__init__(self, parent, -1, "AB8OJ Meshtastic Client", size=(800, 600))  # TODO: what is -1?

        nb = wx.Listbook(self, style=wx.LB_LEFT)
        appconfig_panel = wx.Panel(nb)
        wx.StaticText(appconfig_panel, label="Application configuration")
        devices_panel = wx.Panel(nb)
        wx.StaticText(devices_panel, label="Devices")
        nb.AddPage(appconfig_panel, "Application configuration")
        nb.AddPage(devices_panel, "Devices")

        self.CreateStatusBar()

        filemenu = wx.Menu()
        # Note that ID_EXIT doesn't display anything if the host platform provides another way (e.g. Mac)
        menu_exit = filemenu.Append(wx.ID_EXIT, "Exit", " Exit")
        menu_fruit = filemenu.Append(100, "Banana")  # TODO: Obviously, replace with something more useful
        self.Bind(wx.EVT_MENU, self.fruit_selected, menu_fruit)
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)

        aboutmenu = wx.Menu()
        # Note that ID_ABOUT doesn't display anything if the host platform provides another way (e.g. Mac)
        aboutmenu.Append(wx.ID_ABOUT, "About", " Aboout this program")
        aboutmenu.Append(900, "Version")

        menubar = wx.MenuBar()
        menubar.Append(filemenu, "File")
        menubar.Append(aboutmenu, "About")
        self.SetMenuBar(menubar)

        self.Show(True)

    def fruit_selected(self, event):
        # NOTE: standard MessageDialog always displays a folder icon on Mac OS X, so use RichMessageDialog instead
        dlg = wx.RichMessageDialog(self, "Banana for scale", "",
                               wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def on_exit(self, event):
        # TODO: Exit confirmation if configured to do so
        self.Close(True)

# === Main ===
def main():
    client_app = wx.App(False)  # Do not redirect stdin.stdout to a window yet
    client_frame = MainFrame(None)
    client_app.MainLoop()
    client_app.Destroy()
    # TODO: other cleanup here

if __name__ == "__main__":
    main()
