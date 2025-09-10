# GUI events

import wx.lib.newevent

set_status_bar, EVT_SET_STATUS_BAR = wx.lib.newevent.NewEvent()
refresh_panel, EVT_REFRESH_PANEL = wx.lib.newevent.NewEvent()
update_connection_status, EVT_UPDATE_CONNECTION_STATUS = wx.lib.newevent.NewEvent()
process_received_message, EVT_PROCESS_RECEIVED_MESSAGE = wx.lib.newevent.NewEvent()
