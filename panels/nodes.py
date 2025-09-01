import wx

class NodesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        wx.StaticText(self, label="Nodes")
