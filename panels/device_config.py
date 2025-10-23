import wx
import wx.propgrid as wxpg

import shared
from gui_events import set_status_bar, EVT_ADD_DEVICE, EVT_REFRESH_PANEL, fake_device_disconnect, EVT_REMOVE_DEVICE
from panels.channel_edit import ChannelEdit


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

        sizer.Add(wx.StaticText(self, wx.ID_ANY, "User configuration"), 0)
        user_button_box = wx.BoxSizer(wx.HORIZONTAL)
        user_reload_button = wx.Button(self, wx.ID_ANY, label="Reload")
        user_button_box.Add(user_reload_button, 0)
        user_save_button = wx.Button(self, wx.ID_ANY, label="Save")
        self.Bind(wx.EVT_BUTTON, self.onUserReloadButton, user_reload_button)
        self.Bind(wx.EVT_BUTTON, self.onUserSaveButton, user_save_button)
        user_button_box.Add(user_save_button, 0)
        sizer.Add(user_button_box, 0)
        # Using a property grid for consistency, but the properties will be hardcoded
        self.user_config_editor = wxpg.PropertyGrid(self, style=wxpg.PG_SPLITTER_AUTO_CENTER | wxpg.PG_BOLD_MODIFIED)
        self.user_config_editor.SetMinSize(wx.Size(-1, 75))
        self.user_config_editor.SetMaxSize(wx.Size(-1, 75))
        self.user_config_editor.SetInitialSize(wx.Size(-1, 75))
        sizer.Add(self.user_config_editor, 1, wx.EXPAND)

        sizer.Add(wx.StaticText(self, wx.ID_ANY, "Channel Configuration"), 0)
        chan_button_box = wx.BoxSizer(wx.HORIZONTAL)
        self.chan_edit_button = wx.Button(self, label="Edit Channel")
        self.chan_edit_button.Disable()
        chan_button_box.Add(self.chan_edit_button, 0)
        self.chan_delete_button = wx.Button(self, label="Delete Channel")
        self.chan_delete_button.Disable()
        chan_button_box.Add(self.chan_delete_button, 0)
        self.Bind(wx.EVT_BUTTON, self.onChanEditButton, self.chan_edit_button)
        self.Bind(wx.EVT_BUTTON, self.onChanDeleteButton, self.chan_delete_button)
        sizer.Add(chan_button_box, 0)
        self.channel_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.channel_list.SetMinSize(wx.Size(430, 100))
        self.channel_list.SetMaxSize(wx.Size(430, 150))  # May want to adjust max size later
        self.channel_list.InsertColumn(0, '#', width=20)
        self.channel_list.InsertColumn(1, 'Role', width=110)
        self.channel_list.InsertColumn(2, 'Name', width=300)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onChannelSelected, self.channel_list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onChannelDeselected, self.channel_list)
        sizer.Add(self.channel_list, 1)

        sizer.Add(wx.StaticText(self, wx.ID_ANY, "Device Configuration"), 0)
        lc_button_box = wx.BoxSizer(wx.HORIZONTAL)
        lc_reload_button = wx.Button(self, label="Reload")
        lc_button_box.Add(lc_reload_button, 0)
        lc_save_button = wx.Button(self, label="Save")
        lc_button_box.Add(lc_save_button, 0)
        self.Bind(wx.EVT_BUTTON, self.onLCReloadButton, lc_reload_button)
        self.Bind(wx.EVT_BUTTON, self.onLCSaveButton, lc_save_button)
        sizer.Add(lc_button_box, 0)
        self.lc_config_editor = wxpg.PropertyGrid(self, style=wxpg.PG_SPLITTER_AUTO_CENTER | wxpg.PG_BOLD_MODIFIED)
        sizer.Add(self.lc_config_editor, 1, wx.EXPAND)

        sizer.Add(wx.StaticText(self, wx.ID_ANY, "Module Configuration"), 0)
        mc_button_box = wx.BoxSizer(wx.HORIZONTAL)
        mc_reload_button = wx.Button(self, label="Reload")
        mc_button_box.Add(mc_reload_button, 0)
        mc_save_button = wx.Button(self, label="Save")
        mc_button_box.Add(mc_save_button, 0)
        self.Bind(wx.EVT_BUTTON, self.onMCReloadButton, mc_reload_button)
        self.Bind(wx.EVT_BUTTON, self.onMCSaveButton, mc_save_button)
        sizer.Add(mc_button_box, 0)
        self.mc_config_editor = wxpg.PropertyGrid(self, style=wxpg.PG_SPLITTER_AUTO_CENTER | wxpg.PG_BOLD_MODIFIED)
        sizer.Add(self.mc_config_editor, 1, wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.selected_device = None  # Device last selected , so we don't have to call control's method every time
        self.this_node = None

        self.Bind(EVT_REFRESH_PANEL, self.refresh_panel_event)
        self.Bind(EVT_ADD_DEVICE, self.add_device_event)
        self.Bind(EVT_REMOVE_DEVICE, self.remove_device_event)

    def _reload_user_grid(self):
        if not self.selected_device or not self.this_node:
            return  # Just in case

        interface = shared.connected_interfaces[self.selected_device]
        user_values = interface.getMyNodeInfo().get("user", {})
        self.user_config_editor.Clear()
        self.user_config_editor.Append(wxpg.StringProperty("Short name", "short_name", interface.getShortName()))
        self.user_config_editor.Append(wxpg.StringProperty("Long name", "long_name", interface.getLongName()))
        self.user_config_editor.Append(wxpg.BoolProperty("Licensed mode", "is_licensed",
                                                         user_values.get("is_licensed", False)))
        # TODO: Is is_unmessageable the right name?
        self.user_config_editor.Append(wxpg.BoolProperty("Unmessageable", "is_unmessageable",
                                                         user_values.get("is_unmessageable", False)))
        self.SendSizeEvent()  # this is what it takes to get the user config editor to display w/o scroll bars

        return

    def _load_channel_list(self):
        if not self.selected_device or not self.this_node:
            return

        self.channel_list.DeleteAllItems()
        for chan in self.this_node.channels:
            self.channel_list.Append((chan.index, shared.channel_roles[chan.role], chan.settings.name))

        return

    def _reload_lc_grid(self):
        if not self.selected_device or not self.this_node:
            return  # Just in case

        self.lc_config_editor.Clear()
        self._load_config_values(self.this_node.localConfig, self.lc_config_editor)
        self.lc_config_editor.CollapseAll()

        return

    def _reload_mc_grid(self):
        if not self.selected_device or not self.this_node:
            return  # Just in case

        self.mc_config_editor.Clear()
        self._load_config_values(self.this_node.moduleConfig, self.mc_config_editor)
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
                setting_value = getattr(category_settings, setting_key)
                self._add_setting_to_grid(category_settings, setting_key, setting_value, grid, cat)

        return

    def _add_setting_to_grid(self, config, key, value, grid, category):
        # Note: there are duplicate keys across configuration categories, but property names must be unique.
        # So, create a unique name for each (e.g. Security_isManaged). Labels (the visible text) can be duplicated.

        # Determine the property and editor types
        if isinstance(value, bool):
            prop = wxpg.BoolProperty(str(key), f"{category}_{str(key)}", value)
            prop.SetEditor("CheckBox")
        elif isinstance(value, int):
            # If the protobuf says this is an enumerated type, get labels and values and make this an EnumProperty
            if config.DESCRIPTOR.fields_by_name[key].enum_type:
                labels, label_values = self._get_choices_from_protobuf(key, config.DESCRIPTOR)
                prop = wxpg.EnumProperty(str(key), f"{category}_{str(key)}", labels, label_values, value)
            # And if it isn't, then it's a plain ol' integer
            else:
                prop = wxpg.IntProperty(str(key), f"{category}_{str(key)}", value)
                prop.SetEditor("TextCtrl")
        elif isinstance(value, str):
            prop = wxpg.StringProperty(str(key), f"{category}_{str(key)}", str(value))
            prop.SetEditor("TextCtrl")
        else:  # A new one on us, make it a string for now
            prop = wxpg.StringProperty(str(key), f"{category}_{str(key)}", str(value))  # default to simple string
            prop.SetEditor("TextCtrl")

        # Add the setting to the propertygrid
        grid.AppendIn(category, prop)

        return

    @staticmethod
    def _get_choices_from_protobuf(key, descriptor):
        # If this was called, enum_type was already checked for None-ness. Assume it's not none.
        names = []
        values = []
        enum_type = descriptor.fields_by_name[key].enum_type

        for value_text in enum_type.values_by_name:
            names.append(value_text)
            values.append(enum_type.values_by_name[value_text].number)

        return names, values

    """
    A bit about the descriptor and the enum types contained therein:
    A "field" in this context is the setting name (e.g. 'baud')
    
    fields_by_name[field_name].enum_type is None if the field is not an enum type 
    enum_types_by_name keys are the names of the fields that are enum types (not used in this code but could be handy)
    
    config.DESCRIPTOR.fields_by_name[field_name].enum_type:
       .values_by_name: keys are the text values for just this field
       .values_by_name['text'].number is the int value of the text e.g. .values_by_name["BAUD_DEFAULT"].number = 0
       .values_by_number[int].name looks up the name of the int val e.g. values_by_number[0] = "BAUD_DEFAULT"
    """

    @staticmethod
    def _get_changed_categories(editor, config):
        changed_cats = []  # Categories that have changed settings
        cat_iterator = editor.GetIterator(wx.propgrid.PG_ITERATE_CATEGORIES)
        while not cat_iterator.AtEnd():
            cat = cat_iterator.GetProperty()
            cat_modified = False

            for child_index in range(cat.GetChildCount()):
                child = cat.Item(child_index)
                if editor.IsPropertyModified(child):
                    category_settings = getattr(config, cat.GetName())
                    setattr(category_settings, child.GetLabel(), child.GetValue())  # Must be the label not the name
                    cat_modified = True

            if cat_modified:
                changed_cats.append(cat.GetName())
            cat_iterator.Next()

        return changed_cats

    def _save_changed_categories(self, changed_cats, editor):
        saved_cats = []
        error_cats = []

        self.this_node.beginSettingsTransaction()
        for cat in changed_cats:
            # noinspection PyBroadException
            try:
                self.this_node.writeConfig(cat)
            except Exception:
                # TODO: Log the exception when logging is implemented
                error_cats.append(cat)
            else:
                saved_cats.append(cat)
        self.this_node.commitSettingsTransaction()

        if saved_cats:
            saved = ", ".join(saved_cats)
        else:
            saved = "None"
        if error_cats:
            errors = ", ".join(error_cats)
        else:
            errors = "None"
        wx.RichMessageDialog(self, f"Saved: {saved}, errors: {errors} \nGo to Devices panel to reconnect",
                             style=wx.OK | wx.ICON_INFORMATION).ShowModal()

        if not error_cats:
            editor.ClearModifiedStatus()

        # Assume the node had to reboot, even though it might not be true in all cases.
        # BLE devices in particular do not trigger the connection down topic, so kludge that.
        wx.PostEvent(self.GetTopLevelParent(),
                     fake_device_disconnect(name=self.selected_device,
                                            interface=shared.connected_interfaces[self.selected_device]))
        self.this_node = None

        return

    # wxPython events

    def onDevicePickerChoice(self, event):
        self.selected_device = self.device_picker.GetString(event.GetSelection())
        self.this_node = shared.connected_interfaces[self.selected_device].getNode('^local')
        self._load_channel_list()
        self._reload_user_grid()
        self._reload_mc_grid()
        self._reload_lc_grid()

    # TODO: Add event handler for device being deselected

    # noinspection PyUnusedLocal
    def onChannelSelected(self, event):
        self.chan_edit_button.Enable(True)
        self.chan_delete_button.Enable(True)

    # noinspection PyUnusedLocal
    def onChannelDeselected(self, event):
        self.chan_edit_button.Disable()
        self.chan_delete_button.Disable()

    # noinspection PyUnusedLocal
    def onChanEditButton(self, event):
        # TODO: Only allow editing of the first disabled channel
        # TODO: pass the index of the channel
        edit_dialog = ChannelEdit(self)
        edit_dialog.ShowModal()
        self._load_channel_list()

    # noinspection PyUnusedLocal
    def onChanDeleteButton(self, event):
        # TODO: What happens when you delete a channel in the middle of others?
        # TODO: reload channel list after this
        pass

    # noinspection PyUnusedLocal
    def onUserReloadButton(self, event):
        confirm = wx.RichMessageDialog(self, "Are you sure you want to reload the user configuration?",
                                       style=wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if confirm.ShowModal() == wx.ID_OK:
            self._reload_user_grid()
            wx.PostEvent(self.GetTopLevelParent(), set_status_bar(text="User configuration reloaded"))

    # noinspection PyUnusedLocal
    def onUserSaveButton(self, event):
        self.this_node.setOwner(self.user_config_editor.GetPropertyValueAsString("long_name"),
                                self.user_config_editor.GetPropertyValueAsString("short_name"),
                                self.user_config_editor.GetPropertyValue("is_licensed"),
                                self.user_config_editor.GetPropertyValue("is_unmessageable"))
        self.user_config_editor.ClearModifiedStatus()

        wx.RichMessageDialog(self, f"Saved user configuration\nGo to Devices panel to reconnect",
                             style=wx.OK | wx.ICON_INFORMATION).ShowModal()
        wx.PostEvent(self.GetTopLevelParent(),
                     fake_device_disconnect(name=self.selected_device,
                                            interface=shared.connected_interfaces[self.selected_device]))
        self.this_node = None

    # noinspection PyUnusedLocal
    def onLCReloadButton(self, event):
        confirm = wx.RichMessageDialog(self, "Are you sure you want to reload the device configuration?",
                                       style=wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if confirm.ShowModal() == wx.ID_OK:
            self._reload_lc_grid()
            wx.PostEvent(self.GetTopLevelParent(), set_status_bar(text="Device configuration reloaded"))

    # noinspection PyUnusedLocal
    def onLCSaveButton(self, event):
        changed_cats = self._get_changed_categories(self.lc_config_editor, self.this_node.localConfig)
        if changed_cats:
            self._save_changed_categories(changed_cats, self.lc_config_editor)
        else:  # No changed categories
            wx.RichMessageDialog(self, "No changes made", style=wx.OK | wx.ICON_INFORMATION).ShowModal()

    # noinspection PyUnusedLocal
    def onMCReloadButton(self, event):
        confirm = wx.RichMessageDialog(self, "Are you sure you want to reload the module configuration?",
                                       style=wx.OK | wx.CANCEL | wx.ICON_WARNING)
        if confirm.ShowModal() == wx.ID_OK:
            self._reload_mc_grid()
            wx.PostEvent(self.GetTopLevelParent(), set_status_bar(text="Module configuration reloaded"))

    # noinspection PyUnusedLocal
    def onMCSaveButton(self, event):
        changed_cats = self._get_changed_categories(self.mc_config_editor, self.this_node.moduleConfig)
        if changed_cats:
            self._save_changed_categories(changed_cats, self.mc_config_editor)
        else:  # No changed categories
            wx.RichMessageDialog(self, "No changes made", style=wx.OK | wx.ICON_INFORMATION).ShowModal()

    def add_device_event(self, event):
        device_name = event.name

        # Add the new device to the device picker and message buffer
        self.device_picker.Append(device_name)
        if self.device_picker.GetCount() == 1:  # this is the first device, auto-select it
            self.selected_device = device_name
            self.this_node = shared.connected_interfaces[self.selected_device].getNode('^local')
            self.device_picker.Select(0)
            self._reload_user_grid()
            self._load_channel_list()
            self._reload_mc_grid()
            self._reload_lc_grid()

    def remove_device_event(self, event):
        device_name = event.name

        index = self.device_picker.FindString(device_name)
        if index != wx.NOT_FOUND:
            self.device_picker.Delete(index)
        if self.selected_device == device_name:
            self.selected_device = None
            self.user_config_editor.Clear()
            self.channel_list.DeleteAllItems()
            self.lc_config_editor.Clear()
            self.mc_config_editor.Clear()

    # noinspection PyUnusedLocal
    def refresh_panel_event(self, event):
        self.Layout()
