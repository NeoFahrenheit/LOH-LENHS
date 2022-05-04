"""
Arquivo contem a classe responsavel pela janela de Consumo de Energia e Indicadores Hidroenergeticos.
energy_consumption.py
"""

import wx
import os
import conversor
import database
import file_manager as fm
import global_variables as gv
import tooltip_frame as tf

class EnergyConsumption(wx.Frame):
    """ Classe responsavel pela janela de Consumo de Energia e Indicadores Hidroenergeticos. """

    def __init__(self, parent):
        wx.Frame.__init__(self, parent)

        self.menu = wx.MenuBar()
        self.toolbar = self.CreateToolBar()
        self.status_bar = self.CreateStatusBar()

        self.WINDOW_NAME = 'Consumo Energético e Indicadores Hidroenergéticos'

        self.vazaoBombeada = 0
        self.alturaNanometrica = 0
        self.rendimentoMotor = 0
        self.rendimentoBomba = 0
        self.bombasParalelo = 0
        self.operacaoHorarioPonta = 0
        self.operacaoHorarioForaPonta = 0

        self.summaryTextField = []
        self.resultTextField = []

        self.conversorWindow = None
        self.tooltipWindow = None
        self.databaseWindow = None

        self.isButtonClicked = False

        self.SetMinSize((691, 494))
        self.SetMaxSize((691, 494))
        self.SetTitle('Consumo de Energia e Indicadores Hidroenergeticos')

        self.Bind(wx.EVT_CLOSE, self.OnCloseApp)

        self.setupMenuBar(self.menu)
        self.setupToolsMenu(self.menu)
        self.SetMenuBar(self.menu)
        self.setupToolbar(self.toolbar)
        self.initUI()
        self.SetDoubleBuffered(True)

        self.getDataFromFile()
        self.CenterOnParent()

    def initUI(self):
        """ Inicializa a UI. """

        self.computeButton = wx.Button(self, wx.ID_ANY, 'Calcular', size=(200, 30))
        self.computeButton.SetBackgroundColour('#A1BAEA')
        self.computeButton.Bind(wx.EVT_BUTTON, self.OnCalculate)

        self.topVerticalSizer = wx.BoxSizer(wx.VERTICAL)

        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        self.topVerticalSizer.Add(self.topSizer, flag=wx.TOP, border=2)
        self.addItemsToTopSizer()

        self.topVerticalSizer.Add(self.computeButton, flag=wx.ALL | wx.ALIGN_CENTER, border=5)

        self.bottomSizer = wx.BoxSizer(wx.VERTICAL)
        self.topVerticalSizer.Add(self.bottomSizer, flag=wx.TOP, border=2)
        self.addItemsToBottomSizer()

        self.SetSizerAndFit(self.topVerticalSizer)

    def setupMenuBar(self, menu):
        """ Inicializa o menu. """

        file_menu = wx.Menu()

        # Criando os itens do menu.
        open_item_menu = file_menu.Append(wx.ID_OPEN, '&Abrir\tCtrl+A', 'Abrir um arquivo')
        file_menu.AppendSeparator()
        home_item_menu = file_menu.Append(wx.ID_HOME, 'Voltar para Home', 'Voltar para a tela de boas vindas')
        exit_item_menu = file_menu.Append(wx.ID_EXIT, 'Sair', 'Sair do programa')

        # Criando os bindings.
        self.Bind(wx.EVT_MENU, self.OnOpenFile, open_item_menu)
        self.Bind(wx.EVT_MENU, lambda event: self.OnQuit(event, is_exit=False), home_item_menu)
        self.Bind(wx.EVT_MENU, lambda event: self.OnQuit(event, is_exit=True), exit_item_menu)

        menu.Append(file_menu, 'Arquivo')

    def setupToolsMenu(self, menu):
        ''' Inicializa o menu de 'Ferramentas'. '''

        file_menu = wx.Menu()

        conversor_item_menu = file_menu.Append(-1, '&Conversor', 'Abrir o conversor de unidades')
        database_item_menu = file_menu.Append(-1, '&Banco de dados', 'Abrir o banco de dados')

        self.Bind(wx.EVT_MENU, self.OnConversor, conversor_item_menu)
        self.Bind(wx.EVT_MENU, self.OnDatabase, database_item_menu)

        menu.Append(file_menu, 'Ferramentas')

        self.SetMenuBar(menu)

    def setupToolbar(self, toolbar):
        """ Inicializa a toolbar. """

        openTool = toolbar.AddTool(wx.ID_OPEN, 'Abrir', wx.Bitmap('images/open.png'), 'Abrir arquivo')
        conversorTool = toolbar.AddTool(wx.ID_ANY, 'Conversor', wx.Bitmap('images/calculator.png'), 'Conversor de unidades')
        databaseTool = toolbar.AddTool(wx.ID_ANY, 'Banco de dados', wx.Bitmap('images/database.png'), 'Banco de dados')
        toolbar.AddSeparator()
        homeTool = toolbar.AddTool(wx.ID_HOME, 'Home', wx.Bitmap('images/home.png'), 'Voltar para Home')

        self.Bind(wx.EVT_TOOL, self.OnOpenFile, openTool)
        self.Bind(wx.EVT_TOOL, self.OnConversor, conversorTool)
        self.Bind(wx.EVT_TOOL, self.OnDatabase, databaseTool)
        self.Bind(wx.EVT_TOOL, lambda event: self.OnQuit(event, is_exit=False), homeTool)

        self.toolbar.Realize()

    def OnOpenFile(self, event):
        """ Abre um arquivo e popula o texto do resumo. """

        dialog = wx.FileDialog(self, f"Escolha um arquivo {gv.file_suffix}", gv.file_dir, '', f'*{gv.file_suffix}*', wx.FD_OPEN)
        # Se a ID do Modal for OK, significa que o usuário escolheu um arquivo.
        if dialog.ShowModal() == wx.ID_OK:
            if gv.opened_file:
                gv.opened_file.close()

            gv.filename = dialog.GetFilename()
            gv.file_dir = dialog.GetDirectory()
            gv.file_path = os.path.join(gv.file_dir, gv.filename)
            gv.opened_file = open(gv.file_path, 'r')

            self.isButtonClicked = False

            self.SetTitle(f'{gv.filename} - {self.WINDOW_NAME}')
            if not self.getDataFromFile():
                message = wx.MessageDialog(self, 'O arquivo carregado não contém as informações necessárias ou foi corrompido.',
                'Erro encontrado', wx.OK | wx.ICON_ERROR)

                message.ShowModal()
                message.Destroy()

                fm.clearFileVariables()

                self.OnQuit(event, is_exit=False)

            else:
                for i in range(0, len(self.resultTextField)):
                    self.resultTextField[i].SetLabel('---- ')

                    if i == 5:
                        self.resultTextField[i].SetBackgroundColour(wx.NullColour)

        self.Layout()

    def OnCloseApp(self, event):
        """ Chamada quando o usuário clica no X da janela para sair do programa. """

        self.OnQuit(event, is_exit=True)


    def OnQuit(self, event, is_exit):
        """ Chamada quando o usuário tenta sair, seja para fechar o programa ou voltar pra Home. """

        self.Destroy()
        if is_exit:
            gv.welcome_screen.destroy_()
        else:
            gv.welcome_screen.show_()

    def getDataFromFile(self):
        """ Puxa as informações relevantes do arquivo para a tela de variáveis.
        Retorna True em caso de sucesso. """

        gv.opened_file.seek(0)
        lines = gv.opened_file.readlines()
        if not lines:
            return False

        index = 0
        found = False
        for line in lines:
            if line.strip() == '#parameters_start':
                found = True
                break
            index += 1

        if not found:
            return False

        gv.opened_file.seek(0)
        data = gv.opened_file.readlines()[index + 1 : index + 8]

        for i in range(0, 7):
            if i == 0:
                self.summaryTextField[i].SetLabel(f'{self.returnFormatted10(data[i].strip())} ')
                self.vazaoBombeada = float(data[i].strip())
            if i == 1:
                self.summaryTextField[i].SetLabel(f'{self.returnFormatted10(data[i].strip())} ')
                self.alturaNanometrica = float(data[i].strip())
            if i == 2:
                self.summaryTextField[i].SetLabel(f'{data[i].strip()} ')
                self.rendimentoMotor = float(data[i].strip())
            if i == 3:
                self.summaryTextField[i].SetLabel(f'{data[i].strip()} ')
                self.rendimentoBomba = float(data[i].strip())
            if i == 4:
                self.summaryTextField[i].SetLabel(f'{data[i].strip()} ')
                self.bombasParalelo = int(data[i].strip())
            if i == 5:
                self.summaryTextField[i].SetLabel(f'{data[i].strip()} ')
                self.operacaoHorarioPonta = float(data[i].strip())
            if i == 6:
                self.summaryTextField[i].SetLabel(f'{data[i].strip()} ')
                self.operacaoHorarioForaPonta = float(data[i].strip())

        self.SetTitle(f'{gv.filename} - {self.WINDOW_NAME}')

        return True

    def addItemsToTopSizer(self):
        ''' Adiciona os itens no topSizer. '''

        text = wx.StaticText(self, -1, 'Variáveis preenchidas em Parâmetros do Sistema...')
        text.SetFont( wx.Font(10, wx.FONTFAMILY_ROMAN, wx.NORMAL, wx.BOLD, False) )

        self.topSizer.Add(text, flag=wx.BOTTOM, border=10)
        self.topSizer.Add(self.getSummaryBox('Vazão Bombeada\t\t\t     (m³/s)', '', 0), flag=wx.BOTTOM, border=2)
        self.topSizer.Add(self.getSummaryBox('Altura Manométrica\t\t\t(m)', '', 1), flag=wx.BOTTOM, border=2)
        self.topSizer.Add(self.getSummaryBox('Rendimento do Motor\t\t\t(%)', '', 2), flag=wx.BOTTOM, border=2)
        self.topSizer.Add(self.getSummaryBox('Rendimento da Bomba\t\t\t(%)', '', 3), flag=wx.BOTTOM, border=2)
        self.topSizer.Add(self.getSummaryBox('Bombas em paralelo', '', 4), flag=wx.BOTTOM, border=2)
        self.topSizer.Add(self.getSummaryBox('Tempo dentro do Horário de Ponta     (h/dia)', '', 5), flag=wx.BOTTOM, border=2)
        self.topSizer.Add(self.getSummaryBox('Tempo fora do Horário de Ponta       (h/dia)', '', 6), flag=wx.BOTTOM, border=2)

    def addItemsToBottomSizer(self):
        ''' Adiciona os itens na bottomSizer. '''

        self.bottomSizer.Add(self.getSummaryBox('Consumo na ponta \t\t(kWh/mês)', '---- ', 7, True), flag=wx.BOTTOM, border=2)
        self.bottomSizer.Add(self.getSummaryBox('Consumo fora da ponta \t\t(kWh/mês)', '---- ', 8, True), flag=wx.BOTTOM, border=2)
        self.bottomSizer.Add(self.getSummaryBox('Consumo Total \t\t\t(kWh/mês)', '---- ', 9, True), flag=wx.BOTTOM, border=2)
        self.bottomSizer.Add(self.getSummaryBox('Volume Bombeado\t\t\t(m³/mês)', '---- ', 10, True), flag=wx.BOTTOM, border=2)
        self.bottomSizer.Add(self.getSummaryBox('Consumo Específico \t\t(kWh/m³)', '---- ', 11, True), flag=wx.BOTTOM, border=2)
        self.bottomSizer.Add(self.getSummaryBox('Consumo Específico Normalizado  (kWh/m³/100m)', '---- ', 12, True), flag=wx.BOTTOM, border=2)

    def getSummaryBox(self, text, value, index, isResult=False):
        """ Retorna um wx.Panel com o texto e o valor associado (como uma wx.BoxerSizer HORIZONTAL) """

        tColor = '#c7c3c3'
        lPanel = wx.Panel(self)
        lPanel.SetBackgroundColour(tColor)
        rPanel = wx.Panel(self)
        rPanel.SetBackgroundColour(wx.NullColour)

        hBox = wx.BoxSizer(wx.HORIZONTAL)

        font = wx.Font(13, wx.MODERN, wx.NORMAL, wx.NORMAL, False)

        lText = wx.StaticText(lPanel, wx.ID_ANY, text, size=(450, 5))
        lText.SetFont(font)
        rText = wx.StaticText(rPanel, wx.ID_ANY, value, size=(200, 5), style=wx.TE_RIGHT)
        rText.SetFont(font)

        # Adicionando a referência da StaticText a lista.
        if isResult:
            self.resultTextField.append(rText)
        else:
            self.summaryTextField.append(rText)

        hBox.Add(lPanel)
        hBox.Add(rPanel)

        # Cria as tooltips
        image = wx.Bitmap('images/question.png')
        tooltip = wx.ToolTip(gv.tooltipList[index])
        tooltip.SetAutoPop(30_000)
        btn = wx.Button(self, id=1000 + index, size=(20, 20))
        btn.SetToolTip(tooltip)
        btn.SetBitmap(image)
        btn.Bind(wx.EVT_BUTTON, self.OnTooltipButton)

        hBox.Add(btn, flag=wx.LEFT, border=5)

        return hBox


    def OnTooltipButton(self, event):
        ''' Chamada quando um botão de tooltip for clicado. '''

        working_tooltips = [1]
        ID = event.GetEventObject().Id
        ID -= 1000

        if ID not in working_tooltips:
            return

        if not self.tooltipWindow:
            self.tooltipWindow = tf.TooltipFrame(self, ID)
        else:
            self.tooltipWindow.OnCloseApp(None)
            self.tooltipWindow = tf.TooltipFrame(self, ID)

    def returnFormatted10(self, number):
        """ Retorna o número no formato de string com 10 casas decimais.

        Parâmetros
        ----------
        number : int """

        return f'{float(number):.10f}'

    def OnCalculate(self, event):
        """ Funcao e chamda quando o usuário clica em calcular. """

        if not self.isButtonClicked:
            self.isButtonClicked = True
        else:
            return

        # Pegando os valores para a exibicao dos resultados.
        CEP = f'{self.energiaPonta(True):.2f}'
        CEFP = f'{self.energiaPonta(False):.2f}'
        CET = f'{self.consumoTotal():.2f}'
        VB = f'{self.volumeBombeado():.2f}'
        CE = f'{self.consumoEspecifico():.2f}'
        CEN = f'{self.consumoEspecificoNormalizado():.2f}'

        # Atualizando os compos de texto com os resultados.
        self.resultTextField[0].SetLabel(f'{CEP} ')
        self.resultTextField[1].SetLabel(f'{CEFP} ')
        self.resultTextField[2].SetLabel(f'{CET} ')
        self.resultTextField[3].SetLabel(f'{VB} ')
        self.resultTextField[4].SetLabel(f'{CE} ')

        self.resultTextField[5].SetLabel(f'{CEN} ')
        self.resultTextField[5].SetBackgroundColour(self.getCEN_color())

    def getCEN_color(self):
        ''' Retorna a cor em RGB (tuple) do valor Consumo Especifico Normalizado. '''

        consumo = self.consumoEspecificoNormalizado()
        if consumo < 0.4:
            color = (146, 208, 80)
        elif consumo < 0.56:
            color = (255, 255, 81)
        else:
            color = (217, 150, 148)

        return color

    def energiaPonta(self, isIn):
        """ Retorna o consumo de energia na ponta.
        @``isIn`` é True para Operacao dentro da Ponta, False caso contrario. """

        num = 9.81 * self.vazaoBombeada * self.alturaNanometrica # Numerador
        den = (self.rendimentoMotor / 100) * (self.rendimentoBomba / 100) # Denominador

        if isIn:
            result = (num / den) * self.operacaoHorarioPonta * 30
        else:
            result = (num / den) * self.operacaoHorarioForaPonta * 30

        return result

    def consumoTotal(self):
        """ Retorna o consumo de energia total. """

        return self.energiaPonta(True) + self.energiaPonta(False)

    def volumeBombeado(self):
        ''' Retorna o volume bombeado. '''

        return self.vazaoBombeada * (self.operacaoHorarioPonta + self.operacaoHorarioForaPonta) * 30 * 3600

    def consumoEspecifico(self):
        """ Retorna o consumo especifico. """

        return self.consumoTotal() / self.volumeBombeado()

    def consumoEspecificoNormalizado(self):
        """ Retorna o consumo especifico normalizado. """

        return self.consumoEspecifico() * (100 / self.alturaNanometrica)

    def OnConversor(self, event):
        ''' Funcao chamada quando o usuário clica no botao da calculadora. '''

        if not self.conversorWindow:
            self.conversorWindow = conversor.Conversor(self)
            self.conversorWindow.Show()

    def OnDatabase(self, event):
        ''' Abre a janela do banco de dados. '''

        if not self.databaseWindow:
            self.databaseWindow = database.Database(self)
            self.databaseWindow.Show()