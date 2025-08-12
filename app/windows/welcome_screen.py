"""
welcome_screen.py
Arquivo contem as funcoes responsavel pela tela de boas vindas,
onde o usuario pode escolher com que tipo de função ele quer trabalhar.
"""

import wx
import app.global_variables as gv
import app.file_manager as fm
import app.windows.water_consumption as water_consumption
import app.windows.parameters as parameters
import app.windows.energy_consumption as energy_consumption
import app.windows.custos as custos
import app.windows.hydric as hydric
import app.windows.database as database
import app.pdf_export as pdf_export
import app.windows.about as about

SOFTWARE_NAME = 'LENHS / Diagnóstico Hidroenergético'

ACTIVATED_COLOR = '#c9f0c0'
HOVERED_COLOR = '#b0ff9e'

MSG = """Bem vindo ao software LOH / LENHS.\nEste software está em desenvolvimento.\nEm caso de qualquer problema, por favor,\nentre em contato com o bolsista responsável. """

ADDRESS = """Instituto de Pesquisas Hidráulicas
Universidade Federal do Rio Grande do Sul
Caixa Postal 15029
Av. Bento Gonçalves, 9500
91501-970 - Porto Alegre - RS - Brasil"""

class WelcomeWindow(wx.Frame):
    """ Cria a janela de boas vindas. """

    def __init__(self, parent, title):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, title=title, style=style)

        self.version = 1.0
        self.toolbar = self.CreateToolBar()

        # Criando a caixa de texto.
        self.welcomeMessage = wx.StaticText(self, label = MSG)

        # Vai receber a referencia da janela que o usuario escolher trabalhar.
        self.working_window = None
        self.databaseWindow = None

        self.setupToolbar(self.toolbar)
        self.init_buttons()

        self.CentreOnScreen()

    def setupToolbar(self, toolbar):
        """ Inicializa a toolbar. """

        openTool = toolbar.AddTool(wx.ID_OPEN, 'Abrir', wx.Bitmap('assets/images/open.png'), 'Abrir arquivo')
        closeTool = toolbar.AddTool(wx.ID_CLOSE, 'Fechar', wx.Bitmap('assets/images/close.png'), 'Fechar arquivo')
        pdfTool = toolbar.AddTool(wx.ID_ANY, 'Relatório', wx.Bitmap('assets/images/pdf.png'), 'Gerar relatório')
        toolbar.AddSeparator()
        infoTool = toolbar.AddTool(wx.ID_ABORT, 'Sobre', wx.Bitmap('assets/images/info.png'), 'Sobre o software')

        self.Bind(wx.EVT_TOOL, self.OnOpenFile, openTool)
        self.Bind(wx.EVT_TOOL, self.OnCloseFile, closeTool)
        self.Bind(wx.EVT_TOOL, self.OnPDF, pdfTool)
        self.Bind(wx.EVT_TOOL, self.OnAbout, infoTool)


        self.toolbar.Realize()

    def init_buttons(self):
        """ Cria os botoes da tela de boa vindas. """

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer = wx.BoxSizer(wx.VERTICAL)

        font = wx.Font(18, wx.FONTFAMILY_ROMAN, wx.DEFAULT, wx.DEFAULT)

        self.consumoBtn = wx.Button(self, wx.ID_ANY, 'Consumo de Água', size=(350, 60))
        self.consumoBtn.SetFont(font)
        buttonsSizer.Add(self.consumoBtn, flag=wx.TOP, border=10)

        self.parametrosBtn =  wx.Button(self, wx.ID_ANY, 'Parâmetros Operacionais', size=(350, 60))
        self.parametrosBtn.SetFont(font)
        buttonsSizer.Add(self.parametrosBtn, flag=wx.TOP, border=10)

        self.energyBtn =  wx.Button(self, wx.ID_ANY, 'Consumo de Energia e\nIndicadores Hidroenergéticos', size=(350, 60))
        self.energyBtn.SetFont(font)
        buttonsSizer.Add(self.energyBtn, flag=wx.TOP, border=10)
        self.energyBtn.Enable(False)

        self.custosBtn = wx.Button(self, wx.ID_ANY, 'Custos de Operação e\nIndicadores Financeiros', size=(350, 60))
        self.custosBtn.SetFont(font)
        buttonsSizer.Add(self.custosBtn, flag=wx.TOP, border=10)
        self.custosBtn.Enable(False)

        self.hidricoBtn = wx.Button(self, wx.ID_ANY, 'Balanço Hídrico de Reservatório', size=(350, 60))
        self.hidricoBtn.SetFont(font)
        buttonsSizer.Add(self.hidricoBtn, flag=wx.TOP, border=10)

        self.databaseBtn = wx.Button(self, wx.ID_ANY, 'Banco de Dados', size=(350, 60))
        self.databaseBtn.SetFont(font)
        buttonsSizer.Add(self.databaseBtn, flag=wx.TOP, border=85)

        self.consumoBtn.Bind(wx.EVT_BUTTON, self.OnConsumo)
        self.parametrosBtn.Bind(wx.EVT_BUTTON, self.OnParametros)
        self.custosBtn.Bind(wx.EVT_BUTTON, self.OnCustos)
        self.hidricoBtn.Bind(wx.EVT_BUTTON, self.OnHidrico)
        self.databaseBtn.Bind(wx.EVT_BUTTON, self.OnDatabase)

        self.energyBtn.Bind(wx.EVT_BUTTON, self.OnEnergy)
        self.energyBtn.Bind(wx.EVT_ENTER_WINDOW, lambda event: self.OnHover(event, self.energyBtn))
        self.energyBtn.Bind(wx.EVT_LEAVE_WINDOW, lambda event: self.OnLeaveHover(event, self.energyBtn))

        leftSizer.Add(buttonsSizer, flag=wx.LEFT, border=10)

        hSizer.Add(leftSizer)
        hSizer.Add(rightSizer, flag=wx.ALL, border=20)

        self.initRightBox(rightSizer)
        self.SetSizerAndFit(hSizer)

    def initRightBox(self, box):
        ''' Inicializa o BoxSizer direito. '''

        iphImg = wx.Bitmap('assets/images/iph_logo.png', wx.BITMAP_TYPE_ANY)
        iphBitmap = wx.StaticBitmap(self, -1, iphImg)

        lensImg = wx.Bitmap('assets/images/lenhs_logo.png', wx.BITMAP_TYPE_ANY)
        lensBitmap = wx.StaticBitmap(self, -1, lensImg)

        baseFont = wx.Font(10, wx.FONTFAMILY_ROMAN, wx.NORMAL, wx.NORMAL)

        self.welcomeMessage.SetFont(baseFont)

        address = wx.StaticText(self, -1, ADDRESS)
        address.SetFont(baseFont)

        box.Add(lensBitmap, flag=wx.ALIGN_CENTRE)
        box.Add(iphBitmap, flag=wx.ALIGN_CENTRE)
        box.Add(self.welcomeMessage, flag=wx.ALIGN_LEFT | wx.TOP, border=14)
        box.Add(address, flag=wx.ALIGN_LEFT | wx.TOP, border=14)

    def OnOpenFile(self, event):
        """ Chamada quando o usuario clica para abrir um arquivo. """

        dialog = wx.FileDialog(self, f"Escolha um arquivo {gv.file_suffix}", gv.file_dir, '', f'*{gv.file_suffix}*', wx.FD_OPEN)
        # Se a ID do Modal for OK, significa que o usuario escolheu um arquivo.
        if dialog.ShowModal() == wx.ID_OK:
            if gv.opened_file:
                gv.opened_file.close()

            fm.openAndUpdateFileVariables(dialog)
            self.SetTitle(f'{gv.filename} - {SOFTWARE_NAME}')

            if fm.isFileIntegrityOK():
                self.refreshButtons()
            else:
                fm.clearFileVariables()
                self.SetTitle(f'{SOFTWARE_NAME}')

                message = wx.MessageDialog(self, 'O arquivo carregado não contém as informações necessárias ou foi corrompido.',
                'Erro encontrado', wx.OK | wx.ICON_ERROR)

                message.ShowModal()
                message.Destroy()

    def OnCloseFile(self, event):
        """ Chamada quando o usuario clica para fechar o arquivo. """

        fm.clearFileVariables()

        self.energyBtn.Enable(False)
        self.energyBtn.SetBackgroundColour(wx.NullColour)

        self.custosBtn.Enable(False)
        self.custosBtn.SetBackgroundColour(wx.NullColour)

        self.SetTitle(f'{SOFTWARE_NAME}')

    def OnPDF(self, event):
        ''' Chamada quando o usuário clica para gerar o relatório em .pdf. '''

        if not gv.opened_file:
            dialog = wx.MessageDialog(self, 'Abra um arquivo para gerar o relatório em .pdf, por favor.', 'Arquivo não carregado', wx.ICON_ERROR)
            dialog.ShowModal()
            return

        window = pdf_export.ExportPDF(self)
        window.ShowModal()

    def OnAbout(self, event):
        ''' Chamada quando o usuário clica no botão Sobre. '''

        window = about.About(self)
        window.ShowModal()

    def refreshButtons(self):
        """ Atualiza o estado dos botoes e o titulo da janela conforme o arquivo aberto. """

        if gv.opened_file:
            self.SetTitle(f'{gv.filename} - {SOFTWARE_NAME}')
            isParamFound = False
            if '#parameters_start' in gv.fileStartIndices.keys():
                isParamFound = True

            if isParamFound:
                self.energyBtn.Enable(True)
                self.energyBtn.SetBackgroundColour(ACTIVATED_COLOR)

                self.custosBtn.Enable(True)
                self.custosBtn.SetBackgroundColour(ACTIVATED_COLOR)
            else:
                self.energyBtn.Enable(False)
                self.energyBtn.SetBackgroundColour(wx.NullColour)

                self.custosBtn.Enable(False)
                self.custosBtn.SetBackgroundColour(wx.NullColour)

        else:
            self.energyBtn.Enable(False)
            self.energyBtn.SetBackgroundColour(wx.NullColour)

            self.custosBtn.Enable(False)
            self.custosBtn.SetBackgroundColour(wx.NullColour)


            self.SetTitle(f'{SOFTWARE_NAME}')

    def OnConsumo(self, event):
        """ Cria a janela de consumo e fecha a de boas vindas. """

        self.Hide()
        self.working_window = water_consumption.CreateWaterWindow(self)
        self.working_window.Show()

        event.Skip()

    def OnParametros(self, event):
        """ Cria a janela de parametros operacionais do sistema e fecha a de boas vindas. """

        self.Hide()
        self.working_window = parameters.ParametersWindow(self)
        self.working_window.Show()

        event.Skip()

    def OnEnergy(self, event):
        """ Cria a janela de consumo energetico e indicadores hidroenergeticos e fecha a tela de boas vindas. """

        self.Hide()
        self.working_window = energy_consumption.EnergyConsumption(self)
        self.working_window.Show()

        event.Skip()

    def OnCustos(self, event):
        """ Cria a janela de Custos de Operação e Indicadores Financeiros e fecha a tela de boas vindas. """

        self.Hide()
        self.working_window = custos.Custos(self)
        self.working_window.Show()

        event.Skip()

    def OnHidrico(self, event):
        """ Cria a janela de Custos de Operacao e Indicadores Financeiros e fecha a tela de boas vindas. """

        self.Hide()
        self.working_window = hydric.HydricBalance(self)
        self.working_window.Show()

        event.Skip()

    def OnDatabase(self, event):
        """ Abre a janela do banco de dados. """

        if not self.databaseWindow:
            self.databaseWindow = database.Database(self)
            self.databaseWindow.Show()

    def OnHover(self, event, button):
        """ Chamada quando o ponteiro do mouse esta sob algum botao ativavel. """

        button.SetBackgroundColour(HOVERED_COLOR)

    def OnLeaveHover(self, event, button):
        """ Chamada quando o ponteiro do mouse sai sob algum botao ativavel. """

        button.SetBackgroundColour(ACTIVATED_COLOR)

    def show_(self):
        """ Mostra novamente a tela de boas vindas. """

        self.Show()
        self.working_window = None
        self.refreshButtons()

    def destroy_(self):
        """ Destroi a janela de boas vindas. Usava para fechar completamente o programa.
        Deve, obrigatoriamente, ser chamada quando o usuario sai do programa fora da tela de
        boas vindas. """

        self.Destroy()