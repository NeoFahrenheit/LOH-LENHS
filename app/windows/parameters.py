"""
parameters.py
Janela responsavel pelos parametros do sistema. Ela nao precisa que os consumos de agua estejam preenchidos para ser utilizada.
"""

import wx
import os
import app.windows.database as database
import app.global_variables as gv
import app.file_manager as fm
import app.data_processing as dp
import app.global_variables as gv
import app.windows.conversor as conversor
import app.windows.tooltip_frame as tf
import app.windows.parameters_windows as parameters_windows

VAZAO_BOMBEADA = 'Vazão bombeada (m³/h)'
VAZAO_BOMBEADA_PNG = None

ALTURA_NANOMETRICA = 'Altura Manométrica (m)'
ALTURA_NANOMETRICA_PNG = None

RENDIMENTO_MOTOR = 'Rendimento do Motor (%)'
RENDIMENTO_MOTOR_PNG = None

RENDIMENTO_BOMBA = 'Rendimento da Bomba (%)'
RENDIMENTO_BOMBA_PNG = None

BOMBAS_PARALELO = 'Numero de bombas em paralelo'
BOMBAS_PARALELO_PNG = None

OPERACAO_HORARIO_PONTA = 'Tempo de operação no horário de ponta (h/dia)'
OPERACAO_HORARIO_PONTA_PNG = None

OPERACAO_HORARIO_FORA_PONTA = 'Tempo de operação fora do horário de ponta (h/dia)'
OPERACAO_HORARIO_FORA_PONTA_PNG = None

class ParametersWindow(wx.Frame):
    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.WINDOW_NAME = 'Parâmetros do Sistema'
        self.toolbar = self.CreateToolBar()
        self.menu = wx.MenuBar()
        self.status_bar = self.CreateStatusBar()
        self.isToSave = False

        self.isSaved = True
        self.isThereErrors = False
        self.errorMessages = []
        self.isClearingFields = False

        self.conversorWindow = None
        self.databaseWindow = None
        self.tooltipWindow = None
        self.pumpSizer = wx.BoxSizer(wx.VERTICAL)
        self.systemSizer = wx.BoxSizer(wx.VERTICAL)
        self.operationSizer = wx.BoxSizer(wx.VERTICAL)
        self.pumpRef = None
        self.systemRef = None
        self.curSelected = 1

        self.SetTitle(f'{self.WINDOW_NAME}')

        self.Bind(wx.EVT_CLOSE, self.OnCloseApp)

        self.setupMenuBar(self.menu)
        self.setupToolsMenu(self.menu)
        self.setupToolbar(self.toolbar)
        self.SetMenuBar(self.menu)

        self.setupUI()
        #self.SetSize((727, 640))

        self.LoadFile()
        self.CenterOnScreen()

    def setupMenuBar(self, menu):
        """ Inicializa o menu. """

        file_menu = wx.Menu()

        # Criando os itens do menu.
        new_item_menu = file_menu.Append(wx.ID_NEW, '&Novo\tCtrl+N', 'Criar um arquivo.')
        open_item_menu = file_menu.Append(wx.ID_OPEN, '&Abrir\tCtrl+A', 'Abrir um arquivo')
        save_item_menu = file_menu.Append(wx.ID_SAVE, '&Salvar\tCtrl+S', 'Salvar o arquivo')
        close_item_menu = file_menu.Append(wx.ID_CLOSE, '&Fechar\tCtrl+F', 'Fechar o arquivo')
        home_menu_item = file_menu.Append(wx.ID_HOME, 'Voltar para &Home', 'Voltar para a tela de boas vindas')
        file_menu.AppendSeparator()

        exit_menu_item = file_menu.Append(wx.ID_EXIT, 'Sair', 'Sair do programa')

        # Criando os bindings.
        self.Bind(wx.EVT_MENU, self.OnNewFile, new_item_menu)
        self.Bind(wx.EVT_MENU, self.OnOpenFile, open_item_menu)
        self.Bind(wx.EVT_MENU, self.OnSaveFile, save_item_menu)
        self.Bind(wx.EVT_MENU, self.OnCloseFile, close_item_menu)
        self.Bind(wx.EVT_MENU, lambda event: self.OnQuit(event, is_exit=False), home_menu_item)
        self.Bind(wx.EVT_MENU, lambda event: self.OnQuit(event, is_exit=True), exit_menu_item)

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

        newTool = toolbar.AddTool(wx.ID_NEW, 'Novo', wx.Bitmap('assets/images/new.png'), 'Novo arquivo')
        openTool = toolbar.AddTool(wx.ID_OPEN, 'Abrir', wx.Bitmap('assets/images/open.png'), 'Abrir Arquivo')
        saveTool = toolbar.AddTool(wx.ID_SAVE, 'Salvar', wx.Bitmap('assets/images/save.png'), 'Salvar arquivo')
        conversorTool = toolbar.AddTool(wx.ID_ANY, 'Conversor', wx.Bitmap('assets/images/calculator.png'), 'Abrir o conversor de unidades')
        databaseTool = toolbar.AddTool(wx.ID_ANY, 'Banco de dados', wx.Bitmap('assets/images/database.png'), 'Abrir o banco de dados')
        toolbar.AddSeparator()
        homeTool = toolbar.AddTool(wx.ID_HOME, 'Voltar pra Home', wx.Bitmap('assets/images/home.png'), 'Voltar para Home')

        self.Bind(wx.EVT_TOOL, self.OnNewFile, newTool)
        self.Bind(wx.EVT_TOOL, self.OnOpenFile, openTool)
        self.Bind(wx.EVT_TOOL, self.OnSaveFile, saveTool)
        self.Bind(wx.EVT_TOOL, self.OnConversor, conversorTool)
        self.Bind(wx.EVT_TOOL, self.OnDatabase, databaseTool)
        self.Bind(wx.EVT_TOOL, lambda event: self.OnQuit(event, is_exit=False), homeTool)

        self.toolbar.Realize()

    def setupUI(self):
        """ Constroi a UI. """

        # Os item dentro da lista correspondem, em ordem...
        # [0] --> Vazao Bombeada
        # [1] --> Altura nanometrica
        # [2] --> Rendimento do Motor
        # [3] --> Rendimento da Bomba
        # [4] --> Numero de bombas em paralelo
        # [5] --> Tempo de operacao no horario da ponta
        # [6] --> Tempo de operacao no horario fora da ponta
        self.textBoxesRefs = []

        masterSizer = wx.BoxSizer(wx.VERTICAL)
        hBox = wx.BoxSizer(wx.HORIZONTAL)
        masterSizer.Add(hBox)

        leftSizer = wx.BoxSizer(wx.VERTICAL)
        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        hBox.Add(leftSizer)
        hBox.Add(self.rightSizer)

        # Constrói as caixinhas de texto e as imagens.
        self.vWrapperBox = wx.BoxSizer(wx.VERTICAL)

        for i in range(0, 7):
            text = self.getTextCtrl()
            text.Bind(wx.EVT_TEXT, self.OnKeyTyped)
            self.textBoxesRefs.append(text)

            vBox = self.getVerticalBox()
            vBox.Add(self.getStaticText(self.getLabel(i)))
            vBox.Add(text, flag=wx.EXPAND)
            vBox.SetMinSize(300, 40)

            hBox = self.getHorizontalBox()
            hBox.Add(vBox, flag=wx.ALL, border=5)

            image = wx.Bitmap(self.getImages(i))
            tooltip = wx.ToolTip(gv.tooltipList[i])
            tooltip.SetAutoPop(30_000)
            btn = wx.Button(self, id=1000 + i, size=(40, 40))
            btn.SetToolTip(tooltip)
            btn.SetBitmap(image)
            btn.Bind(wx.EVT_BUTTON, self.OnTooltipButton)

            hBox.Add(btn, flag=wx.ALL, border=5)
            self.vWrapperBox.Add(hBox, flag=wx.ALL, proportion=1, border=4)

        self.createBottomSizer()
        leftSizer.Add(self.vWrapperBox)
        self.createRightWindows()

        self.SetSizerAndFit(masterSizer)

    def createRightWindows(self):
        ''' Cria as janelas que ficam à direita da janela principal. '''

        self.pumpRef = parameters_windows.PumpWindow(self)
        self.systemRef = parameters_windows.SystemWindow(self)
        self.operationRef = parameters_windows.OperationPoint(self)

        self.pumpSizer.Add(self.pumpRef, flag=wx.EXPAND)
        self.systemSizer.Add(self.systemRef)
        self.operationSizer.Add(self.operationRef, flag=wx.EXPAND)

        self.systemSizer.ShowItems(False)
        self.operationSizer.ShowItems(False)

        self.rightSizer.Add(self.pumpSizer)
        self.rightSizer.Add(self.systemSizer)
        self.rightSizer.Add(self.operationSizer)

    def hideAllRightSizers(self):
        ''' Esconde todas as janelas que ficam do lado esquerdo da janela. '''

        self.pumpSizer.ShowItems(False)
        self.systemSizer.ShowItems(False)
        self.operationSizer.ShowItems(False)

    def createBottomSizer(self):
        ''' Cria e inicializa o sizer inferior. '''

        # Constrói o sizer inferior com os botões de simulação.
        vBox = wx.StaticBoxSizer(wx.VERTICAL, self, 'Simulações adicionais')
        hBox = wx.BoxSizer(wx.HORIZONTAL)

        font = wx.Font(9, wx.DEFAULT, wx.DEFAULT, wx.FONTWEIGHT_BOLD)
        smallerFont = wx.Font(8, wx.DEFAULT, wx.DEFAULT, wx.DEFAULT)
        text = wx.StaticText(self, -1, 'Estimar vazão de bombeamento e Altura manométrica')
        text.SetFont(font)
        vBox.Add(text, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=10)

        pumpBtn = wx.Button(self, -1, 'Curva da Bomba', size=(100, 40))
        systemBtn = wx.Button(self, -1, 'Curva do Sistema', size=(100, 40))
        operationBtn = wx.Button(self, -1, 'Ponto de Operação', size=(100, 40))
        operationBtn.SetFont(smallerFont)

        hBox.Add(pumpBtn, flag=wx.LEFT | wx.RIGHT, border=6)
        hBox.Add(systemBtn, flag=wx.LEFT | wx.RIGHT, border=6)
        hBox.Add(operationBtn, flag=wx.LEFT | wx.RIGHT, border=6)

        pumpBtn.Bind(wx.EVT_BUTTON, self.OnPump)
        systemBtn.Bind(wx.EVT_BUTTON, self.OnSystem)
        operationBtn.Bind(wx.EVT_BUTTON, self.OnOperation)

        vBox.Add(hBox, flag=wx.BOTTOM, border=5)
        self.vWrapperBox.Add(vBox, flag=wx.ALL, border=10)

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


    def getVerticalBox(self):
        """ Retorna a referência de uma wx.BoxSizer(wx.VERTICAL). """

        return wx.BoxSizer(wx.VERTICAL)


    def getHorizontalBox(self):
        """ Retorna a referência de uma wx.BoxSizer(wx.HORIZONTAL). """

        return wx.BoxSizer(wx.HORIZONTAL)


    def getStaticText(self, label):
        """ Retorna a referência de uma wx.StaticText(). """

        return wx.StaticText(self, label = label)


    def getTextCtrl(self):
        """ Retorna a referência de um wx.TextCtrl. """

        return wx.TextCtrl(self, size=(100, 20))

    def getBitmap(self, path):
        """ Retorna a referência de um wx.Bitmap(). """

        return wx.Bitmap(path)

    def OnKeyTyped(self, event):
        """ Chamado quando usuário aperta alguma tecla em qualquer um dos campos de texto. """

        # A ação de limpar os campos depois de fechar os arquivos, ativa esse evento.
        # Para nos "proteger", temos essa pequena gambiarra.
        if self.isClearingFields:
            return

        self.isSaved = False

        if gv.opened_file:
            self.SetTitle(f'* {gv.filename} - {self.WINDOW_NAME}')
        else:
            self.SetTitle(f'(Não Salvo) - {self.WINDOW_NAME}')

        event.Skip()

    def updateTitleName(self):
        ''' Atualiza o título da janela. '''

        isAllSaved = [self.isSaved]

        if self.pumpRef:
            isAllSaved.append(self.pumpRef.isSaved)

        if self.systemRef:
            isAllSaved.append(self.systemRef.isSaved)

        isAllSaved = all(isAllSaved)

        if gv.opened_file:
            if isAllSaved:
                msg = f'{gv.filename} - {self.WINDOW_NAME}'
            else:
                msg = f'* {gv.filename} - {self.WINDOW_NAME}'
        else:
            if isAllSaved:
                msg = f'{self.WINDOW_NAME}'
            else:
                msg = f'* {self.WINDOW_NAME}'

        self.SetTitle(msg)

    def OnNewFile(self, event):
        """ Chamada quando o usuário clica para abrir um novo arquivo"""

        if not self.isSaved:
            if gv.opened_file:
                msg = f'Desejar salvar o arquivo "{gv.filename}" antes de criar um novo?'
                message = wx.MessageDialog(self, msg, 'Arquivo não salvo.', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
                answer = message.ShowModal()
                if answer == wx.ID_CANCEL:
                    return

                if answer == wx.ID_YES:
                    self.SaveFile()
                    self.CloseFile()
                else:
                    self.CloseFile()

            else:
                msg = 'Desejar salvar o arquivo antes de criar um novo?'
                message = wx.MessageDialog(self, msg, 'Arquivo não salvo.', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
                answer = message.ShowModal()
                if answer == wx.ID_CANCEL:
                    return

                elif answer == wx.ID_NO:
                    self.CloseFile()

                else:
                    self.OnSaveFile(event)

        else:
            if gv.opened_file:
                self.CloseFile()

    def getLabel(self, index):
        """ Recebe um `index` (0 ~ 6) e retorna a string referente ao indice.
        Retorna None em caso de indice incorreto. """

        if index == 0:
            return VAZAO_BOMBEADA
        elif index == 1:
            return ALTURA_NANOMETRICA
        elif index == 2:
            return RENDIMENTO_MOTOR
        elif index == 3:
            return RENDIMENTO_BOMBA
        elif index == 4:
            return BOMBAS_PARALELO
        elif index == 5:
            return OPERACAO_HORARIO_PONTA
        elif index == 6:
            return OPERACAO_HORARIO_FORA_PONTA
        else:
            return None

    def getImages(self, index):
        """ Recebe um indice (0 ~ 6) e retorna o path do ícone dos parametros do sistema. """

        if index == 0:
            return 'assets/images/parameters/water_tap.png'
        elif index == 1:
            return 'assets/images/parameters/altura.png'
        elif index == 2:
            return 'assets/images/parameters/motor.png'
        elif index == 3:
            return 'assets/images/parameters/bomba.png'
        elif index == 4:
            return 'assets/images/parameters/bombas.png'
        elif index == 5:
            return 'assets/images/parameters/on_time.png'
        elif index == 6:
            return 'assets/images/parameters/off_time.png'
        else:
            return None


    def OnOpenFile(self, event):
        """ Chamada quando o usuário tenta abrir um novo arquivo. """

        if not self.isSaved:
            if gv.opened_file:
                msg = f'Desejar salvar o arquivo "{gv.filename}" antes de abrir um novo?'
            else:
                msg = 'Desejar salvar antes de abrir um novo?'

            message = wx.MessageDialog(self, msg, 'Arquivo não salvo.', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            answer = message.ShowModal()
            if answer == wx.ID_CANCEL:
                return

            if gv.opened_file:
                if answer == wx.ID_YES:
                    self.SaveFile()
                    self.CloseFile()
                else:
                    self.CloseFile()

        dialog = wx.FileDialog(self, f"Escolha um arquivo {gv.file_suffix}", gv.file_dir, '', f'*{gv.file_suffix}*', wx.FD_OPEN)
        # Se a ID do Modal for OK, significa que o usuário escolheu um arquivo.
        if dialog.ShowModal() == wx.ID_OK:
            fm.openAndUpdateFileVariables(dialog)
            self.data = fm.copyWaterFileDataToList()

            if fm.isFileIntegrityOK():
                self.grabParametersDataFromFile()
                gv.file_path = os.path.join(gv.file_dir, gv.filename)
                self.OpenFileFromChilds()
                self.isSaved = True
                self.updateTitleName()

            else:
                fm.clearFileVariables()
                dlg = wx.MessageDialog(self, 'Ocorreu um erro ao abrir o arquivo.\nEle pode ter sido modificado inadvertidamente ou corrompido.',
                'Erro ao abrir o arquivo', wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()

        dialog.Destroy()

    def OpenFileFromChilds(self):
        ''' Abre o arquivo para todas as janelas. '''

        self.pumpRef.LoadFile()
        self.systemRef.LoadFile()

    def checkAllWindows(self):
        ''' Chama as funcões de salvar arquivo de todas as janelas. Retorna False se alguma apresentar erro. '''

        self.errorMessages.clear()
        self.errorMessages = ['Erros encontrados nas seguintes janelas:\n']

        if self.checkErrors():
            self.errorMessages.append('Parâmetros do Sistema\n')

        if not self.pumpRef.checkAndTransferToLists():
            self.errorMessages.append('Curva da Bomba\n')

        if self.systemRef.checkErrors():
            self.errorMessages.append('Curva do Sistema\n')

        if len(self.errorMessages) > 1:
            dlg = wx.MessageDialog(self, ''.join(self.errorMessages), 'Erros encontrados', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return False

        return True

    def OnSaveFile(self, event):
        """ Chamada quando o usuário tenta salvar. Retorna True em caso de sucesso."""

        if not self.checkAllWindows():
            return

        if gv.opened_file:
            self.SaveFile()
            return True

        # Se o usuário estiver criando um arquivo do zero...
        else:
            dialog = wx.FileDialog(self, f"Escolha um nome para o arquivo {gv.file_suffix}", gv.file_dir, '', f'*{gv.file_suffix}*', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            if dialog.ShowModal() == wx.ID_OK:
                fm.saveAndUpdateFileVariables(dialog)

                fm.createEmptyFile()

                self.isSaved = True
                self.SetTitle(f'{gv.filename} - {self.WINDOW_NAME}')

                dialog.Destroy()
                self.writeParametersDataToFile()
                return True

            return False

    def isAllWindowsSaved(self):
        ''' Retorna True se todas as janelas estão salvas. '''

        return all([self.isSaved, self.pumpRef.isSaved, self.systemRef.isSaved])

    def SaveFile(self):
        """ Função responsavel por salvar o arquivo. Supoe que já existe um arquivo aberto. """

        if gv.opened_file and not self.isAllWindowsSaved():
            self.writeParametersDataToFile()
            self.isSaved = True

            self.pumpRef.OnSave()
            self.systemRef.OnSave()
            self.updateTitleName()

    def checkErrors(self):
        """ Verifica se os campos estão corretamente preenchidos. Atualiza a variável self.isSaved.
        Retorna True em caso de erros."""

        self.isThereErrors = False
        isOK = True

        for i in range(0, 7):
            value = self.textBoxesRefs[i].GetValue()
            if not value or not (dp.isInt(value) or dp.isFloat(value)) or float(value) <= 0:
                isOK = False

            # Os valores entre os indices 0 e 3 precisam ser Flaot.
            else:
                if i == 2:
                    n = float(value)
                    if (n <= 0 or n > 100):
                        isOk = False

                elif i == 3:
                    n = float(value)
                    if (n <= 0 or n > 100):
                        isOk = False

                elif i == 4:
                    isOK = dp.isInt(value)

            if not isOK:
                self.textBoxesRefs[i].SetOwnBackgroundColour(gv.RED_ERROR)
                self.isThereErrors = True
            else:
                self.textBoxesRefs[i].SetOwnBackgroundColour(wx.NullColour)

            isOK = True
            self.textBoxesRefs[i].Refresh()

        if self.isThereErrors:
            return True
        else:
            return False

    def writeParametersDataToFile(self):
        """ Salvas as variaveis para o arquivo de texto. """

        count = 0

        # Os os dados de parametros ja existirem, apenas o substituimos. Se nao, colocamos no final usando .append().
        if '#parameters_start' in gv.fileStartIndices.keys():
            start = gv.fileStartIndices['#parameters_start']

            for i in range(start, start + 7):
                gv.fileLines[i] = f'{self.textBoxesRefs[count].GetValue().strip()}\n'
                count += 1

        else:
            gv.fileLines.append('#parameters_start\n')
            gv.fileStartIndices['#parameters_start'] = len(gv.fileLines)

            for i in range(0, 7):
                gv.fileLines.append(f'{self.textBoxesRefs[count].GetValue().strip()}\n')
                count += 1

            gv.fileLines.append('#parameters_end\n')

        # Fechamos o arquivo e o apagamos totalmente.
        gv.opened_file.close()
        gv.opened_file = open(gv.file_path, 'w')

        # Reescrevemos do zero.
        gv.opened_file.write(''.join(gv.fileLines))
        gv.opened_file.close()

        # Reabrimos em modo de leitura.
        gv.opened_file = open(gv.file_path, 'r')


    def grabParametersDataFromFile(self):
        """ Recupera as informações dos paramentros do arquivo. """

        if '#parameters_start' in gv.fileStartIndices.keys():
            start = gv.fileStartIndices['#parameters_start']
            count = 0

            # Se já verificamos a integridade dos arquivos, os dados aqui já são validos.
            for i in range(start, start + 7):
                value = gv.fileLines[i].strip()
                self.textBoxesRefs[count].SetValue(value)
                self.textBoxesRefs[count].SetOwnBackgroundColour(wx.NullColour)
                count += 1

    def LoadFile(self):
        """ Chamada quando a janela de parametros é inicia. Se já tiver um arquivo aberto, preenche os campos
        de texto dos paramentros. """

        if gv.opened_file:
            self.grabParametersDataFromFile()
            self.isSaved = True
            self.updateTitleName()

    def OnCloseFile(self, event):
        """ Chamada quando o usuário tenta fechar o arquivo. """

        if self.isSaved:
            self.CloseFile()
        else:
            if gv.opened_file:
                prompt = f'Desejar salvar o arquivo "{gv.filename}" antes de fechar?'
            else:
                prompt = f'Desejar salvar o arquivo antes de fechar?'

            message = wx.MessageDialog(self, prompt, 'Arquivo não salvo.', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            answer = message.ShowModal()
            if answer == wx.ID_CANCEL:
                return

            if answer == wx.ID_YES:
                self.OnSaveFile(event)
                self.CloseFile()
            else:
                self.CloseFile()

        event.Skip()

    def CloseFile(self):
        """ Limpa a tabela e fecha o arquivo aberto. """

        if gv.opened_file:
            fm.clearFileVariables()

        self.isSaved = True

        self.isClearingFields = True
        for i in range(0, 7):
            self.textBoxesRefs[i].Clear()
        self.isClearingFields = False

        self.pumpRef.onFileBeingClosed()
        self.systemRef.clearFields()

        self.updateTitleName()

    def OnQuit(self, event, is_exit):
        """ Chamada quando o usuário tentar sair do app.
            `@is_exit` diz se o usuário quer sair ou voltar pra tela de boas vindas.
            True para sair, False para voltar para a janela de boas vindas. """

        if not self.isSaved:
            if gv.opened_file:
                msg = f'Desejar salvar o arquivo "{gv.filename}" antes de sair?'
            else:
                msg = 'Desejar salvar antes de sair?'

            message = wx.MessageDialog(self, msg, 'Arquivo não salvo.', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            answer = message.ShowModal()
            if answer == wx.ID_CANCEL:
                return

            if answer == wx.ID_YES:
                if gv.opened_file:
                    self.SaveFile()
                    if is_exit:
                        self.CloseFile()
                else:
                    if self.OnSaveFile(event):
                        if is_exit:
                            self.CloseFile()
                    else:
                        return

        self.Destroy()
        if is_exit:
            gv.welcome_screen.destroy_()
        else:
            gv.welcome_screen.show_()

    def OnConversor(self, event):
        ''' Chamada quando o usuário clica no botão da calculadora. '''

        if not self.conversorWindow:
            self.conversorWindow = conversor.Conversor(self)
            self.conversorWindow.Show()

    def OnDatabase(self, event):
        ''' Abre a janela do banco de dados. '''

        if not self.databaseWindow:
            self.databaseWindow = database.Database(self)
            self.databaseWindow.Show()

    def SaveAllGraphs(self, path):
        ''' Salva todos os gráficos. '''

        self.pumpRef.plotGraph(True, f'{path}\\pump.png')
        self.systemRef.plotGraph(None, True, f'{path}\\system.png')
        self.operationRef.plotGraph(True, f'{path}\\operation.png')

    def OnPump(self, event):
        ''' Chamada quando o usuário clicar no botão ``Curva da Bomba`` na parte inferior da janela. '''

        if self.curSelected != 1:
            self.hideAllRightSizers()
            self.pumpSizer.ShowItems(True)
            self.rightSizer.Layout()

            self.curSelected = 1

    def OnSystem(self, event):
        ''' Chamada quando o usuário clicar no botão ``Curva do Sistema`` na parte inferior da janela. '''

        if self.curSelected != 2:
            self.hideAllRightSizers()
            self.systemSizer.ShowItems(True)
            self.rightSizer.Layout()

            self.curSelected = 2

    def OnOperation(self, event):
        ''' Chamada quando o usuário clicar no botão ``Curva do Sistema`` na parte inferior da janela. '''

        if self.curSelected != 3:
            self.hideAllRightSizers()
            self.operationSizer.ShowItems(True)
            self.rightSizer.Layout()

            self.curSelected = 3

    def OnCloseApp(self, event):
        """ Chamada quando o usuário clica no X vermelho para fechar o programa. """

        self.OnQuit(event, is_exit=True)