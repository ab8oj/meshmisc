import wx
import wx.propgrid as wxpg

from dotenv import dotenv_values, set_key
from pubsub import pub
import pathlib
import shutil

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
        self.Bind(wx.EVT_BUTTON, self.onSaveButton, save_button)
        outer_box.Add(button_box, 0, wx.CENTER)

        # TODO: Email validator for email properties (see bottom of dev doc for snippets)
        # TODO: self.dotenv_file = dotenv.find_dotenv() to find .env file

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
        property_grid.ClearModifiedStatus()
        return

    # noinspection PyUnusedLocal
    def onReloadButton(self, event):
        confirm = wx.RichMessageDialog(self, "Are you sure you want to reload .env?",
                                       style=wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if confirm.ShowModal() == wx.ID_OK:
            self.reload_env(self.pg)
            pub.sendMessage("mainframe.changeStatusBar", status_text=".env reloaded")

    # noinspection PyUnusedLocal
    def onSaveButton(self, event):
        # TODO: Add error checking, especially for set_key
        # Save a backup copy of .env
        pathlib.Path(".env.bak").unlink(missing_ok=True)
        shutil.copy(pathlib.Path(".env"), pathlib.Path(".env.bak"))

        # Sadly we have to iterate through all properties to find those that have changed
        changed_keys = []
        iterator = self.pg.GetIterator(wx.propgrid.PG_ITERATE_NORMAL)
        while not iterator.AtEnd():
            prop = iterator.GetProperty()
            if self.pg.IsPropertyModified(prop):
                prop_name = prop.GetName()
                prop_value = prop.GetValue()
                set_key(".env", prop_name, prop_value)
                changed_keys.append(prop_name)
            iterator.Next()

        if changed_keys:
            key_string = ", ".join(changed_keys)
            wx.RichMessageDialog(self, "Changed items:\n" + key_string,style=wx.OK | wx.ICON_INFORMATION).ShowModal()
            self.pg.ClearModifiedStatus()
        else:
            wx.RichMessageDialog(self, "No items have been changed",style=wx.OK | wx.ICON_INFORMATION).ShowModal()

        return

