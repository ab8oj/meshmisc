# GUI events

import wx.lib.newevent

set_status_bar, EVT_SET_STATUS_BAR = wx.lib.newevent.NewEvent()
refresh_panel, EVT_REFRESH_PANEL = wx.lib.newevent.NewEvent()
update_connection_status, EVT_UPDATE_CONNECTION_STATUS = wx.lib.newevent.NewEvent()
process_received_message, EVT_PROCESS_RECEIVED_MESSAGE = wx.lib.newevent.NewEvent()
add_device, EVT_ADD_DEVICE = wx.lib.newevent.NewEvent()
remove_device, EVT_REMOVE_DEVICE = wx.lib.newevent.NewEvent()
announce_new_device, EVT_ANNOUNCE_NEW_DEVICE = wx.lib.newevent.NewEvent()
node_updated, EVT_NODE_UPDATED = wx.lib.newevent.NewEvent()
child_closed, EVT_CHILD_CLOSED = wx.lib.newevent.NewEvent()
refresh_specific_panel, EVT_REFRESH_SPECIFIC_PANEL = wx.lib.newevent.NewEvent()
fake_device_disconnect, EVT_FAKE_DEVICE_DISCONNECT = wx.lib.newevent.NewEvent()