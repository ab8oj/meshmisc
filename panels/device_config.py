import wx
import wx.propgrid as wxpg

import shared
from gui_events import set_status_bar, EVT_ADD_DEVICE, EVT_REFRESH_PANEL


class DevConfigPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        dev_picker_label = wx.StaticText(self, wx.ID_ANY, "Devices")
        self.device_picker = wx.Choice(self, wx.ID_ANY, choices=[],
                                       size=wx.Size(150, 20),
                                       style=wx.CB_SORT | wx.ALIGN_TOP)
        self.device_picker.SetSelection(wx.NOT_FOUND)
        self.Bind(wx.EVT_CHOICE, self.onDevicePickerChoice, self.device_picker)
        sizer.Add(dev_picker_label, 0, flag=wx.LEFT)
        sizer.Add(self.device_picker, 0)

        sizer.Add(wx.StaticText(self, wx.ID_ANY, "Device Configuration"), 0, wx.CENTER)
        lc_button_box = wx.BoxSizer(wx.HORIZONTAL)
        lc_reload_button = wx.Button(self, label="Reload")
        lc_button_box.Add(lc_reload_button, 0)
        lc_save_button = wx.Button(self, label="Save")
        lc_button_box.Add(lc_save_button, 0)
        self.Bind(wx.EVT_BUTTON, self.onLCReloadButton, lc_reload_button)
        self.Bind(wx.EVT_BUTTON, self.onLCSaveButton, lc_save_button)
        sizer.Add(lc_button_box, 0, wx.CENTER)
        self.lc_config_editor = wxpg.PropertyGrid(self, style=wxpg.PG_SPLITTER_AUTO_CENTER | wxpg.PG_BOLD_MODIFIED)
        sizer.Add(self.lc_config_editor, 1, wx.EXPAND)

        sizer.Add(wx.StaticText(self, wx.ID_ANY, "Module Configuration"), 0, wx.CENTER)
        mc_button_box = wx.BoxSizer(wx.HORIZONTAL)
        mc_reload_button = wx.Button(self, label="Reload")
        mc_button_box.Add(mc_reload_button, 0)
        mc_save_button = wx.Button(self, label="Save")
        mc_button_box.Add(mc_save_button, 0)
        self.Bind(wx.EVT_BUTTON, self.onMCReloadButton, mc_reload_button)
        self.Bind(wx.EVT_BUTTON, self.onMCSaveButton, mc_save_button)
        sizer.Add(mc_button_box, 0, wx.CENTER)
        self.mc_config_editor = wxpg.PropertyGrid(self, style=wxpg.PG_SPLITTER_AUTO_CENTER | wxpg.PG_BOLD_MODIFIED)
        sizer.Add(self.mc_config_editor, 1, wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.localConfig = {}
        self.moduleConfig = {}

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)

    def _reload_lc_grid(self, interface):
        if not self.selected_device:
            return  # Just in case

        # Buffers for storing values that might change. This makes for easy reloading / discarding of changes
        this_device = interface.getNode('^local')
        self.localConfig = this_device.localConfig

        self.lc_config_editor.Clear()
        self._load_config_values(self.localConfig, self.lc_config_editor)
        self.lc_config_editor.CollapseAll()

        return

    def _reload_mc_grid(self, interface):
        if not self.selected_device:
            return  # Just in case

        # Buffers for storing values that might change. This makes for easy reloading / discarding of changes
        this_device = interface.getNode('^local')
        self.moduleConfig = this_device.moduleConfig

        self.mc_config_editor.Clear()
        self._load_config_values(self.moduleConfig, self.mc_config_editor)
        self.mc_config_editor.CollapseAll()

        return

    def _load_config_values(self, config, grid):
        # The configuration bits use Google protocol buffers (oh, joy), hence the DESCRIPTOR stuff herein
        # General format: config.category.setting (e.g. localConfig.bluetooth.fixed_pin = "123456")
        categories = config.DESCRIPTOR.fields_by_name.keys()  # Get the names of all the categories
        for cat in categories:
            if cat == "version":  # Gotta love the exception
                continue
            grid.Append(wxpg.PropertyCategory(cat))  # Make it a category in the property grid

            category_settings = getattr(config, cat)
            setting_keys = category_settings.DESCRIPTOR.fields_by_name  # Get all the settings under this category
            for setting_key in setting_keys:
                if setting_key == "version":  # Again
                    continue
                editor = self._get_editor_type(config, setting_key)
                setting_value = getattr(category_settings, setting_key)
                """
                config.DESCRIPTOR.fields_by_name[setting_key].enum_type.name = name of enum type
                   .enum_type is None if it's not an enum type
                onfig.DESCRIPTOR.fields_by_name[setting_key].enum_type.<presumably "values" or something>
                    is a list of values
                    maybe "values_by_name"? Each of those has a corresponding .number to get the numeric value. See:
                    https://stackoverflow.com/questions/40226049/find-enums-listed-in-python-descriptor-for-protobuf
                ...according to https://stackoverflow.com/questions/26849968/finding-enum-type-in-a-protobuffer
                """
                # Note: there are duplicate keys across configuration categories, but property names must be unique.
                #       So, create a unique name for each (e.g. Security_isManaged). Labels can be duplicated.
                grid.AppendIn(cat, wxpg.StringProperty(str(setting_key), f"{cat}_{str(setting_key)}",
                                                                        str(setting_value)))
                """
                Replace the above with:
                    Add the property to the grid (we need the return value which is a PGProperty)
                        using the appropriate data type 
                    SetPropertyEditor of that property using "editor" 
                        What is "id" in SetPropertyEditor? property, str, or id
                        Just Internet search for examples of SetPropertyEditor
                        
                    *** Maybe change _get_editor_type to actually add the property and set the editor type 
                """

        return

    @staticmethod
    def _get_editor_type(config, setting_key):
        if isinstance(setting_key, bool):
            return "CheckBox"
        elif isinstance(setting_key, int):
            return "TextCtrl"
        elif isinstance(setting_key, str):
            if config.DESCRIPTOR.fields_by_name[setting_key].enum_type:
                return "Will figure out enum type later"
            else:
                return "TextCtrl"
        else:
            return "TextCtrl"  # default to simple string

    """
    wx.EnumProperty to select from a list of choices (int or string)
    SetPropertyEditor can set choice, checkbox, etc editors. 
    ...so, when would I use wx.EnumProperty and when would I use SetPropertyEditor?
    """

    # wxPython events

    def onDevicePickerChoice(self, event):
        self.selected_device = self.device_picker.GetString(event.GetSelection())
        self._reload_mc_grid(shared.connected_interfaces[self.selected_device])
        self._reload_lc_grid(shared.connected_interfaces[self.selected_device])

    def onLCReloadButton(self, event):
        confirm = wx.RichMessageDialog(self, "Are you sure you want to reload the device configuration?",
                                       style=wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if confirm.ShowModal() == wx.ID_OK:
            self._reload_lc_grid(shared.connected_interfaces[self.selected_device])
            wx.PostEvent(self.GetTopLevelParent(), set_status_bar(text="Device configuration reloaded"))

    def onLCSaveButton(self, event):
        pass
        # *** Copy changed values to radio then write config

    def onMCReloadButton(self, event):
        confirm = wx.RichMessageDialog(self, "Are you sure you want to reload the module configuration?",
                                       style=wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if confirm.ShowModal() == wx.ID_OK:
            self._reload_mc_grid(shared.connected_interfaces[self.selected_device])
            wx.PostEvent(self.GetTopLevelParent(), set_status_bar(text="Module configuration reloaded"))

    def onMCSaveButton(self, event):
        pass
        # *** Copy changed values to radio then write config

    def add_device_event(self, event):
        device_name = event.name

        # Add the new device to the device picker and message buffer
        self.device_picker.Append(device_name)
        if self.device_picker.GetCount() == 1:  # this is the first device, auto-select it
            self.selected_device = device_name
            self.device_picker.Select(0)
            self._reload_mc_grid(shared.connected_interfaces[self.selected_device])
            self._reload_lc_grid(shared.connected_interfaces[self.selected_device])

    def refresh_panel_event(self, event):
        self.Layout()
