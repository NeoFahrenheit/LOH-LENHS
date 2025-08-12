"""
Janela responsável pela classe da janela Sobre.
about.py
"""

import wx
import wx.richtext as rt
import webbrowser

class About(wx.Dialog):
    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.MINIMIZE_BOX) & (~wx.RESIZE_BORDER)
        super().__init__(parent, style=style)

        self.parent = parent
        self.SetTitle('Sobre')
        self.CenterOnParent()

        self.initUI()

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def initUI(self):
        ''' Inicializa a UI. '''

        master = wx.BoxSizer(wx.VERTICAL)

        # logo = wx.StaticBitmap(self, -1, wx.Bitmap('assets/images/iph_logo.png'))
        logo2 = wx.StaticBitmap(self, -1, wx.Bitmap('assets/images/lenhs_logo.png'))
        name = wx.StaticText(self, -1, 'LENHS / Diagnóstico Hidroenergético')
        ver = wx.StaticText(self, -1, f'Versão: {self.parent.version}')
        pyVer = wx.StaticText(self, -1, 'Python: 3.9.2')
        wxVer = wx.StaticText(self, -1, 'wxPython: 4.1.1 msw (phoenix)')
        self.rtc = rt.RichTextCtrl(self, -1, size=(300, 150), style=wx.TE_READONLY)
        self.rtc.GetCaret().Hide()
        self.rtc.Bind(wx.EVT_TEXT_URL, self.OnURL)

        self.writeInBold('Equipe:')
        self.rtc.Newline()
        self.rtc.AppendText('Leandro Arruda Monteiro (Programador)')
        self.rtc.Newline()
        self.rtc.AppendText('Pedro Guido Mottes Bassegio (Autor)')
        self.rtc.Newline()
        self.rtc.AppendText('Mauricio Dai Prá (Autor/Orientador)')
        self.rtc.Newline()
        self.rtc.Newline()

        self.writeInBold('Link de acesso:')
        self.rtc.Newline()
        self.rtc.AppendText('Laboratório de Obras Hidráulicas: ')
        self.writeInURL('http://www.ufrgs.br/loh', 'LOH')
        self.rtc.Newline()

        self.writeInBold('Email do LENHS:')
        self.rtc.Newline()
        self.writeBlueUnderlined('lenhs-iph@ufrgs.br')
        self.rtc.Newline()
        self.rtc.Newline()

        self.writeInBold('Ícones:')
        self.rtc.Newline()
        self.writeInURL('https://fonts.google.com/icons', 'Google Fonts')
        self.writeInURL('https://www.flaticon.com/authors/revicon', 'Revicon')
        self.writeInURL('https://www.flaticon.com/authors/freepik', 'Freepik')
        self.writeInURL('https://www.flaticon.com/authors/those-icons', 'Those Icons')
        self.writeInURL('https://www.flaticon.com/authors/eucalyp', 'Eucalyp')

        # self.rtc.Newline()
        # self.rtc.BeginAlignment(wx.TEXT_ALIGNMENT_CENTER)
        # self.rtc.WriteImage(wx.Bitmap('assets/images/iph_logo.png'))
        # self.rtc.Newline()

        # self.rtc.AppendText('Laboratório de Eficiência Energética e Hidráulica no Saneamento')


        # master.Add(logo, flag=wx.ALL | wx.ALIGN_CENTER, border=10)
        master.Add(logo2, flag=wx.ALL | wx.ALIGN_CENTER, border=10)
        master.Add(name, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER, border=10)
        master.Add(ver, flag=wx.ALIGN_CENTER)
        master.Add(pyVer, flag=wx.ALIGN_CENTER)
        master.Add(wxVer, flag=wx.ALIGN_CENTER)
        master.Add(self.rtc, flag=wx.ALL | wx.ALIGN_CENTER, border=15)

        self.SetSizerAndFit(master)
    def writeInBold(self, text):
        ''' Escreve `text` em self.rtc em negrito e depois muda para o estilo padrão. '''

        self.rtc.ApplyBoldToSelection()
        self.rtc.WriteText(text)
        self.rtc.SetDefaultStyle(wx.TextAttr())

    def writeInURL(self, url, text, appendNewLine=True):
        ''' Escreve `text` em self.rtc no estilo URL e depois muda para o estilo padrão. '''

        self.rtc.BeginTextColour(wx.BLUE)
        self.rtc.BeginUnderline()
        self.rtc.BeginURL(url)
        self.rtc.WriteText(text)
        if appendNewLine: self.rtc.AppendText('')

        self.rtc.EndTextColour()
        self.rtc.EndUnderline()
        self.rtc.EndURL()

    def OnURL(self, event):
        ''' Chamada quando algum link é clicado. Abre o link no browser padrão da máquina. '''

        webbrowser.open_new(event.GetString())

    def writeBlueUnderlined(self, text):
        ''' Escreve `text` em azul com sublinhado. '''

        self.rtc.BeginTextColour(wx.BLUE)
        self.rtc.BeginUnderline()

        self.rtc.WriteText(text)

        self.rtc.EndTextColour()
        self.rtc.EndUnderline()

    def OnCloseWindow(self, event):
        ''' Fecha a janela. '''

        self.Destroy()