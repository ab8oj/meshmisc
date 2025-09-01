import wx

class MessagesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        wx.StaticText(self, label="Messages")