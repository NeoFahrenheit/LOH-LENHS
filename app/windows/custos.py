"""
Arquivo contém a classe responsável pela janela Custos de Operação e Indicadores Financeiros.
custos.py
"""

import wx
import os
import app.windows.database as database
import app.windows.tax_window as tax_window
import app.windows.conversor as conversor
import app.global_variables as gv
import app.file_manager as fm
import app.data_processing as dp

GREEN = '#8e9c91'
BLUE = '#9fa3e0'

class Custos(wx.Frame):
    ''' Classe responsável pela janela Custos de Operação e Indicadores Financeiros. '''

    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.WINDOW_NAME = 'Indicadores Financeiros'
        self.menu = wx.MenuBar()
        self.toolbar = self.CreateToolBar()
        self.status_bar = self.CreateStatusBar()

        self.isSaved = True
        self.isThereErrors = False
        self.IsModifyingFields = False
        self.isGreenMode = True

        self.defaultValues = [30, 2.45, 1.2] # Na ordem: ICMS, PIS e CONFINS

        # Irão guardar as referências.
        self.inputAliFields = []
        self.inputGreenFields = []
        self.inputBlueFields = []

        self.SetSize((400, 520))

        self.greenResultWindow = None
        self.blueResultWindow = None
        self.conversorWindow = None
        self.databaseWindow = None

        self.SetTitle(f'{self.WINDOW_NAME}')

        self.setupMenuBar(self.menu)
        self.setupToolsMenu(self.menu)
        self.setupToolbar(self.toolbar)

        self.InitUI()

        if gv.opened_file:
            self.GetDataFromFile()
        else:
            self.OnGreenTax(None)
            self.bottomBlueSizer.ShowItems(False)

        self.Bind(wx.EVT_CLOSE, self.OnCloseApp)
        self.CenterOnParent()

    def setupMenuBar(self, menu):
        """ Inicializa o menu. """

        file_menu = wx.Menu()

        # Criando os itens do menu.
        open_item_menu = file_menu.Append(wx.ID_OPEN, '&Abrir\tCtrl+A', 'Abrir um arquivo')
        save_item_menu = file_menu.Append(wx.ID_SAVE, '&Salvar\tCtrl+S', 'Salvar o arquivo')
        file_menu.AppendSeparator()
        home_item_menu = file_menu.Append(wx.ID_HOME, 'Voltar para Home', 'Voltar para a tela de boas vindas')
        exit_item_menu = file_menu.Append(wx.ID_EXIT, 'Sair', 'Sair do programa')

        # Criando os bindings.
        self.Bind(wx.EVT_MENU, self.OnOpenFile, open_item_menu)
        self.Bind(wx.EVT_MENU, self.OnSaveFile, save_item_menu)
        self.Bind(wx.EVT_MENU, lambda event: self.OnQuit(event, is_exit=False), home_item_menu)
        self.Bind(wx.EVT_MENU, lambda event: self.OnQuit(event, is_exit=True), exit_item_menu)

        menu.Append(file_menu, 'Arquivo')

        self.SetMenuBar(menu)

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

        openTool = toolbar.AddTool(wx.ID_OPEN, 'Abrir', wx.Bitmap('assets/images/open.png'), 'Abrir arquivo')
        saveTool = toolbar.AddTool(wx.ID_SAVE, 'Salvar', wx.Bitmap('assets/images/save.png'), 'Salvar arquivo')
        conversorTool = toolbar.AddTool(wx.ID_ANY, 'Conversor', wx.Bitmap('assets/images/calculator.png'), 'Conversor de unidades')
        databaseTool = toolbar.AddTool(wx.ID_ANY, 'Banco de dados', wx.Bitmap('assets/images/database.png'), 'Banco de dados')
        toolbar.AddSeparator()
        homeTool = toolbar.AddTool(wx.ID_HOME, 'Home', wx.Bitmap('assets/images/home.png'), 'Voltar para Home')

        self.Bind(wx.EVT_TOOL, self.OnOpenFile, openTool)
        self.Bind(wx.EVT_TOOL, self.OnSaveFile, saveTool)
        self.Bind(wx.EVT_TOOL, self.OnConversor, conversorTool)
        self.Bind(wx.EVT_TOOL, self.OnDatabase, databaseTool)
        self.Bind(wx.EVT_TOOL, lambda event: self.OnQuit(event, is_exit=False), homeTool)

        self.toolbar.Realize()

    def InitUI(self):
        ''' Inicializa a UI, usando os sizers. '''

        self.masterSizer = wx.BoxSizer(wx.VERTICAL)
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        self.bottomGreenSizer = wx.BoxSizer(wx.VERTICAL)
        self.bottomBlueSizer = wx.BoxSizer(wx.VERTICAL)

        self.masterSizer.Add(self.topSizer)
        self.masterSizer.Add(self.bottomGreenSizer, flag=wx.TOP, border=25)
        self.masterSizer.Add(self.bottomBlueSizer, flag=wx.TOP, border=25)

        # Configurando o campo de ICMS
        self.icms = self.GetTextInputField('Alíquota ICMS (%) ')
        self.icms[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputAliFields.append(self.icms[1])
        self.topSizer.Add(self.icms[0], flag=wx.ALL, border=2)

        # Configurando o campo de PIS
        self.pis = self.GetTextInputField('Alíquota PIS (%) ')
        self.pis[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputAliFields.append(self.pis[1])
        self.topSizer.Add(self.pis[0], flag=wx.ALL, border=2)

        # Configurando o campo de CONFINS
        self.confins = self.GetTextInputField('Alíquota CONFINS (%) ')
        self.confins[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputAliFields.append(self.confins[1])
        self.topSizer.Add(self.confins[0], flag=wx.ALL, border=2)

        # Colocando o botão de usar o valor padrão das variáveis.
        self.defaultBtn = wx.Button(self, -1, 'Usar valores padrão ')
        self.topSizer.Add(self.defaultBtn, flag=wx.ALL | wx.ALIGN_LEFT, border=10)
        self.defaultBtn.Bind(wx.EVT_BUTTON, self.OnDefault)

        # Colocando os botões de tarifa verde e azul.
        self.greenBtn = wx.Button(self, -1, 'Tarifa Verde', size=(100, 40))
        self.greenBtn.SetBackgroundColour('#d0e8cf')
        self.greenBtn.Bind(wx.EVT_BUTTON, self.OnGreenTax)

        self.blueBtn = wx.Button(self, -1, 'Tarifa Azul', size=(100, 40))
        self.blueBtn.SetBackgroundColour('#c5cee3')
        self.blueBtn.Bind(wx.EVT_BUTTON, self.OnBlueTax)

        # Adicionando os botões de tarifa ao sizers
        btnHBOX = wx.BoxSizer(wx.HORIZONTAL)
        btnHBOX.Add(self.greenBtn, flag=wx.LEFT, border=50)
        btnHBOX.Add(self.blueBtn, flag=wx.LEFT, border=80)
        self.topSizer.Add(btnHBOX, flag=wx.TOP, border=25)

        self.CreateGreenTax()
        self.CreateBlueTax()

        self.SetSizer(self.masterSizer)

    def CreateGreenTax(self):
        ''' Popula o self.bottomGreenSizer com os campos da tarifa verde. '''

        text = wx.StaticText(self, -1, 'Modificando a tarifa verde', style=wx.TE_CENTRE)
        text.SetBackgroundColour(GREEN)
        self.bottomGreenSizer.Add(text, flag=wx.EXPAND)

        self.greenEnergiaPonta = self.GetTextInputField('Energia Ponta (R$/kWh) ')
        self.greenEnergiaPonta[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputGreenFields.append(self.greenEnergiaPonta[1])
        self.bottomGreenSizer.Add(self.greenEnergiaPonta[0], flag=wx.ALL, border=2)

        self.greenEnergiaForaPonta = self.GetTextInputField('Energia Fora Ponta (R$/kWh) ')
        self.greenEnergiaForaPonta[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputGreenFields.append(self.greenEnergiaForaPonta[1])
        self.bottomGreenSizer.Add(self.greenEnergiaForaPonta[0], flag=wx.ALL, border=2)

        self.greenEnergiaDemanda = self.GetTextInputField('Preço Demanda (R$) ')
        self.greenEnergiaDemanda[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputGreenFields.append(self.greenEnergiaDemanda[1])
        self.bottomGreenSizer.Add(self.greenEnergiaDemanda[0], flag=wx.ALL, border=2)

        greenBtn = wx.Button(self,-1, 'Realizar Cálculos')
        greenBtn.Bind(wx.EVT_BUTTON, self.OnGreenCalculate)
        self.bottomGreenSizer.Add(greenBtn, flag=wx.ALL | wx.ALIGN_CENTER, border=20)

    def CreateBlueTax(self):
        ''' Popula o self.bottomBlueSizer com os campos da tarifa azul. '''

        text = wx.StaticText(self, -1, 'Modificando a tarifa azul', style=wx.TE_CENTRE)
        text.SetBackgroundColour(BLUE)
        self.bottomBlueSizer.Add(text, flag=wx.EXPAND)

        self.blueDemandaPonta = self.GetTextInputField('Demanda Ponta (R$/kWh) ')
        self.blueDemandaPonta[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputBlueFields.append(self.blueDemandaPonta[1])
        self.bottomBlueSizer.Add(self.blueDemandaPonta[0], flag=wx.ALL, border=2)

        self.blueDemandaForaPonta = self.GetTextInputField('Demanda Fora Ponta (R$/kWh) ')
        self.blueDemandaForaPonta[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputBlueFields.append(self.blueDemandaForaPonta[1])
        self.bottomBlueSizer.Add(self.blueDemandaForaPonta[0], flag=wx.ALL, border=2)

        self.blueEnergiaPonta = self.GetTextInputField('Energia Ponta (R$/kWh) ')
        self.blueEnergiaPonta[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputBlueFields.append(self.blueEnergiaPonta[1])
        self.bottomBlueSizer.Add(self.blueEnergiaPonta[0], flag=wx.ALL, border=2)

        self.blueEnergiaForaPonta = self.GetTextInputField('Energia Fora Ponta (R$/kWh) ')
        self.blueEnergiaForaPonta[1].Bind(wx.EVT_TEXT, self.OnKeyTyped)
        self.inputBlueFields.append(self.blueEnergiaForaPonta[1])
        self.bottomBlueSizer.Add(self.blueEnergiaForaPonta[0], flag=wx.ALL, border=2)

        blueBtn = wx.Button(self, -1, 'Realizar Cálculos')
        blueBtn.Bind(wx.EVT_BUTTON, self.OnBlueCalculate)
        self.bottomBlueSizer.Add(blueBtn, flag=wx.ALL | wx.ALIGN_CENTER, border = 8)

    def OnGreenTax(self, event):
        ''' Chamada quando o botão "Tarifa Verde" é clicado. '''

        # Verifcamos se a tabela azul atual tem erros antes de trocar para a tarifa verde.
        if self.checkList(self.inputBlueFields, True):
            self.message_dialog('Erros encontrados', 'Por favor, corriga os erros antes de mudar de tarifa.')
            return
        else:
            # O modo já esta selecionado, não precisamos re-criar o BoxSizer. Se o fizermos do mesmo jeito, teremos erros
            # porque iremos acessar objetos que já foram deletados.
            if self.isGreenMode:
                return
            else:
                self.isGreenMode = True

            self.bottomGreenSizer.ShowItems(True)
            self.bottomBlueSizer.ShowItems(False)

        self.Layout()

    def OnBlueTax(self, event):
        ''' Chamada quando o botao "Tarifa Azul' é clicado. '''

        # Verifcamos se a tabela verde atual tem erros antes de trocar para a tarifa azul.
        if self.checkList(self.inputGreenFields, True):
            self.message_dialog('Erros encontrados', 'Por favor, corriga os erros antes de mudar de tarifa.')
            return
        else:
            # O modo já esta selecionado, não precisamos re-criar o BoxSizer. Se o fizermos do mesmo jeito, teremos erros
            # porque iremos acessar objetos que ja foram deletados.
            if not self.isGreenMode:
                return
            else:
                self.isGreenMode = False

            self.bottomGreenSizer.ShowItems(False)
            self.bottomBlueSizer.ShowItems(True)

        self.Layout()

    def OnGreenCalculate(self, event):
        ''' Chamada quando o botão 'Realizar Cálculos' da Tarifa Verde é clicado. '''

        if not event:
            isDataOnly = True
        else:
            isDataOnly = False

        if self.checkList(self.inputAliFields):
            self.message_dialog('Erros encontrados', 'Por favor, corriga os erros do campo de alíquotas antes de calcular.')
            return

        if self.checkList(self.inputGreenFields):
            self.message_dialog('Erros encontrados', 'Por favor, corriga os erros do campo da tarifa verde antes de calcular.')
            return

        if not self.greenResultWindow:
            self.greenResultWindow = tax_window.ResultWindow(self, 'GREEN',
            self.inputAliFields, self.inputGreenFields, self.inputBlueFields, isDataOnly)

            if not isDataOnly:
                self.greenResultWindow.Show()
            else:
                return self.greenResultWindow.greenResult

    def OnBlueCalculate(self, event):
        ''' Chamada quando o botão 'Realizar Cálculos' da Tarifa Azul é clicado. '''

        if not event:
            isDataOnly = True
        else:
            isDataOnly = False

        if self.checkList(self.inputAliFields):
            self.message_dialog('Erros encontrados', 'Por favor, corriga os erros do campo de alíquotas antes de calcular.')
            return

        if self.checkList(self.inputBlueFields):
            self.message_dialog('Erros encontrados', 'Por favor, corriga os erros do campo da tarifa azul antes de calcular.')
            return

        if not self.blueResultWindow:
            self.blueResultWindow = tax_window.ResultWindow(self, 'BLUE',
            self.inputAliFields, self.inputGreenFields, self.inputBlueFields, isDataOnly)

            if not isDataOnly:
                self.blueResultWindow.Show()
            else:
                return self.blueResultWindow.blueResult

    def GetTextInputField(self, inText):
        ''' Retorna uma wx.BoxSizer(wx.HORIZONTAL) e a referência para o textField em uma tupla.\n
        Exemplo: (hBox, textInput) '''

        lPanel = wx.Panel(self, -1)
        rPanel = wx.Panel(self, -1)
        hBox = wx.BoxSizer(wx.HORIZONTAL)

        font = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')

        staticText = wx.StaticText(lPanel, -1, inText, size=(200, 25), style=wx.ALIGN_RIGHT)
        staticText.SetFont(font)

        textInput = wx.TextCtrl(rPanel, -1, size=(200, 25))

        hBox.Add(lPanel)
        hBox.Add(rPanel, flag=wx.EXPAND)

        return (hBox, textInput)

    def OnOpenFile(self, event):
        ''' Chamada quando o usuário clica para abrir um arquivo. '''

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

            if fm.isFileIntegrityOK() and '#parameters_start' in gv.fileStartIndices.keys():
                self.GetDataFromFile()
                gv.file_path = os.path.join(gv.file_dir, gv.filename)
                self.isSaved = True
                self.SetTitle(f'{gv.filename} - {self.WINDOW_NAME}')

            else:
                fm.clearFileVariables()
                message = wx.MessageDialog(self, 'O arquivo carregado não contém as informações necessárias ou foi corrompido.',
                'Erro encontrado', wx.OK | wx.ICON_ERROR)
                message.ShowModal()
                message.Destroy()

                self.OnQuit(event, is_exit=False)

        dialog.Destroy()


    def GetDataFromFile(self):
        ''' Recupera os dados salvos no arquivo.  '''

        # Depois de achar #expenses_start, a próxima linha contém uma string no tipo color.
        # A palavra pode ser APENAS 'green' ou 'blue'.
        # A palavra diz em qual cor estava selecionava quando foi clicado em salvar.
        # Campos de dados de tarifas inexistentes estarão vazios, contendo apenas um '\n'.

        if '#expenses_start' in gv.fileStartIndices.keys():
            index = gv.fileStartIndices['#expenses_start']

            tax = gv.fileLines[index].strip() # Pegamos o id de identificação da escolha da tarifa
            index += 1 # Somamos + 1 para chegar aos dados.

            self.IsModifyingFields = True   # Usamos isso para que a modificação do campo não marque o arquivo como não salvo...

            # Pegando as alíquotas.
            for i in range(0, 3):
                self.inputAliFields[i].SetValue(gv.fileLines[index].strip())
                index += 1

            # Pegando os dados da tarifa verde
            for i in range(0, 3):
                self.inputGreenFields[i].SetValue(gv.fileLines[index].strip())
                index += 1

            # Pegando os dados da tarifa azul
            for i in range(0, 4):
                self.inputBlueFields[i].SetValue(gv.fileLines[index].strip())
                index += 1

            self.IsModifyingFields = False

            if tax == 'blue':
                # O valor de self.isGreenMode está trocado aqui para permitir a execução completa da função self.OnBlueTax.
                self.isGreenMode = True
                self.OnBlueTax(None)
            else:
                # O valor de self.isGreenMode está trocado aqui para permitir a execução completa da função self.OnGreenTax.
                self.isGreenMode = False
                self.OnGreenTax(None)

            self.SetTitle(f'{gv.filename} - {self.WINDOW_NAME}')
            self.isSaved = True

        if gv.opened_file:
            self.SetTitle(f'{gv.filename} - {self.WINDOW_NAME}')
            self.isSaved = True


    def WriteDataToFile(self):
        ''' Salva todos os dados para o arquivo. '''

        if '#expenses_start' in gv.fileStartIndices.keys():
            index = gv.fileStartIndices['#expenses_start']

            if self.isGreenMode:
                gv.fileLines[index] = 'green\n'
            else:
                gv.fileLines[index] = 'blue\n'

            index += 1
            # Agora começaremos com os dados em si.
            # Os dados das alíquotas são obrigatórios, então podemos escrevê-los com calma.
            for field in self.inputAliFields:
                gv.fileLines[index] = f'{field.GetValue()}\n'
                index += 1

            # Iremos agora guardar os dados das tarifas. O usuário é obrigado a preencher os dados de pelo menos uma delas.
            # Agora os dados das tarifas verdes.
            for field in self.inputGreenFields:
                gv.fileLines[index] = f'{field.GetValue()}\n'
                index += 1

            # Agora os dados das tarifas azuis.
            for field in self.inputBlueFields:
                gv.fileLines[index] = f'{field.GetValue()}\n'
                index += 1

        else:
            gv.fileLines.append('#expenses_start\n')
            gv.fileStartIndices['#expenses_start'] = len(gv.fileLines)

            if self.isGreenMode:
                gv.fileLines.append('green\n')
            else:
                gv.fileLines.append('blue\n')

            for field in self.inputAliFields:
                gv.fileLines.append(f'{field.GetValue()}\n')

            for field in self.inputGreenFields:
                gv.fileLines.append(f'{field.GetValue()}\n')

            for field in self.inputBlueFields:
                gv.fileLines.append(f'{field.GetValue()}\n')

            gv.fileLines.append('#expenses_end\n')

        # Fechamos o arquivo e o apagamos totalmente.
        gv.opened_file.close()
        gv.opened_file = open(gv.file_path, 'w')

        # Reescrevemos do zero.
        gv.opened_file.write(''.join(gv.fileLines))
        gv.opened_file.close()

        # Reabrimos em modo de leitura.
        gv.opened_file = open(gv.file_path, 'r')

    def OnSaveFile(self, event):
        ''' Chamada quando o usuário clica para salvar o arquivo. Retorna True em caso de sucesso. '''

        self.checkList(self.inputAliFields)
        if self.isThereErrors:
            self.message_dialog('Erros encontrados.', 'Corriga os errros antes de continuar, por favor.')
            return

        if self.isGreenMode:
            self.checkList(self.inputGreenFields, True)
        else:
            self.checkList(self.inputBlueFields, True)

        if self.isThereErrors:
            self.message_dialog('Erros encontrados.', 'Corriga os errros antes de continuar, por favor.')
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
                self.WriteDataToFile()

                return True

            return False

    def SaveFile(self):
        ''' Salva o arquivo. '''

        if self.isThereErrors:
            return

        if gv.opened_file and not self.isSaved:
            self.WriteDataToFile()
            self.isSaved = True
            self.SetTitle(f'{gv.filename} - {self.WINDOW_NAME}')

    def CloseFile(self):
        ''' Fecha o arquivo. Pode ser chamada mesmo sem um arquivo aberto. '''

        if gv.opened_file:
            self.SetTitle(f'{self.WINDOW_NAME}')
            fm.clearFileVariables()
            self.isSaved = True

        # Se não tiver arquivo aberto, apenas "limpa" os campos.
        else:
            self.SetTitle(f'{self.WINDOW_NAME}')
            self.isSaved = True

        self.IsModifyingFields = True

        self.clearFields(self.inputAliFields)
        self.clearFields(self.inputGreenFields)
        self.clearFields(self.inputBlueFields)

        self.IsModifyingFields = False

    def OnQuit(self, event, is_exit):
        """ Chamada quando o usuário tenta sair, seja para fechar o programa ou voltar pra Home. """

        if not self.isSaved:
            msg = f'Desejar salvar o arquivo "{gv.filename}" antes de sair?'
            message = wx.MessageDialog(self, msg, 'Arquivo não salvo.', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            answer = message.ShowModal()

            if answer == wx.ID_YES:
                self.SaveFile()
            elif answer == wx.ID_CANCEL:
                return

        self.Destroy()
        if is_exit:
            gv.welcome_screen.destroy_()
        else:
            gv.welcome_screen.show_()

    def OnCloseApp(self, event):
        """ Chamada quando o usuário clica no X da janela para sair do programa. """

        if not self.isSaved:
            message = wx.MessageDialog(self, f'Deseja salvar o arquivo {gv.filename} antes de sair?', 'Arquivo não salvo.', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            answer = message.ShowModal()
            if answer == wx.ID_YES:
                self.OnSaveFile(event)
            elif answer == wx.ID_CANCEL:
                return

        self.Destroy()
        gv.welcome_screen.destroy_()

    def OnDefault(self, event):
        ''' Chamada quando o botão "Usar valores padrão" é clicado. '''

        for i in range(0, 3):
            self.inputAliFields[i].SetValue(str(self.defaultValues[i]))

    def checkList(self, inList, ignoreAllBlanks=False):
        ''' Checa a ``inList``, que é do tipo self.inputAliFields, self.inputGreenFields ou self.inputGreenFields, por erros.
        Colore de acordo e atualiza a variável self.isThereErrors. Retorna True se encontrou erros. '''

        # Estamos mudando para False porque se jé estiver True antes, não existe nada no codigo abaixo
        # que o mude para False.
        self.isThereErrors = False

        # Se True, os campos vazios (todos eles) não serão considerados como erros.
        if ignoreAllBlanks:
            isThereSomething = False
            for n in inList:
                value = n.GetValue()
                if value != '':
                    isThereSomething = True
                    break

            if not isThereSomething:
                self.isThereErrors = False
                for n in inList:
                    n.SetOwnBackgroundColour(wx.NullColour)
                    n.Refresh()
                return False

        isOK = True
        for n in inList:
            value = n.GetValue()
            if not (dp.isInt(value) or dp.isFloat(value)):
                isOK = False

            else:
                if float(value) < 0:
                    isOK = False

            if not isOK:
                n.SetOwnBackgroundColour(gv.RED_ERROR)
                self.isThereErrors = True
            else:
                n.SetOwnBackgroundColour(wx.NullColour)

            isOK = True
            n.Refresh()

        if self.isThereErrors:
            return True
        else:
            return False

    def clearFields(self, inList):
        ''' Limpa os campos que pertencem a ``inList``. '''

        if not inList:
            return

        for n in inList:
            n.SetValue('')

    def OnKeyTyped(self, event):
        """ Evento chamado quando usuário aperta alguma tecla em qualquer um dos campos de texto. """

        # A ação de limpar os campos depois de fechar os arquivos, ativa esse evento.
        # Para nos "proteger", temos essa pequena gambiarra.
        if self.IsModifyingFields:
            return

        self.isSaved = False

        if gv.opened_file:
            self.SetTitle(f'* {gv.filename} - {self.WINDOW_NAME}')
        else:
            self.SetTitle(f'(Não Salvo) - {self.WINDOW_NAME}')

        event.Skip()

    def OnConversor(self, event):
        ''' Abre a janela do conversor de unidades. '''

        if not self.conversorWindow:
            self.conversorWindow = conversor.Conversor(self)
            self.conversorWindow.Show()

    def OnDatabase(self, event):
        ''' Abre a janela do banco de dados. '''

        if not self.databaseWindow:
            self.databaseWindow = database.Database(self)
            self.databaseWindow.Show()

    def message_dialog(self, title, message):
        """ Abre um janela com uma informacao. Apenas um botao de OK e fornecido. """

        wx.MessageBox(message, title, wx.OK | wx.ICON_INFORMATION)