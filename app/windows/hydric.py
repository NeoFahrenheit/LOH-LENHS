"""
Arquivo responsável pela janela de Balanço Hídrico de Reservatório
hydric.py
"""

import os
import wx
import wx.lib.scrolledpanel as scrolled
import wx.grid as gridlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import app.global_variables as gv
import app.data_processing as dp
import app.file_manager as fm
import app.windows.conversor as conversor
import app.windows.database as database
import app.windows.water_database as water_database

class HydricBalance(wx.Frame):
    """ Cria a janela de `Balanço Hídrico de Reservatório`. """

    def __init__(self, parent, isToSave=False, path=''):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        super().__init__(parent, style=style)

        self.parent = parent
        self.isToSave = isToSave
        self.path = path
        self.WINDOW_NAME = 'Balanço Hídrico de Reservatório'

        self.menu = wx.MenuBar()
        self.statusBar = self.CreateStatusBar()
        self.toolbar = self.CreateToolBar()

        self.isSaved = True
        # Python não passa booleans por referência...
        self.isUsingWaterData1 = [False]
        self.isUsingWaterData2 = [False]

        self.opt1Fields = []
        self.opt2Fields = []

        self.bombsVazao1 = []
        self.bombsVazao2 = []

        self.opt1Curva = []
        self.opt2Curva = []

        self.data1 = []
        self.data2 = []

        self.conversorWindow = None
        self.waterWindow = None
        self.tableWindow = None

        self.initToolbar()
        self.initFileMenu()
        self.initToolsMenu()

        self.initUI()
        self.CenterOnScreen()

        self.SetTitle(self.WINDOW_NAME)
        self.LoadFile()

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)


    def initToolbar(self):
        ''' Inicializa a self.toolbar. '''

        newTool = self.toolbar.AddTool(wx.ID_NEW, 'Novo', wx.Bitmap('assets/images/new.png'), 'Criar novo arquivo')
        openTool = self.toolbar.AddTool(wx.ID_OPEN, 'Abrir', wx.Bitmap('assets/images/open.png'), 'Abrir arquivo')
        saveTool = self.toolbar.AddTool(wx.ID_SAVE, 'Salvar', wx.Bitmap('assets/images/save.png'), 'Salvar arquivo')
        conversorTool = self.toolbar.AddTool(wx.ID_ANY, 'Conversor', wx.Bitmap('assets/images/calculator.png'), 'Conversor de unidades')
        databaseTool = self.toolbar.AddTool(wx.ID_ANY, 'Banco de dados', wx.Bitmap('assets/images/database.png'), 'Banco de dados')
        self.toolbar.AddSeparator()
        homeTool = self.toolbar.AddTool(wx.ID_HOME, 'Home', wx.Bitmap('assets/images/home.png'), 'Voltar para Home')

        self.Bind(wx.EVT_TOOL, self.OnNewFile, newTool)
        self.Bind(wx.EVT_TOOL, self.OnOpenFile, openTool)
        self.Bind(wx.EVT_TOOL, self.OnSaveFile, saveTool)
        self.Bind(wx.EVT_TOOL, self.OnConversor, conversorTool)
        self.Bind(wx.EVT_TOOL, self.OnDatabase, databaseTool)
        self.Bind(wx.EVT_TOOL, lambda event: self.OnQuit(event, is_exit=False), homeTool)

        self.toolbar.Realize()

    def initFileMenu(self):
        ''' Inicializa o menu arquivo. '''

        file_menu = wx.Menu()

        # Criando os itens do menu.
        new_item_menu = file_menu.Append(wx.ID_NEW, '&Novo\tCtrl+N', 'Criar novo um arquivo')
        open_item_menu = file_menu.Append(wx.ID_OPEN, '&Abrir\tCtrl+A', 'Abrir um arquivo')
        save_item_menu = file_menu.Append(wx.ID_SAVE, '&Salvar\tCtrl+S', 'Salvar o arquivo')
        close_item_menu = file_menu.Append(wx.ID_CLOSE, '&Fechar\tCtrl+F', 'Fechar o arquivo')
        file_menu.AppendSeparator()
        home_item_menu = file_menu.Append(wx.ID_HOME, 'Voltar para Home', 'Voltar para a tela de boas vindas')
        exit_item_menu = file_menu.Append(wx.ID_EXIT, 'Sair', 'Sair do programa')

        # Criando os bindings.
        self.Bind(wx.EVT_MENU, self.OnNewFile, new_item_menu)
        self.Bind(wx.EVT_MENU, self.OnOpenFile, open_item_menu)
        self.Bind(wx.EVT_MENU, self.OnSaveFile, save_item_menu)
        self.Bind(wx.EVT_MENU, self.OnCloseFile, close_item_menu)
        self.Bind(wx.EVT_MENU, lambda event: self.OnQuit(event, is_exit=False), home_item_menu)
        self.Bind(wx.EVT_MENU, lambda event: self.OnQuit(event, is_exit=True), exit_item_menu)

        self.menu.Append(file_menu, 'Arquivo')

        self.SetMenuBar(self.menu)

    def initToolsMenu(self):
        ''' Inicializa o menu `Ferramentas`. '''

        file_menu = wx.Menu()

        conversor_item_menu = file_menu.Append(-1, '&Conversor', 'Abrir o conversor de unidades')
        database_item_menu = file_menu.Append(-1, '&Banco de dados', 'Abrir o banco de dados')

        self.Bind(wx.EVT_MENU, self.OnConversor, conversor_item_menu)
        self.Bind(wx.EVT_MENU, self.OnDatabase, database_item_menu)

        self.menu.Append(file_menu, 'Ferramentas')

        self.SetMenuBar(self.menu)

    def initUI(self):
        ''' Inicializa a UI. '''

        masterSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.leftBox = wx.StaticBoxSizer(wx.VERTICAL, self)
        self.rightBox = wx.StaticBoxSizer(wx.VERTICAL, self)

        masterSizer.Add(self.leftBox, flag=wx.ALL, border=5)
        masterSizer.Add(self.rightBox, flag=wx.ALL, border=5)

        self.leftBox.Add( wx.StaticText(self, -1, 'Opção 1 - Dados de Volume do Reservatório\n') )
        self.rightBox.Add( wx.StaticText(self, -1, 'Opção 2 - Dados de Níveis do Reservatório\n') )

        for i in range(0, 2):
            for j in range(0, 8):
                self.initOptionSizer(i, j)

        self.SetSizerAndFit(masterSizer)

    def initOptionSizer(self, option, index):
        ''' Insere um sizer com um par de text / input no seu sizer apropriado.

        Parâmetros
        ------
        `option`: Se para a opção 1 ou 2.
        `index` : O index da posição que a informação aparece no frame. Para index = 7, cria os sizers dos botões de desenhar gráfico.
        '''

        textSize = (125, 23)
        optNames = [ ['Volume útil (m³)', 'Volume mínimo (m³)', 'Volume máximo (m³)', 'Curva da demanda', 'Dias de simulação', 'Volume inicial (m³)', 'Número de bombas'],
        ['Área da base (m²)', 'Nível mínimo (m)', 'Nível máximo (m)', 'Curva da demanda', 'Dias de simulação', 'Nível inicial (m)', 'Número de bombas'] ]

        if index in [0, 1, 2, 4, 5]:
            hBox = wx.BoxSizer(wx.HORIZONTAL)
            hBox.Add( wx.StaticText(self, -1, optNames[option][index], size=(125, 23)), flag=wx.TOP, border=3 )
            ctrl = wx.TextCtrl(self, -1)
            ctrl.Bind(wx.EVT_TEXT, self.OnKey)
            hBox.Add(ctrl)

            if option == 0:
                self.leftBox.Add(hBox, flag=wx.TOP, border=5)
                self.opt1Fields.append(ctrl)
            else:
                self.rightBox.Add(hBox, flag=wx.TOP, border=5)
                self.opt2Fields.append(ctrl)

        # Curva da demanda
        elif index == 3:
            hBox = wx.BoxSizer(wx.HORIZONTAL)
            hBox.Add( wx.StaticText(self, -1, optNames[option][index], size=textSize), flag=wx.TOP, border=3 )
            curvaBtn = wx.Button(self, 1000 + option, 'Adicionar', size=(110, 23), name='AddCurve')
            curvaBtn.Bind(wx.EVT_BUTTON, self.OnTable)
            hBox.Add(curvaBtn)

            if option == 0:
                self.leftBox.Add(hBox, flag=wx.TOP, border=5)
                self.opt1Fields.append(curvaBtn)
            else:
                self.rightBox.Add(hBox, flag=wx.TOP, border=5)
                self.opt2Fields.append(curvaBtn)

        # Número de bombas
        elif index == 6:
            sizer = wx.BoxSizer(wx.VERTICAL)
            hBox = wx.BoxSizer(wx.HORIZONTAL)
            hBox.Add( wx.StaticText(self, -1, optNames[option][index], size=textSize), flag=wx.TOP, border=3 )
            bombsQtd = wx.TextCtrl(self, 1000 + option)
            bombsQtd.Bind(wx.EVT_TEXT, self.OnBombs)
            bombScrollSizer = wx.BoxSizer(wx.VERTICAL)
            bombScroll = scrolled.ScrolledPanel(self, -1, size=(235, 100), style=wx.SUNKEN_BORDER)
            bombScroll.SetSizer(bombScrollSizer)
            bombScroll.SetupScrolling()
            hBox.Add(bombsQtd)
            sizer.Add(hBox)
            sizer.Add(bombScroll, flag=wx.TOP, border=5)

            if option == 0:
                self.leftBox.Add(sizer, flag=wx.TOP, border=5)
                self.opt1Fields.append( [bombsQtd, (bombScroll, bombScrollSizer)] )
            else:
                self.rightBox.Add(sizer, flag=wx.TOP, border=5)
                self.opt2Fields.append( [bombsQtd, (bombScroll, bombScrollSizer)] )

        # Botões de desenhar gráfico
        elif index == 7:
            sizer = wx.BoxSizer(wx.VERTICAL)
            volumeBtn = wx.Button(self, option + 1000, 'Desenhar Gráfico', size=(162, 23))
            volumeBtn.Bind(wx.EVT_BUTTON, self.OnVolume)

            sizer.Add(volumeBtn, flag=wx.ALIGN_CENTER)

            if option == 0:
                self.leftBox.Add(sizer, flag=wx.ALL | wx.EXPAND, border=10)
            else:
                self.rightBox.Add(sizer, flag=wx.ALL | wx.EXPAND, border=10)

    def updateScrolledPanel(self, ID, number):
        ''' Atualiza o scrolledPanel correspondente ao ID com a `number` quantidade(s) de TextCtrl
        para as informações de vazão da bomba. '''

        if number > 9 or number < 1:
            self.clearScrolledPanel(ID)
            return

        self.clearScrolledPanel(ID)

        if ID == 0:
            bombScroll = self.opt1Fields[6][1][0]
            bombSizer = self.opt1Fields[6][1][1]
            bombsCtrlList = self.bombsVazao1
        else:
            bombScroll = self.opt2Fields[6][1][0]
            bombSizer = self.opt2Fields[6][1][1]
            bombsCtrlList = self.bombsVazao2

        for i in range(0, number):
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add( wx.StaticText(bombScroll, -1, f'Vazão Bomba {i + 1} (m³/s) :', size=(125, 23)), flag=wx.TOP, border=3 )
            textCtrl = wx.TextCtrl(bombScroll, -1, size=(75, 23))
            textCtrl.Bind(wx.EVT_TEXT, self.OnKey)
            bombsCtrlList.append(textCtrl)
            sizer.Add(textCtrl)

            bombSizer.Add(sizer, flag=wx.ALL, border=5)

        bombScroll.SetupScrolling()

    def clearScrolledPanel(self, ID):
        ''' Deleta todos os componentes do sizer corresponde ao ID e sua lista. '''

        if ID == 0:
            bombSizer = self.opt1Fields[6][1][1]
            bombSizer.Clear(True)
            bombSizer.Layout()
            self.bombsVazao1.clear()

        else:
            bombSizer = self.opt2Fields[6][1][1]
            bombSizer.Clear(True)
            bombSizer.Layout()
            self.bombsVazao2.clear()

        self.SendSizeEvent()    # Faz o scrolledPanel resetar ao tamanho original com 0 sizers.

    def getVazaoValues(self, option):
        ''' Retorna, em uma lista de strings, os valores da vazão digitado pelo usuário. `option` deve ser 0 ou 1. '''

        out = []

        if option == 0:
            for text in self.bombsVazao1:
                out.append(text.GetValue())
        else:
            for text in self.bombsVazao2:
                out.append(text.GetValue())

        return out

    def checkErrors(self, option):
        ''' Checa por erros no formulário. Retorna True caso encontre erros. Formulários totalmente vazio não serão considerados como erros.'''

        isThereErrors = False

        if option == 0:
            curList = self.opt1Fields
            vazaoList = self.bombsVazao1
            demandaList = self.opt1Curva
            waterData = self.isUsingWaterData1
        else:
            curList = self.opt2Fields
            vazaoList = self.bombsVazao2
            demandaList = self.opt2Curva
            waterData = self.isUsingWaterData2

        # Se o formulário estiver totalmente vazio, vamos considerar que não existe erros.
        if self.isFormEmpty(option):
            return False

        for i in range(0, 7):
            # Volume útil
            if i == 0:
                value = curList[i].GetValue()
                if not (dp.isFloat(value) and float(value) >= 1):
                    isThereErrors = True
                    dp.colorField(curList[i], True)
                else:
                    dp.colorField(curList[i], False)

            # Volume mínimo
            elif i == 1:
                # Este valor pode ser 0.
                isVolMinimoOK = False
                value = curList[i].GetValue()
                if not (dp.isFloat(value) and float(value) >= 0):
                    isThereErrors = True
                    dp.colorField(curList[i], True)
                else:
                    dp.colorField(curList[i], False)
                    isVolMinimoOK = True

            # Volume maximo.
            elif i == 2:
                # Volume maximo não pode ser menor ou igual ao volume mínimo.
                value = curList[i].GetValue()
                isFloatOK = dp.isFloat(value) and float(value) > 0
                if not isFloatOK:
                    isThereErrors = True
                    dp.colorField(curList[i], True)

                # Se o volume minimo existe e for válido, precisamos ver se ele é o maior.
                elif isVolMinimoOK:
                    if not float(value) > float(curList[i - 1].GetValue()):
                        isThereErrors = True
                        dp.colorField(curList[i], True)
                    else:
                        dp.colorField(curList[i], False)

                else:
                    dp.colorField(curList[i], False)

            # Checa pelo valor do botão 'Adicionar'.
            elif i == 3:
                if not demandaList and not waterData[0]:
                    isThereErrors = True
                    dp.colorField(curList[i], True)
                else:
                    dp.colorField(curList[i], False)

            # Dias de simulação
            elif i == 4:
                value = curList[i].GetValue()
                if not (dp.isInt(value) and int(value) > 0):
                    isThereErrors = True
                    dp.colorField(curList[i], True)
                else:
                    dp.colorField(curList[i], False)

            # Volume inicial
            elif i == 5:
                # Este valor pode ser 0.
                value = curList[i].GetValue()
                if not (dp.isFloat(value) and float(value) >= 0):
                    isThereErrors = True
                    dp.colorField(curList[i], True)
                else:
                    dp.colorField(curList[i], False)

            # Número de bombas
            elif i == 6:
                value = curList[i][0].GetValue()
                if not (dp.isInt(value) and int(value) > 0):
                    isThereErrors = True
                    dp.colorField(curList[i][0], True)
                else:
                    dp.colorField(curList[i][0], False)

        # Checa pelos valores de vazão da bomba.
        for field in vazaoList:
            value = field.GetValue()
            if not (dp.isFloat(value) and float(value) > 0):
                isThereErrors = True
                dp.colorField(field, True)
            else:
                dp.colorField(field, False)

        return isThereErrors

    def updateTitleName(self):
        ''' Atualiza o título da janela. '''

        if gv.opened_file:
            if self.isSaved:
                msg = f'{gv.filename} - {self.WINDOW_NAME}'
            else:
                msg = f'* {gv.filename} - {self.WINDOW_NAME}'
        else:
            if self.isSaved:
                msg = f'{self.WINDOW_NAME}'
            else:
                msg = f'* {self.WINDOW_NAME}'

        self.SetTitle(msg)

    def isFormEmpty(self, option):
        ''' Checa se o formulário `option` está totalmente em branco. Retorna True em caso afirmativo. Descolore todos os campos em branco. '''

        if option == 0:
            curList = self.opt1Fields
            curvaList = self.opt1Curva
        else:
            curList = self.opt2Fields
            curvaList = self.opt2Curva

        isAllEmpty = True
        for i in range(0, 7):
            if i in [0, 1, 2, 4, 5]:
                value = curList[i].GetValue()
                if not dp.isFieldEmpty(value):
                    isAllEmpty = False
                else:
                    dp.colorField(curList[i], False)

            elif i == 6:
                value = curList[i][0].GetValue()
                if not dp.isFieldEmpty(value):
                    isAllEmpty = False
                else:
                    dp.colorField(curList[i][0], False)

        if curvaList:
            isAllEmpty = False
        else:
            dp.colorField(curList[3], False)

        return isAllEmpty

    def clearForms(self):
        ''' Limpa os campos de todos os formulários, como também todos os dados das listas. '''

        opt = [self.opt1Fields, self.opt2Fields]

        self.bombsVazao1.clear()
        self.bombsVazao2.clear()
        self.opt1Curva.clear()
        self.opt2Curva.clear()
        self.data1.clear()
        self.data2.clear()
        self.isUsingWaterData1 = [False]
        self.isUsingWaterData2 = [False]

        for i in range(0, 2):
            for j in range(0, 7):
                if j in [0, 1, 2, 4, 5]:
                    opt[i][j].Clear()
                    dp.colorField(opt[i][j], False)

                elif j == 3:
                    opt[i][j].SetLabel('Adicionar')
                    dp.colorField(opt[i][j], False)

                elif j == 6:
                    opt[i][j][0].Clear()
                    dp.colorField(opt[i][j][0], False)

    def LoadFile(self):
        ''' Carrega o arquivo especificado em `gv.file_path`. '''

        if gv.opened_file and fm.isFileIntegrityOK():
            self.grabDataFromFile()
            self.isSaved = True
            self.updateTitleName()

    def grabDataFromFile(self):
        ''' Carrega as informações do arquivo aberto. '''

        if not '#hydric_start' in gv.fileStartIndices.keys():
            return

        opts = [self.opt1Fields, self.opt2Fields]
        curvas = [self.opt1Curva, self.opt2Curva]
        vazoes = [self.bombsVazao1, self.bombsVazao2]
        waterData = [self.isUsingWaterData1, self.isUsingWaterData2]

        index = gv.fileStartIndices['#hydric_start']

        for i in range(0, 2):
            if gv.fileLines[index] != '\n':

                for j in range(0, 7):
                    if j in [0, 1, 2, 4, 5]:
                        opts[i][j].SetValue(gv.fileLines[index].strip())
                        index += 1

                    # Curva da demanda
                    elif j == 3:
                        words = gv.fileLines[index].strip().split()
                        if words[0] == '-1':
                            temp = fm.copyWaterFileDataToList()
                            temp = dp.getTableReadyData(temp)
                            curvas[i].clear()
                            curvas[i].extend(temp)
                            opts[i][j].SetLabel('Salvo: Cons. Água')

                            waterData[i][0] = True
                        else:
                            for word in words:
                                curvas[i].append(float(word))

                            opts[i][j].SetLabel('Salvo')

                        index += 1

                    # Número de bombas
                    elif j == 6:
                        words = gv.fileLines[index].strip().split()
                        number = words[0]
                        vazoesFile = words[1:]

                        opts[i][j][0].SetValue(number)
                        for x in range(0, len(vazoesFile)):
                            vazoes[i][x].SetValue(vazoesFile[x])

                        index += 1

            # Se a próxima linha for '\n', não há dados daquele formulário ali.
            else:
                index += 7


    def writeDataToFile(self):
        ''' Salva as informações no arquivo. '''

        if not '#hydric_start' in gv.fileStartIndices.keys():
            gv.fileStartIndices['#hydric_start'] = len(gv.fileLines) + 1
            gv.fileLines.append('#hydric_start\n')

            for _ in range(0, 14):   # Espaço para os dois formulários.
                gv.fileLines.append('\n')

            gv.fileLines.append('#hydric_end\n')
            gv.fileStartIndices['#hydric_end'] = len(gv.fileLines) - 1

        self.flushData()

        # Fechamos o arquivo e o apagamos totalmente.
        gv.opened_file.close()
        gv.opened_file = open(gv.file_path, 'w')

        # Reescrevemos do zero.
        gv.opened_file.write(''.join(gv.fileLines))
        gv.opened_file.close()

        # Reabrimos em modo de leitura.
        gv.opened_file = open(gv.file_path, 'r')

    def flushData(self):
        ''' Escreve os dados dos formulários para `gv.fileLines`. '''

        opts = [self.opt1Fields, self.opt2Fields]
        curvas = [self.opt1Curva, self.opt2Curva]
        vazoes = [self.bombsVazao1, self.bombsVazao2]
        waterData = [self.isUsingWaterData1, self.isUsingWaterData2]

        start = gv.fileStartIndices['#hydric_start']

        for i in range(0, 2):
            if self.isFormEmpty(i):
                for j in range(0, 7):
                    gv.fileLines[start + j] = '\n'

                start += 7
                continue

            for j in range(0, 7):
                if j in [0, 1, 2, 4, 5]:
                    gv.fileLines[start + j] = f"{opts[i][j].GetValue().strip()}\n"

                elif j == 3:
                    if waterData[i]:
                        gv.fileLines[start + j] = '-1\n'
                    else:
                        out = ''
                        for value in curvas[i]:
                            out += f"{str(value)} "
                        out += '\n'

                        gv.fileLines[start + j] = out

                elif j == 6:
                    out = opts[i][j][0].GetValue().strip()
                    for field in vazoes[i]:
                        out += f" {field.GetValue().strip()}"
                    out += '\n'

                    gv.fileLines[start + j] = out

            start += 7

    def SaveFile(self):
        ''' Salva o arquivo aberto. '''

        if gv.opened_file and not self.isSaved:
            self.writeDataToFile()
            self.isSaved = True
            self.updateTitleName()

    def CloseFile(self):
        ''' Fecha o arquivo. '''

        if gv.opened_file:
            self.clearForms()
            fm.clearFileVariables()
            self.isSaved = True
            self.updateTitleName()

    def getOpt1Fields(self):
        ''' Returna uma lista de tuplas com os dados do primeiro formulário. '''

        soma_vazao = 0
        for value in self.getVazaoValues(0):
            soma_vazao += float(value)

        return [
            ('Volume útil', 'm³', self.opt1Fields[0].GetValue()),
            ('Volume mínimo', 'm³', self.opt1Fields[1].GetValue()),
            ('Volume máximo', 'm³', self.opt1Fields[2].GetValue()),
            ('Dias de simulação', '', self.opt1Fields[4].GetValue()),
            ('Volume inicial', 'm³', self.opt1Fields[5].GetValue()),
            ('Soma da vazão das bombas', 'm³/s', str(soma_vazao)),
        ]

    def getOpt2Fields(self):
        ''' Returna uma lista de tuplas com os dados do primeiro formulário. '''

        soma_vazao = 0
        for value in self.getVazaoValues(1):
            soma_vazao += float(value)

        return [
            ('Área da base', 'm²', self.opt2Fields[0].GetValue()),
            ('Nível mínimo', 'm', self.opt2Fields[1].GetValue()),
            ('Nível máximo', 'm', self.opt2Fields[2].GetValue()),
            ('Dias de simulação', '', self.opt2Fields[4].GetValue()),
            ('Nível inicial', 'm', self.opt2Fields[5].GetValue()),
            ('Soma da vazão das bombas', 'm³/s', str(soma_vazao)),
        ]

    def gatherData(self, ID):
        ''' Prepara os dados para exibição. '''

        # [0] Volume útil (m³)
        # [1] Volume mínimo (m³)
        # [2] Volume máximo (m³)
        # [3] Curva da demanda
        # [4] Dias de simulação
        # [5] Volume inicial (m³)
        # [6] Número de bombas

        vazoes = [self.bombsVazao1, self.bombsVazao2]
        waterData = [self.isUsingWaterData1, self.isUsingWaterData2]

        area = None
        if ID == 0:
            volMinimo = float(self.opt1Fields[1].GetValue())
            volMaximo = float(self.opt1Fields[2].GetValue())
            diasSim = int(self.opt1Fields[4].GetValue())
            volInicial = float(self.opt1Fields[5].GetValue())
        else:
            # Deveríamos mudar os nomes das variáveis para areaMinima, areaInicial, etc.
            # Vamos deixar assim pra reduzir a necessidade de criar mais linhas de código.
            area = float(self.opt2Fields[0].GetValue())
            volMinimo = float(self.opt2Fields[1].GetValue()) / area
            volMaximo = float(self.opt2Fields[2].GetValue()) / area
            diasSim = int(self.opt2Fields[4].GetValue())
            volInicial = float(self.opt2Fields[5].GetValue()) / area

        vazoesSum = 0
        for field in vazoes[ID]:
            vazoesSum += float(field.GetValue())

        if waterData[ID][0]:
            minsBelowZero = self.calculateFromWaterData(ID, volInicial, volMaximo, volMinimo, vazoesSum, diasSim, area)
        else:
            minsBelowZero = self.calculateData(ID, volInicial, volMaximo, volMinimo, vazoesSum, diasSim, area)

        self.plotGraphVolume(ID, volMaximo, minsBelowZero)

    def OnVolume(self, event):
        ''' Chamada quando o usuário clica no botão para desenhar o gráfico de volume instantâneo. '''

        ID = event.GetEventObject().Id
        ID -= 1000

        if self.isFormEmpty(ID):
            dlg = wx.MessageDialog(self, 'Por favor, preencha os campos antes de continuar.', 'Formulário vazio', wx.ICON_ERROR)
            dlg.ShowModal()
            return

        if self.checkErrors(ID):
            dlg = wx.MessageDialog(self, 'Por favor, corrige os erros antes de continuar.', 'Erros encontrados', wx.ICON_ERROR)
            dlg.ShowModal()
            return

        self.gatherData(ID)

    def calculateFromWaterData(self, ID, volInicial, volMaximo, volMinimo, vazoesSum, diasSim, area=None):
        ''' Preenche a lista de dicionários pronta para o plot do gráfico a partir dos dados de consumo de água. (self.data1).
        Ex: [{'time': datetime.datetime(2021, 7, 19, 0, 0), 'volume': 1809.7759602911945, 'liga': 1}] '''

        data = self.opt1Curva
        self.data1.clear()
        days = len(data)
        isRepeating = False
        date = ''
        minutos = []
        i = 0

        while diasSim != 0:
            x = data[i]['xyValues'][0]
            y = data[i]['xyValues'][1]
            interval = int(dp.getTimesDifference(x[0], x[1]) * 60)

            if not isRepeating:
                date = data[i]['date']
                now = datetime.strptime(f"{date} 00:00", '%d/%m/%Y %H:%M')

            for j in range(0, len(y)):
                valueDiv = y[j] / interval

                for _ in range(0, interval):
                    dic = {}
                    dic['time'] = now
                    minutos.append(valueDiv)
                    self.data1.append(dic)

                    now += timedelta(minutes=1)

            i += 1
            diasSim -= 1

            # Se o usuário colocar mais dias de simulação que existe nos dados, o bool abaixo
            # e a última adição ao now, usando o timedelta, fez pular para o dia seguinte.
            # Agora, com isRepeating = True, não vamos ficar repetindo datas.
            if i == days:
                i = 0
                isRepeating = True

        ### Segunda parte ###

        LIGA = []
        VAI = []
        wereBelowZero = False
        minutesBelowZero = 0

        # Calcula a evolução do reservatório e da bomba
        for i in range(0, len(minutos)):
            if i == 0:
                if (volInicial - minutos[i]) >= volMinimo and (volInicial - minutos[i]) <= volMaximo:
                    Qbomba_total = vazoesSum * 0
                    LIGA.append(0)
                    if ID == 0:
                        VAI.append(Qbomba_total - minutos[i] + volInicial)
                    else:
                        VAI.append( (Qbomba_total - minutos[i] + volInicial) / area )

                if (volInicial - minutos[i]) < volMinimo:
                    Qbomba_total = vazoesSum * 60
                    LIGA.append(1)
                    if ID == 0:
                        VAI.append(Qbomba_total - minutos[i] + volInicial)
                    else:
                        VAI.append( (Qbomba_total - minutos[i] + volInicial) / area )

            else:
                if ((VAI[i - 1] - minutos[i] < volMinimo) and (LIGA[i - 1] == 0)) or ((LIGA[i - 1] == 1) and (VAI[i - 1] - minutos[i] < volMaximo)):
                    Qbomba_total = vazoesSum * 60
                    LIGA.append(1)
                    if ID == 0:
                        VAI.append(Qbomba_total - minutos[i] + VAI[i - 1])
                    else:
                        VAI.append( (Qbomba_total - minutos[i] + VAI[i - 1]) / area)

                if ((VAI[i - 1] - minutos[i] > volMinimo) and (LIGA[i - 1] == 0)) or (LIGA[i - 1] == 1 and (VAI[i - 1] - minutos[i] > volMaximo)):
                    Qbomba_total = vazoesSum * 0
                    LIGA.append(0)
                    if ID == 0:
                        VAI.append(Qbomba_total - minutos[i] + VAI[i - 1])
                    else:
                        VAI.append( (Qbomba_total - minutos[i] + VAI[i - 1]) / area)

                if VAI[i] < 0:
                    VAI[i] = 0
                    minutesBelowZero += 1
                    wereBelowZero = True

        if wereBelowZero and not self.isToSave:
            dlg = wx.MessageDialog(self, f'A vazão bombeada não conseguiu atender a demanda do consumo de água por {(minutesBelowZero / 60):.1f} horas.',
            'Vazão insuficiente', wx.ICON_INFORMATION)
            dlg.ShowModal()

        # Formata os dados para a plot dos gráficos.
        for i in range(0, len(minutos)):
            self.data1[i]['volume'] = VAI[i]
            value = LIGA[i]
            if value == 0:
                self.data1[i]['liga'] = volMinimo
            else:
                self.data1[i]['liga'] = volMaximo

        return minutesBelowZero

    def calculateData(self, ID, volInicial, volMaximo, volMinimo, vazoesSum, diasSim, area):
        ''' Preenche a lista de dicionários pronta para o plot do gráfico (self.data1).
        Ex: [{'time': datetime.datetime(1900, 1, 1, 0, 0), 'volume': 1809.7759602911945, 'liga': 1}] '''

        minutos = []
        LIGA = []
        VAI = []

        for value in self.opt1Curva:
            valueDiv = value / 60
            for _ in range(0, 60):
                minutos.append(valueDiv)

        minutos *= diasSim

        wereBelowZero = False
        minutesBelowZero = 0

        # Calcula a evolução do reservatório e da bomba
        for i in range(0, len(minutos)):
            if i == 0:
                if (volInicial - minutos[i]) >= volMinimo and (volInicial - minutos[i]) <= volMaximo:
                    Qbomba_total = vazoesSum * 0
                    LIGA.append(0)
                    if ID == 0:
                        VAI.append(Qbomba_total - minutos[i] + volInicial)
                    else:
                        VAI.append( (Qbomba_total - minutos[i] + volInicial) / area )

                if (volInicial - minutos[i]) < volMinimo:
                    Qbomba_total = vazoesSum * 60
                    LIGA.append(1)
                    if ID == 0:
                        VAI.append(Qbomba_total - minutos[i] + volInicial)
                    else:
                        VAI.append( (Qbomba_total - minutos[i] + volInicial) / area )

            else:
                if ((VAI[i - 1] - minutos[i] < volMinimo) and (LIGA[i - 1] == 0)) or ((LIGA[i - 1] == 1) and (VAI[i - 1] - minutos[i] < volMaximo)):
                    Qbomba_total = vazoesSum * 60
                    LIGA.append(1)
                    if ID == 0:
                        VAI.append(Qbomba_total - minutos[i] + VAI[i - 1])
                    else:
                        VAI.append( (Qbomba_total - minutos[i] + VAI[i - 1]) / area)

                if ((VAI[i - 1] - minutos[i] > volMinimo) and (LIGA[i - 1] == 0)) or (LIGA[i - 1] == 1 and (VAI[i - 1] - minutos[i] > volMaximo)):
                    Qbomba_total = vazoesSum * 0
                    LIGA.append(0)
                    if ID == 0:
                        VAI.append(Qbomba_total - minutos[i] + VAI[i - 1])
                    else:
                        VAI.append( (Qbomba_total - minutos[i] + VAI[i - 1]) / area)

                if VAI[i] < 0:
                    VAI[i] = 0
                    minutesBelowZero += 1
                    wereBelowZero = True

        if wereBelowZero and not self.isToSave:
            dlg = wx.MessageDialog(self, f'A vazão bombeada não conseguiu atender a demanda do consumo de água por {(minutesBelowZero / 60):.1f} horas.',
            'Vazão insuficiente', wx.ICON_INFORMATION)
            dlg.ShowModal()

        # Formata os dados para a plot dos gráficos.
        now = datetime.strptime("1 00:00", '%d %H:%M')
        self.data1.clear()
        for i in range(0, len(minutos)):
            dic = {}

            dic['time'] = now
            dic['volume'] = VAI[i]
            value = LIGA[i]
            if value == 0:
                dic['liga'] = volMinimo
            else:
                dic['liga'] = volMaximo

            self.data1.append(dic)
            now += timedelta(minutes=1)

        return minutesBelowZero

    def plotGraphVolume(self, ID, volMaximo, minsBelowZero):
        ''' Plota o gráfico da análise de volume. '''

        x = []
        y = []
        yBomb = []
        for dic in self.data1:
            x.append(dic['time'])
            y.append(dic['volume'])
            yBomb.append(dic['liga'])

        fig, ax = plt.subplots(figsize=(11, 6))
        ax.xaxis.set_tick_params(rotation=30, labelsize=10)

        # Informacoes do gráfico.
        if minsBelowZero > 0:
            plt.title(f'Quantidade de horas com reservatório vazio: {(minsBelowZero / 60):.1f}', loc='left', fontsize=10)

        plt.suptitle('Análise do volume do reservatório', x=0.07, y=0.98, ha='left', fontsize=15)
        ax.set_xlabel('Dia')

        if ID == 0:
            yLabel = 'Volume (m³)'
        else:
            yLabel = 'Nível (m)'
        ax.set_ylabel(yLabel)

        # estiliza o grid
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='gray', linestyle='dashed', alpha=0.2)
        ax.xaxis.grid(color='gray', linestyle='dashed', alpha=0.2)

        # remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        fmt = mdates.DateFormatter('%d/%m')
        ax.xaxis.set_major_formatter(fmt)  # Aplica a formatacao.
        fig.autofmt_xdate()  # Aplica a 'organizacao'.

        plt.plot(x, y, label='Nível')
        ax.axhline(y=volMaximo, color='grey', alpha=0.4, label='Volume Máximo')
        ax.plot(x, yBomb, '--', color='red', alpha=0.4, label='Funcionamento da bomba')
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=3)
        plt.tight_layout()

        if self.isToSave:
            plt.savefig(f'{self.path}\\opt{ID}.png', bbox_inches='tight')
        else:
            plt.show()

    def OnBombs(self, event):
        ''' Chamada quando é digitado qualquer coisa nos campos de número de bombas. '''

        ID = event.GetEventObject().Id
        ID -= 1000

        if ID == 0:
            value = self.opt1Fields[6][0].GetValue()
        else:
            value = self.opt2Fields[6][0].GetValue()

        try:
            number = int(value)
            self.updateScrolledPanel(ID, number)
        except:
            self.clearScrolledPanel(ID)

    def OnNewFile(self, event):
        ''' Chamada quando o usuário clica em `Novo Arquivo`. '''

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

    def OnOpenFile(self, event):
        ''' Chamada quando o usuário clica em `Abrir Arquivo`. '''

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

            if fm.isFileIntegrityOK():
                self.clearForms()
                self.grabDataFromFile()
                gv.file_path = os.path.join(gv.file_dir, gv.filename)
                self.isSaved = True
                self.updateTitleName()

            else:
                fm.clearFileVariables()
                dlg = wx.MessageDialog(self, 'Ocorreu um erro ao abrir o arquivo.\nEle pode ter sido modificado inadvertidamente ou corrompido.',
                'Erro ao abrir o arquivo', wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()

        dialog.Destroy()

    def OnSaveFile(self, event):
        ''' Chamada quando o usuário clica em `Salvar Arquivo`. '''

        if self.checkErrors(0) or self.checkErrors(1):
            dlg = wx.MessageDialog(self, 'Por favor, corrige os erros antes de continuar.', 'Erros encontrados', wx.ICON_ERROR)
            dlg.ShowModal()
            return False

        if gv.opened_file:
            self.SaveFile()
            return True

        # Se o usuário estiver criando um arquivo do zero...
        else:
            dialog = wx.FileDialog(self, f"Escolha um nome para o arquivo {gv.file_suffix}", gv.file_dir, '', f'*{gv.file_suffix}*', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            if dialog.ShowModal() == wx.ID_OK:
                fm.saveAndUpdateFileVariables(dialog)

                # Cria o arquivo, apenas.
                fm.createEmptyFile()

                self.writeDataToFile()
                self.isSaved = True
                self.updateTitleName()

                dialog.Destroy()
                return True

            return False

    def OnCloseFile(self, event):
        ''' Chamada quando o usuário clica em `Fechar Arquivo`. '''

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

    def OnKey(self, event):
        ''' Chamada quando qualquer tecla é apertada dentro de qualquer TextCtrl. '''

        if self.isSaved:
            self.isSaved = False
            self.updateTitleName()

    def OnConversor(self, event):
        ''' Abre a janela do conversor de unidades. '''

        if not self.conversorWindow:
            self.conversorWindow = conversor.Conversor(self)
            self.conversorWindow.Show()

    def OnDatabase(self, event):
        ''' Abre a janela do banco de dados. '''

        if not self.waterWindow:
            self.waterWindow = database.Database(self)
            self.waterWindow.Show()

    def OnTable(self, event):
        ''' Chamada quando qualquer dos botoes de "Adicionar" for clicado. '''

        ID = event.GetEventObject().Id
        ID -= 1000

        if not self.tableWindow:
            self.tableWindow = HydricGrid(self, ID)
            self.tableWindow.Show()

    def OnCloseWindow(self, event):
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


class HydricGrid(wx.Frame):
    ''' Classe responsável pelo Grid da curva de demanda. '''

    def __init__(self, parent, ID):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.SetTitle('Adicionar curva de rendimento')
        self.CentreOnScreen()

        self.ID = ID
        self.curRow = 0
        self.rowLength = 24

        self.parent = parent
        self.waterWindow = None

        self.currentlySelectedCell = (0, 0)
        self.toolbar = self.CreateToolBar()

        self.initToolbar()
        self.createUI()

        self.grid.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onRowSelected)
        self.grid.Bind(wx.EVT_KEY_DOWN, self.OnKey)

        self.LoadFile()
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def initToolbar(self):
        ''' Inicializa a toolbar. '''

        save_tool = self.toolbar.AddTool(wx.ID_SAVE, 'Salvar', wx.Bitmap('assets/images/save.png'), 'Salvar')
        database_tool = self.toolbar.AddTool(wx.ID_ANY, 'Database', wx.Bitmap('assets/images/database.png'), 'Database')

        self.Bind(wx.EVT_TOOL, self.OnSave, save_tool)
        self.Bind(wx.EVT_TOOL, self.OnDatabase, database_tool)

        self.toolbar.Realize()

    def createUI(self):
        ''' Cria a tabela e a checkbox. '''

        sizer = wx.BoxSizer(wx.VERTICAL)
        hBox = wx.BoxSizer(wx.HORIZONTAL)

        self.checkBox = wx.CheckBox(self, -1)
        self.checkBox.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)
        text = wx.StaticText(self, -1, 'Usar dados de Consumo de Água')
        hBox.Add(self.checkBox)
        hBox.Add(text)

        sizer.Add(hBox, flag=wx.ALL, border=5)

        self.grid = gridlib.Grid(self, -1)
        self.grid.CreateGrid(24, 2)
        self.grid.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        self.grid.SetColSize(0, 125)
        self.grid.SetColSize(1, 125)

        self.grid.SetColLabelValue(0, 'Hora')
        self.grid.SetColLabelValue(1, 'Consumo')

        time = [0, 0]
        for row in range(0, self.rowLength):
            self.grid.SetCellValue(row, 0, dp.addMinutes(time, 60))
            self.grid.SetReadOnly(row, 0)

        sizer.Add(self.grid)
        self.SetSizerAndFit(sizer)

        if not '#water_consumption_start' in gv.fileStartIndices.keys():
            self.checkBox.Enable(False)

    def OnCheckBox(self, event):
        ''' Chamada quando a wx.self.CheckBox é clicada. '''

        if self.checkBox.GetValue():
            self.grid.Enable(False)
        else:
            self.grid.Enable(True)

    def onGetSelection(self, event):
        """
        Pega as células que estão atualmente selecionadas.
        """
        cells = self.grid.GetSelectedCells()
        if not cells:
            if self.grid.GetSelectionBlockTopLeft():
                top_left = self.grid.GetSelectionBlockTopLeft()[0]
                bottom_right = self.grid.GetSelectionBlockBottomRight()[0]
                self.copyToClipboard(top_left, bottom_right)

            # Qualquer destes elses abaixo lida caso apenas uma célula estiver selecionada.
            else:
                self.copyToClipboard(onlyCell=self.currentlySelectedCell)
        else:
            self.copyToClipboard(onlyCell=cells)


    def copyToClipboard(self, top_left=None, bottom_right=None, onlyCell=None):
        """
        A explicação deste código, que compreende as funções `onGetSelection`, `copyToClipboard` e `onRowSelected` (no link descrita como `onSingleSelect`),
        está em: https://www.blog.pythonlibrary.org/2013/10/31/wxpython-how-to-get-selected-cells-in-a-grid/

        Pequenas modificações tiveram que ser feitas para servir ao propósito deste programa, o Ctrl + C.
        """

        # Se apenas uma célula estiver selecionada...
        if onlyCell:
            cells = [onlyCell]
            cols_start = 0
        else:
            cells = []

            rows_start = top_left[0]
            rows_end = bottom_right[0]
            cols_start = top_left[1]
            cols_end = bottom_right[1]
            rows = range(rows_start, rows_end+1)
            cols = range(cols_start, cols_end+1)
            cells.extend([(row, col) for row in rows for col in cols])

        out = ''
        j = cols_start
        for cell in cells:
            row, col = cell
            if j == 2:
                out += f"{self.grid.GetCellValue(row, col)}\n"
                j = 0
            else:
                out += f"{self.grid.GetCellValue(row, col)}\t"

            j += 1

        data = wx.TextDataObject().SetText(out)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    def onRowSelected(self, event):
        ''' Chamada quando o usuário mudar de célula. '''

        self.curRow = event.GetRow()
        self.currentlySelectedCell = (event.GetRow(), event.GetCol())

    def LoadFile(self):
        ''' Carrega dos dados para a tabela, se existirem. '''

        curvas = [self.parent.opt1Curva, self.parent.opt2Curva]
        waterData = [self.parent.isUsingWaterData1, self.parent.isUsingWaterData2]

        if waterData[self.ID][0] == True:
            self.checkBox.SetValue(True)
            self.OnCheckBox(None)

        elif curvas[self.ID]:
            for i in range(0, len(curvas[self.ID])):
                value = curvas[self.ID][i]
                self.grid.SetCellValue(i, 1, str(value))

    def OnKey(self, event):
        ''' Chamada quando o usuário apertar qualquer tecla. Só reage a Ctrl + C ou Ctrl + V. '''

        # Se Ctrl + C
        if event.ControlDown() and event.GetKeyCode() == 67:
            self.onGetSelection(None)

        # Se Ctrl + V
        if event.ControlDown() and event.GetKeyCode() == 86:
            text_data = wx.TextDataObject()
            if wx.TheClipboard.Open():
                success = wx.TheClipboard.GetData(text_data)
                wx.TheClipboard.Close()

            if success:
                text = text_data.GetText()
                self.copyClipboardToTable(text)

        event.Skip()

    def analizeCheckBox(self, ID):
        ''' Analise o status da CheckBox e age de acordo. Retorna True se marcada. '''

        if ID == 0:
            isWaterData = self.parent.isUsingWaterData1
            btn = self.parent.opt1Fields[3]
        else:
            isWaterData = self.parent.isUsingWaterData2
            btn = self.parent.opt2Fields[3]

        value = self.checkBox.GetValue()
        if value:
            isWaterData[0] = True
            btn.SetLabel('Salvo: Cons. Água')
        else:
            isWaterData[0] = False

        return value

    def OnSave(self, event):
        ''' Chamda quando o usuário clica em Salvar. Retorna True se for salvo com sucesso.'''

        ID = self.ID
        isOK = True
        data = []

        if self.analizeCheckBox(ID):
            self.setWaterData(ID)
            dlg = wx.MessageDialog(self, f'Curva de demanda da opção {ID + 1} foi salva com sucesso.', 'Sucesso', wx.ICON_INFORMATION)
            dlg.ShowModal()
            return

        for row in range(0, self.rowLength):
            value = self.grid.GetCellValue(row, 1)
            if dp.isFloat(value) and float(value) > 0:
                self.grid.SetCellBackgroundColour(row, 1, wx.NullColour)
                data.append(float(value))
            else:
                self.grid.SetCellBackgroundColour(row, 1, gv.RED_ERROR)
                isOK = False

        if isOK:
            if ID == 0:
                self.parent.opt1Fields[3].SetLabel('Salvo')
                dp.colorField(self.parent.opt1Fields[3], False)
                self.parent.opt1Curva = data[:]
            else:
                self.parent.opt2Fields[3].SetLabel('Salvo')
                dp.colorField(self.parent.opt1Fields[3], False)
                self.parent.opt2Curva = data[:]

            dlg = wx.MessageDialog(self, f'Curva de demanda da opção {ID + 1} foi salva com sucesso.', 'Sucesso', wx.ICON_INFORMATION)

        else:
            dlg = wx.MessageDialog(self, f'Por favor, corriga os erros da tabela e tente novamente.', 'Erro', wx.ICON_ERROR)

        dlg.ShowModal()
        self.grid.ForceRefresh()
        return isOK

    def setWaterData(self, ID):
        ''' Pega os dados de consumo de água no arquivo e atribui as variáveis data1 ou data2. '''

        if ID == 0:
            data = self.parent.opt1Curva
        else:
            data = self.parent.opt2Curva

        data.clear()
        dics = fm.copyWaterFileDataToList()
        dics = dp.getTableReadyData(dics)
        data = dics[:]

    def OnDatabase(self, event):
        ''' Abre o database direto em Consumo de Água. '''

        if not self.waterWindow:
            self.waterWindow = water_database.WaterDataBase(self)
            self.waterWindow.Show()

    def copyClipboardToTable(self, text):
        ''' Copia o texto da área de transferência para a tabela. '''

        row = self.curRow

        for line in text.splitlines():
            if row < self.rowLength:
                self.grid.SetCellValue(row, 1, line.strip())
            else:
                break

            row += 1

    def OnCloseWindow(self, event):
        ''' Função chamada quando o usuario clica no botao de fechar no canto superior direito. '''

        self.Destroy()
        self.parent.tableWindow = None