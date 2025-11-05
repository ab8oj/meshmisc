import base64
import os

import wx

from gui import shared


class ChannelEdit(wx.Dialog):
    def __init__(self, parent, channel_info, channel_index, this_node, device_name):
        super().__init__(parent=parent)
        self.channel_info = channel_info
        self.channel_index = channel_index
        self.this_node = this_node
        self.device_name = device_name
        window_margin_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        name_box = wx.BoxSizer(wx.HORIZONTAL)
        name_box.Add(wx.StaticText(self, wx.ID_ANY, "Name"))
        self.channel_name = wx.TextCtrl(self, wx.ID_ANY, "", size=wx.Size(350, -1))
        name_box.Add(self.channel_name, 0)
        sizer.Add(name_box, 0, wx.EXPAND | wx.BOTTOM, 5)
        sizer.Add(wx.StaticLine(self, wx.ID_ANY), 0, wx.EXPAND | wx.BOTTOM, 5)

        role_box = wx.BoxSizer(wx.HORIZONTAL)
        role_box.Add(wx.StaticText(self, wx.ID_ANY, "Role"))
        self.channel_role = wx.Choice(self, wx.ID_ANY, choices=shared.channel_roles)
        role_box.Add(self.channel_role)
        sizer.Add(role_box, 0, wx.BOTTOM, 5)
        self.mute = wx.CheckBox(self, wx.ID_ANY, "Mute this channel")
        sizer.Add(self.mute, 0, wx.BOTTOM, 10)
        sizer.Add(wx.StaticLine(self, wx.ID_ANY), 0, wx.EXPAND | wx.BOTTOM, 5)

        key_box = wx.BoxSizer(wx.HORIZONTAL)
        key_box.Add(wx.StaticText(self, wx.ID_ANY, "Key"))
        self.key = wx.TextCtrl(self, wx.ID_ANY, "", size=wx.Size(400, -1))
        key_box.Add(self.key, 0)
        sizer.Add(key_box, 0, wx.EXPAND | wx.BOTTOM, 5)
        key_gen_button = wx.Button(self, wx.ID_ANY, "Generate random key")
        self.Bind(wx.EVT_BUTTON, self.onKeyGenButton, key_gen_button)
        sizer.Add(key_gen_button, 0, wx.BOTTOM, 5)
        sizer.Add(wx.StaticLine(self, wx.ID_ANY), 0, wx.EXPAND | wx.BOTTOM, 5)

        mqtt_box = wx.BoxSizer(wx.HORIZONTAL)
        self.mqtt_uplink_enabled = wx.CheckBox(self, wx.ID_ANY, "MQTT Uplink")
        mqtt_box.Add(self.mqtt_uplink_enabled)
        self.mqtt_downlink_enabled = wx.CheckBox(self, wx.ID_ANY, "MQTT Downlink")
        mqtt_box.Add(self.mqtt_downlink_enabled)
        sizer.Add(mqtt_box, 0, wx.BOTTOM, 10)
        sizer.Add(wx.StaticLine(self, wx.ID_ANY), 0, wx.EXPAND | wx.BOTTOM, 5)

        self.pos_enabled = wx.CheckBox(self, wx.ID_ANY, "Allow position requests")
        self.Bind(wx.EVT_CHECKBOX, self.onPosEnabledCheckbox, self.pos_enabled)
        sizer.Add(self.pos_enabled, 0, wx.BOTTOM, 5)
        pos_box = wx.BoxSizer(wx.HORIZONTAL)
        pos_box.Add(wx.StaticText(self, wx.ID_ANY, "Position precision (bits, 1-32)"))
        self.pos_precision = wx.SpinCtrl(self, wx.ID_ANY, min=1, max=32, initial=16)
        pos_box.Add(self.pos_precision)
        sizer.Add(pos_box, 0, wx.BOTTOM, 10)
        sizer.Add(wx.StaticLine(self, wx.ID_ANY), 0, wx.EXPAND | wx.BOTTOM, 5)

        action_box = wx.BoxSizer(wx.HORIZONTAL)
        save_button = wx.Button(self, wx.ID_ANY, "Save")
        self.Bind(wx.EVT_BUTTON, self.onSaveButton, save_button)
        action_box.Add(save_button)
        cancel_button = wx.Button(self, wx.ID_ANY, "Cancel")
        self.Bind(wx.EVT_BUTTON, self.onCancelButton, cancel_button)
        action_box.Add(cancel_button)
        sizer.Add(action_box, 0)

        window_margin_sizer.Add(sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        self.SetSizerAndFit(window_margin_sizer)
        self.SetAutoLayout(True)

        self._load_channel_info()

    # === Helpers and private functions

    def _load_channel_info(self):
        self.channel_name.SetValue(self.channel_info.settings.name)
        # noinspection PyTypeHints
        role_string_index = self.channel_role.FindString(shared.channel_roles[self.channel_info.role])
        self.channel_role.SetSelection(role_string_index)
        self.mute.SetValue(self.channel_info.settings.module_settings.is_client_muted)
        self.key.SetValue(base64.b64encode(self.channel_info.settings.psk).decode('utf-8'))
        self.mqtt_uplink_enabled.SetValue(self.channel_info.settings.uplink_enabled)
        self.mqtt_downlink_enabled.SetValue(self.channel_info.settings.downlink_enabled)
        if self.channel_info.settings.module_settings.position_precision == 0:
            self.pos_enabled.SetValue(False)
            self.pos_precision.Disable()
        else:
            self.pos_enabled.SetValue(True)
            self.pos_precision.Enable()
        self.pos_precision.SetValue(self.channel_info.settings.module_settings.position_precision)
        return

    def _save_channel_info(self):
        self.channel_info.settings.name = self.channel_name.GetValue()
        # Don't assume the roles in the choice list are in the same order as in shared.channel_roles
        role_string = self.channel_role.GetString(self.channel_role.GetSelection())
        self.channel_info.role = shared.channel_roles.index(role_string)
        self.channel_info.settings.module_settings.is_client_muted = self.mute.GetValue()
        self.channel_info.settings.psk = base64.b64decode(self.key.GetValue().encode('utf-8'))
        self.channel_info.settings.uplink_enabled = self.mqtt_uplink_enabled.GetValue()
        self.channel_info.settings.downlink_enabled = self.mqtt_downlink_enabled.GetValue()
        if self.pos_enabled.GetValue():
            self.channel_info.settings.module_settings.position_precision = self.pos_precision.GetValue()
        else:
            self.channel_info.settings.module_settings.position_precision = 0

        self.this_node.writeChannel(self.channel_index)

    # === wxPython events

    # noinspection PyUnusedLocal
    def onKeyGenButton(self, event):
        self.key.SetValue(base64.b64encode(os.urandom(32)).decode('utf-8'))

    # noinspection PyUnusedLocal
    def onPosEnabledCheckbox(self, event):
        if self.pos_enabled.GetValue():
            self.pos_precision.Enable()
        else:
            self.pos_precision.Disable()

    # noinspection PyUnusedLocal
    def onSaveButton(self, event):
        self._save_channel_info()
        self.EndModal(wx.ID_OK)

    # noinspection PyUnusedLocal
    def onCancelButton(self, event):
        self.EndModal(wx.ID_CANCEL)
