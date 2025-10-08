import copy
import wx
import wx.propgrid as wxpg

import shared
from gui_events import set_status_bar

class DevConfigPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        dev_picker_label = wx.StaticText(self, wx.ID_ANY, "Devices")
        self.msg_device_picker = wx.Choice(self, wx.ID_ANY, choices=[],
                                           size=wx.Size(150, 20),
                                           style=wx.CB_SORT | wx.ALIGN_TOP)
        self.msg_device_picker.SetSelection(wx.NOT_FOUND)
        self.Bind(wx.EVT_CHOICE, self.onDevicePickerChoice, self.msg_device_picker)
        sizer.Add(dev_picker_label, 0, flag=wx.LEFT)
        sizer.Add(self.msg_device_picker, 0)

        """
        wx.EnumProperty to select from a list of choices (int or string)
        SetPropertyEditor can set choice, checkbox, etc editors. 
        ...so, when would I use wx.EnumProperty and when would I use SetPropertyEditor?
        
        Try this with categories and just one set of buttons
        Top level: device/local/radio config, module config
        Second level: keys in localConfig / moduleConfig dicts
        Third level: key/value pairs under those
        """

        button_box = wx.BoxSizer(wx.HORIZONTAL)
        reload_button = wx.Button(self, label="Reload")
        button_box.Add(reload_button, 0)
        save_button = wx.Button(self, label="Save")
        button_box.Add(save_button, 0)
        self.Bind(wx.EVT_BUTTON, self.onReloadButton, reload_button)
        self.Bind(wx.EVT_BUTTON, self.onSaveButton, save_button)
        sizer.Add(button_box, 0, wx.CENTER)

        self.config_editor = wxpg.PropertyGrid(self, style=wxpg.PG_SPLITTER_AUTO_CENTER | wxpg.PG_BOLD_MODIFIED)
        sizer.Add(self.config_editor, 1, wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.localConfig = {}
        self.moduleConfig = {}

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time

    def _reload_config_editor(self):
        if not self.selected_device:
            return  # Just in case

        # Buffer for storing values that might change. This makes for easy reloading / discarding of changes
        self.all_configs = {
            "localConfig": copy.deepcopy(shared.connected_interfaces[self.selected_device]["localConfig"]),
            "moduleConfig": copy.deepcopy(shared.connected_interfaces[self.selected_device]["moduleConfig"])
        }

        # *** more stuff here

        return

    def onDevicePickerChoice(self, event):
        pass
        # *** copy from channel_messages
        # *** set device and module picker choice boxes

    def onReloadButton(self, event):
        confirm = wx.RichMessageDialog(self, "Are you sure you want to reload the configuration editor?",
                                       style=wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if confirm.ShowModal() == wx.ID_OK:
            self._reload_config_editor()
            wx.PostEvent(self.GetTopLevelParent(), set_status_bar(text="Configuration reloaded"))

    def onSaveButton(self, event):
        pass
        # *** Copy changed values to radio then write config
