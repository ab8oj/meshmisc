# Meshtastic client GUI

import wx
import wx.propgrid as wxpg

from dotenv import dotenv_values


class MainFrame(wx.Frame):
    def __init__(self, parent):
        # noinspection PyTypeChecker
        wx.Frame.__init__(self, parent, wx.ID_ANY, "AB8OJ Meshtastic Client", size=(800, 600))  # TODO: size tweaking
        self.CreateStatusBar()

        # === Menus
        filemenu = wx.Menu()
        # Note that some IDs don't display in these menus if the host platform provides it in another menu (e.g. Mac)
        menu_exit = filemenu.Append(wx.ID_EXIT, "Exit", " Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)
        menu_fruit = filemenu.Append(100, "Banana")  # TODO: Obviously, replace with something more useful
        self.Bind(wx.EVT_MENU, self.fruit_selected, menu_fruit)

        aboutmenu = wx.Menu()
        aboutmenu.Append(wx.ID_ABOUT, "About", " Aboout this program")
        aboutmenu.Append(900, "Version")

        menubar = wx.MenuBar()
        menubar.Append(filemenu, "File")
        menubar.Append(aboutmenu, "About")
        self.SetMenuBar(menubar)

        # === Listbook and panels
        lb = wx.Listbook(self, style=wx.LB_LEFT)
        lb.AddPage(AppConfigPanel(lb), "Application configuration")
        lb.AddPage(DevicesPanel(lb), "Devices")
        lb.AddPage(MessagesPanel(lb), "Messages")
        lb.AddPage(NodesPanel(lb), "Nodes")

        self.Show(True)

    # noinspection PyUnusedLocal
    def fruit_selected(self, event):
        # NOTE: standard MessageDialog always displays a folder icon on Mac OS X, so use RichMessageDialog instead
        dlg = wx.RichMessageDialog(self, "Banana for scale", "",
                                   wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    # noinspection PyUnusedLocal
    def on_exit(self, event):
        # TODO: Exit confirmation if configured to do so
        self.Close(True)


class AppConfigPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)

        outer_box = wx.BoxSizer(wx.VERTICAL)

        header_text_box = wx.BoxSizer(wx.HORIZONTAL)
        header_text_box.Add(wx.StaticText(self, label="Environment file editor"), wx.CENTER)
        outer_box.Add(header_text_box, 0, wx.CENTER | wx.TOP)

        button_box = wx.BoxSizer(wx.HORIZONTAL)
        button_box.Add(wx.Button(self, wx.ID_ANY, "Load"), 0)
        button_box.Add(wx.Button(self, wx.ID_ANY, "Save"), 0)
        outer_box.Add(button_box, 0, wx.CENTER)

        pg = wxpg.PropertyGrid(self, style=wxpg.PG_SPLITTER_AUTO_CENTER | wxpg.PG_BOLD_MODIFIED)
        # TODO: Instead of a default load of the file at init time, should it have blank values until load button?
        config = dotenv_values(".env")  # TODO: is there a fun way to configure the location of the config file?
        real_dict = {}
        for key, value in config.items():
            real_dict[key] = value
        pg.SetPropertyValues(real_dict, autofill=True)  # For some reason, this doesn't work with OrderedDict
        outer_box.Add(pg, 1, wx.EXPAND)

        self.SetSizer(outer_box)
        self.SetAutoLayout(True)
        outer_box.Fit(self)

class DevicesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        wx.StaticText(self, label="Devices")


class MessagesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        wx.StaticText(self, label="Messages")


class NodesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        wx.StaticText(self, label="Nodes")


# === Main ===
def main():
    client_app = wx.App(False)  # Do not redirect stdin.stdout to a window yet
    MainFrame(None)
    client_app.MainLoop()
    client_app.Destroy()
    # TODO: other cleanup here


if __name__ == "__main__":
    main()
