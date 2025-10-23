import wx

import shared

class ChannelEdit(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent=parent)
        window_margin_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        name_box = wx.BoxSizer(wx.HORIZONTAL)
        name_box.Add(wx.StaticText(self, wx.ID_ANY, "Name"))
        self.channel_name = wx.TextCtrl(self, wx.ID_ANY, "")
        name_box.Add(self.channel_name, 1, wx.EXPAND)
        sizer.Add(name_box, 0, wx.EXPAND | wx.BOTTOM, 5)

        role_box = wx.BoxSizer(wx.HORIZONTAL)
        role_box.Add(wx.StaticText(self, wx.ID_ANY, "Role"))
        self.channel_role = wx.Choice(self, wx.ID_ANY, choices=shared.channel_roles)
        role_box.Add(self.channel_role)
        sizer.Add(role_box, 0, wx.BOTTOM, 5)
        self.mute = wx.CheckBox(self, wx.ID_ANY, "Mute this channel")
        sizer.Add(self.mute, 0, wx.BOTTOM, 10)

        key_box = wx.BoxSizer(wx.HORIZONTAL)
        key_box.Add(wx.StaticText(self, wx.ID_ANY, "Key"))
        self.key = wx.TextCtrl(self, wx.ID_ANY, "")
        key_box.Add(self.key, 1, wx.EXPAND)
        sizer.Add(key_box, 0, wx.EXPAND | wx.BOTTOM, 5)

        key_gen_box = wx.BoxSizer(wx.HORIZONTAL)
        key_gen_button = wx.Button(self, wx.ID_ANY, "Generate")
        key_gen_box.Add(key_gen_button)
        key_gen_box.Add(wx.StaticText(self, wx.ID_ANY, "Key size"))
        key_size = wx.Choice(self, wx.ID_ANY, choices=["128", "256"])
        key_size.SetSelection(0)
        key_gen_box.Add(key_size)
        sizer.Add(key_gen_box, 0, wx.BOTTOM, 10)

        mqtt_box = wx.BoxSizer(wx.HORIZONTAL)
        self.mqtt_uplink_enabled = wx.CheckBox(self, wx.ID_ANY, "MQTT Uplink Enabled")
        mqtt_box.Add(self.mqtt_uplink_enabled)
        self.mqtt_downlink_enabled = wx.CheckBox(self, wx.ID_ANY, "MQTT Downlink Enabled")
        mqtt_box.Add(self.mqtt_downlink_enabled)
        sizer.Add(mqtt_box, 0, wx.BOTTOM, 10)

        self.pos_enabled = wx.CheckBox(self, wx.ID_ANY, "Allow position requests")
        sizer.Add(self.pos_enabled, 0, wx.BOTTOM, 5)
        pos_box = wx.BoxSizer(wx.HORIZONTAL)
        pos_box.Add(wx.StaticText(self, wx.ID_ANY, "Position precision (bits, 1-32)"))
        self.pos_precision = wx.SpinCtrl(self, wx.ID_ANY, min=1, max=32, initial=16)  # TODO: maybe no initial?
        pos_box.Add(self.pos_precision)
        sizer.Add(pos_box, 0, wx.BOTTOM, 10)

        action_box = wx.BoxSizer(wx.HORIZONTAL)
        save_button = wx.Button(self, wx.ID_ANY, "Save")
        action_box.Add(save_button)
        cancel_button = wx.Button(self, wx.ID_ANY, "Cancel")
        action_box.Add(cancel_button)
        sizer.Add(action_box, 0)

        window_margin_sizer.Add(sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        self.SetSizer(window_margin_sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

"""
Editing a channel:
- Name
   - .settings.name
- Role (choice populated with shared.channel_roles values)
   - .role
- Key size and button to generate a key
   - Must be either 0 bytes (no crypto), 16 bytes (AES128), or 32 bytes (AES256)
- Key (holds either generated key or one pasted in)
   - .settings.psk
- Allow position requests, uplink enabled, downlink enabled (Booleans)
   - .settings: 'downlink_enabled', 'uplink_enabled', not sure about allow position requests
       - maybe allow position requests sets position precision to 0? Probably
   - .settings.module_settings: 'position_precision'
       - see https://meshtastic.org/docs/configuration/radio/channels/ for position precision info
       - not sure what happens for "in between" values that are not in the table
       - also see the "CLI" section near the bottom of the page, that talks about setting psk from the cli
           - look at the CLI source code to see how it gets from base64 to the stored value
- is_client_muted in settings.module_settings is to mute a channel

How do I get the key value to and from what's in the attribute?
   e.g. visible key = AQ==, psk value is "\001"
"""