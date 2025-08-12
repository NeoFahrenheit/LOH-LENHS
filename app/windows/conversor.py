"""
Arquivo resposavel pela conversor de unidades.
conversor.py
"""

import wx

class Conversor(wx.Frame):
    ''' Classe responsável pelo conversor de unidades. '''

    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.parent = parent
        self.SetTitle('Conversor de unidades')

        self.SetBackgroundColour(wx.NullColour)
        self.Center()

        self.Bind(wx.EVT_CLOSE, self.OnCloseApp)
        self.addItems()

    def addItems(self):
        ''' Adiciona os itens para a janela. '''

        masterSizer = wx.BoxSizer(wx.VERTICAL)

        self.toCubicMeters(masterSizer)
        self.toMCA(masterSizer)

        self.SetSizerAndFit(masterSizer)

    def toMCA(self, masterSizer):
        ''' Adiciona o campo da conversão para m.c.a (metros de coluna de água). '''

        dropdownList = ['bar', 'atm', 'kPa']
        self.mcaSelect = wx.ComboBox(self, -1, choices=dropdownList, style=wx.CB_READONLY)
        self.mcaSelect.SetMinSize((69, 23))
        self.mcaSelect.Bind(wx.EVT_COMBOBOX, self.OnMCA)
        self.mcaSelect.SetValue('bar')

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        lText = wx.StaticText(self, -1, 'De')
        rText = wx.StaticText(self, -1, 'para m.c.a', size=(60, 23))

        self.mcaInput = wx.TextCtrl(self, -1, size=(70, 23))
        self.mcaOutput = wx.TextCtrl(self, -1, style=wx.TE_READONLY | wx.CURSOR_NONE, size=(70, 23))

        bmp = wx.Bitmap('assets/images/copy.png')
        copyBtn = wx.Button(self, 1001, size=(23, 23))
        copyBtn.SetBitmap(bmp)
        tooltip = wx.ToolTip('Copiar')
        copyBtn.SetToolTip(tooltip)
        copyBtn.Bind(wx.EVT_BUTTON, self.OnCopyButton)

        sizer.Add(lText, flag=wx.RIGHT | wx.TOP, border=5)
        sizer.Add(self.mcaInput, flag=wx.RIGHT, border=5)
        sizer.Add(self.mcaSelect, flag=wx.RIGHT, border=5)
        sizer.Add(rText, flag=wx.RIGHT | wx.TOP, border=5)
        sizer.Add(self.mcaOutput, flag=wx.RIGHT, border=5)
        sizer.Add(copyBtn)
        masterSizer.Add(sizer, flag=wx.ALL, border=4)

        self.mcaInput.Bind(wx.EVT_TEXT, self.OnMCA)


    def toCubicMeters(self, masterSizer):
        ''' Adiciona o campo da conversão para metros cúbicos de água. '''

        dropdownList = ['l/s', 'l/h', 'l/min', 'm³/h', 'm³/min']

        self.cubicMetersSelect = wx.ComboBox(self, -1, choices=dropdownList, style=wx.CB_READONLY)
        self.cubicMetersSelect.SetMinSize((69, 23))
        self.cubicMetersSelect.Bind(wx.EVT_COMBOBOX, self.OnCubicMeters)
        self.cubicMetersSelect.SetValue('l/s')

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        lText = wx.StaticText(self, -1, 'De')
        rText = wx.StaticText(self, -1, 'para m³/s', size=(60, 23))

        self.metersInput = wx.TextCtrl(self, -1, size=(70, 23))
        self.metersOutput = wx.TextCtrl(self, -1, style=wx.TE_READONLY | wx.CURSOR_NONE, size=(70, 23))

        bmp = wx.Bitmap('assets/images/copy.png')
        copyBtn = wx.Button(self, 1000, size=(23, 23))
        copyBtn.SetBitmap(bmp)
        tooltip = wx.ToolTip('Copiar')
        copyBtn.SetToolTip(tooltip)
        copyBtn.Bind(wx.EVT_BUTTON, self.OnCopyButton)

        sizer.Add(lText, flag=wx.RIGHT | wx.TOP, border=5)
        sizer.Add(self.metersInput, flag=wx.RIGHT, border=5)
        sizer.Add(self.cubicMetersSelect, flag=wx.RIGHT, border=5)
        sizer.Add(rText, flag=wx.RIGHT | wx.TOP, border=5)
        sizer.Add(self.metersOutput, flag=wx.RIGHT, border=5)
        sizer.Add(copyBtn)
        masterSizer.Add(sizer, flag=wx.ALL, border=4)

        self.metersInput.Bind(wx.EVT_TEXT, self.OnCubicMeters)


    def OnCubicMeters(self, event):
        ''' Chamada quando o usuário digita algo no primeiro campo de conversão para m³/s. '''

        text = self.metersInput.GetValue()

        try:
            value = float(text)
        except:
            self.metersOutput.Clear()
            return

        if value <= 0:
            self.metersOutput.Clear()
            return

        select = self.cubicMetersSelect.GetValue()

        if select == 'l/s':
            self.metersOutput.SetValue('{:g}'.format(value / 1000))
        elif select == 'l/h':
            self.metersOutput.SetValue('{:g}'.format(value / 3_600_000))
        elif select == 'l/min':
            self.metersOutput.SetValue('{:g}'.format(value / 60_000))
        elif select == 'm³/h':
            self.metersOutput.SetValue('{:g}'.format(value / 3600))
        else:
            self.metersOutput.SetValue('{:g}'.format(value / 60))

    def OnMCA(self, event):
        ''' Chamada quando o usuário digita algo no primeiro campo de conversão para m.c.a. '''

        text = self.mcaInput.GetValue()

        try:
            value = float(text)
        except:
            self.mcaOutput.Clear()
            return

        if value <= 0:
            self.mcaOutput.Clear()
            return

        select = self.mcaSelect.GetValue()

        if select == 'bar':
            self.mcaOutput.SetValue('{:g}'.format(value * 10.19))
        elif select == 'atm':
            self.mcaOutput.SetValue('{:g}'.format(value * 10.33))
        else:
            self.mcaOutput.SetValue('{:g}'.format(value * 0.102))

    def OnCopyButton(self, event):
        ''' Chamada quando o botao de copiar é clicado. '''

        ID = event.Id
        data = wx.TextDataObject()

        if ID == 1000:
            data.SetText(self.metersOutput.GetValue())

        if ID == 1001:
            data.SetText(self.mcaOutput.GetValue())

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()


    def OnCloseApp(self, event):
        ''' Chamada quando o usuário clica no botão de fechar no canto superior direito. '''

        self.Destroy()
        self.parent.conversorWindow = None
