# GUI events

import wx.lib.newevent

set_status_bar, EVT_SET_STATUS_BAR = wx.lib.newevent.NewEvent()  # Update status bar text
refresh_panel, EVT_REFRESH_PANEL = wx.lib.newevent.NewEvent()  # Redraw the panel to show updates