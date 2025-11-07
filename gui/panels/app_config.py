import wx
import wx.propgrid as wxpg
from dotenv import dotenv_values, set_key
import pathlib
import shutil
import logging

from gui import shared
from gui.gui_events import set_status_bar

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)  # Set our own level separately

class AppConfigPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)

        outer_box = wx.BoxSizer(wx.VERTICAL)

        header_text_box = wx.BoxSizer(wx.HORIZONTAL)
        header_text_box.Add(wx.StaticText(self, label="Environment file editor"), wx.CENTER)
        outer_box.Add(header_text_box, 0, wx.CENTER | wx.TOP, 5)

        button_box = wx.BoxSizer(wx.HORIZONTAL)
        reload_button = wx.Button(self, label="Reload")
        button_box.Add(reload_button, 0)
        save_button = wx.Button(self, label="Save")
        button_box.Add(save_button, 0)
        self.Bind(wx.EVT_BUTTON, self.onReloadButton, reload_button)
        self.Bind(wx.EVT_BUTTON, self.onSaveButton, save_button)
        outer_box.Add(button_box, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 5)

        # TODO: Email validator for email properties (see bottom of dev doc for snippets)

        self.pg = wxpg.PropertyGrid(self, style=wxpg.PG_SPLITTER_AUTO_CENTER | wxpg.PG_BOLD_MODIFIED)
        self.pg.SetPropertyValues(shared.config, autofill=True)
        outer_box.Add(self.pg, 1, wx.EXPAND)

        self.SetSizer(outer_box)
        self.SetAutoLayout(True)
        outer_box.Fit(self)

    @staticmethod
    def _reload_env(property_grid):
        log.debug("Reloading environment")
        # See note in gui.py about why shared.config is loaded this way
        shared.config = {key: value for key, value in dotenv_values(shared.dotenv_file).items()}
        property_grid.SetPropertyValues(shared.config, autofill=True)
        property_grid.ClearModifiedStatus()
        return

    # noinspection PyUnusedLocal
    def onReloadButton(self, event):
        log.debug("Reload button event")
        confirm = wx.RichMessageDialog(self, "Are you sure you want to reload configuration?",
                                       style=wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if confirm.ShowModal() == wx.ID_OK:
            self._reload_env(self.pg)
            wx.PostEvent(self.GetTopLevelParent(), set_status_bar(text="Configuration reloaded"))

    # noinspection PyUnusedLocal
    def onSaveButton(self, event):
        log.debug("Save button event")
        # TODO: Add error checking, especially for set_key
        # Save a backup copy of config file
        log.debug("Backing up environment file")
        backup_env_name = f"{shared.dotenv_file}.bak"
        pathlib.Path(backup_env_name).unlink(missing_ok=True)
        shutil.copy(pathlib.Path(shared.dotenv_file), pathlib.Path(backup_env_name))

        # Sadly we have to iterate through all properties to find those that have changed
        changed_keys = []
        iterator = self.pg.GetIterator(wx.propgrid.PG_ITERATE_NORMAL)
        while not iterator.AtEnd():
            prop = iterator.GetProperty()
            if self.pg.IsPropertyModified(prop):
                prop_name = prop.GetName()
                prop_value = prop.GetValue()
                log.info(f"Saving key {prop_name} value {prop_value}")
                set_key(shared.dotenv_file, prop_name, prop_value)
                changed_keys.append(prop_name)
            iterator.Next()
        log.info(f"Saved {len(changed_keys)} changed key(s)")

        if changed_keys:
            key_string = ", ".join(changed_keys)
            wx.RichMessageDialog(self, "Changed items:\n" + key_string,style=wx.OK | wx.ICON_INFORMATION).ShowModal()
            self.pg.ClearModifiedStatus()
        else:
            wx.RichMessageDialog(self, "No items have been changed",style=wx.OK | wx.ICON_INFORMATION).ShowModal()

        return
