'''
Arquivo contem a classe TooltipFrame, que mostra as tooltips quando um botao de informacoes e clicado.
tooltip_frame.py
'''

import wx
import global_variables as gv

class TooltipFrame(wx.Frame):
    ''' Classe responsavel pela janela das tooltips. '''

    def __init__(self, parent, index):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.MINIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.index = index
        self.parent = parent

        self.CenterOnParent()
        self.showTooltip(index)

        self.Bind(wx.EVT_CLOSE, self.OnCloseApp)
        self.Show()

    def showTooltip(self, index):
        ''' Recebe um index e exibe a tooltip correspondente. '''

        text = wx.StaticText(self, -1, gv.tooltipList[index])
        imagePath = f'images/tooltip_images/tooltip{index}.png'
        image = wx.StaticBitmap(self, -1)
        image.SetBitmap(wx.Bitmap(imagePath))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text, flag=wx.ALL | wx.ALIGN_CENTRE, border=5)
        sizer.Add(image, flag=wx.ALL | wx.ALIGN_CENTRE, border=5)
        self.SetSizerAndFit(sizer)


    def OnCloseApp(self, event):
        ''' Funcao chamada quando o usuario clica no botao de fechar no canto superior direito. '''

        self.Destroy()
        self.parent.tooltipWindow = None