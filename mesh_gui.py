# Meshtastic client GUI

import wx
import wx.propgrid as wxpg

from dotenv import dotenv_values
from pubsub import pub


class MainFrame(wx.Frame):
    def __init__(self, parent):
        # noinspection PyTypeChecker
        wx.Frame.__init__(self, parent, wx.ID_ANY, "AB8OJ Meshtastic Client", size=(800, 600))  # TODO: size tweaking
        self.CreateStatusBar()
        pub.subscribe(self.onChangeStatusBar, "mainframe.changeStatusBar")
        pub.subscribe(self.onClearStatusBar, "mainframe.clearStatusBar")

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
        lb.AddPage(AppConfigPanel(lb), "Application configuration")
        lb.AddPage(DevicesPanel(lb), "Devices")
        lb.AddPage(MessagesPanel(lb), "Messages")
        lb.AddPage(NodesPanel(lb), "Nodes")

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

    # === Pub/sub events
    def onChangeStatusBar(self, status_text):
        self.SetStatusText(status_text)

    def onClearStatusBar(self):
        self.SetStatusText("")


# === Panels for the main listbook
class AppConfigPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)

        outer_box = wx.BoxSizer(wx.VERTICAL)

        header_text_box = wx.BoxSizer(wx.HORIZONTAL)
        header_text_box.Add(wx.StaticText(self, label="Environment file editor"), wx.CENTER)
        outer_box.Add(header_text_box, 0, wx.CENTER | wx.TOP)

        button_box = wx.BoxSizer(wx.HORIZONTAL)
        reload_button = wx.Button(self, label="Reload")
        button_box.Add(reload_button, 0)
        save_button = wx.Button(self, label="Save")
        button_box.Add(save_button, 0)
        self.Bind(wx.EVT_BUTTON, self.onReloadButton, reload_button)
        self.Bind(wx.EVT_MENU, self.onSaveButton, save_button)
        outer_box.Add(button_box, 0, wx.CENTER)

        self.pg = wxpg.PropertyGrid(self, style=wxpg.PG_SPLITTER_AUTO_CENTER | wxpg.PG_BOLD_MODIFIED)
        self.reload_env(self.pg)
        outer_box.Add(self.pg, 1, wx.EXPAND)

        self.SetSizer(outer_box)
        self.SetAutoLayout(True)
        outer_box.Fit(self)

    @staticmethod
    def reload_env(property_grid):
        """
        Reload .env into a property grid
        SetPropertyValues cannot handle OrderedDicts so we have to convert it to a plain dict
        Dicts now remember insertion order (Python 3.7+), so this conversion preserves key order
        """
        real_dict = {key: value for key, value in dotenv_values(".env").items()}
        property_grid.SetPropertyValues(real_dict, autofill=True)
        # TODO: Un-bold all property grid values
        return

    def onReloadButton(self, event):
        confirm = wx.RichMessageDialog(self, "Are you sure you want to reload .env?",
                                   style=wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if confirm.ShowModal() == wx.ID_OK:
            self.reload_env(self.pg)
            pub.sendMessage("mainframe.changeStatusBar", status_text=".env reloaded")

    def onSaveButton(self, event):
        pass


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
