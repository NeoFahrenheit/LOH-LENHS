'''
Arquivo responsavel pelas janelas auxiliares criadas a partir do botão Parametros do Sistema.
parameters_windows.py
'''

import wx
import wx.grid as gridlib
import numpy as np
from scipy.optimize import curve_fit
from intersect import intersection
import matplotlib.pyplot as plt
import global_variables as gv
import file_manager as fm
import data_processing as dp

class PumpWindow(wx.Panel):
    ''' Classe responsavel pela janela de `Curva da Bomba`. '''

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.rowSize = 24
        self.curRow = 0
        self.isSaved = True
        self.currentlySelectedCell = (0, 0)

        self.q = [] # Vazão
        self.h = [] # Altura Manométrica

        self.toolbar = wx.ToolBar(self, -1)
        self.initToolbar()
        self.initUI()

        self.LoadFile()

        self.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.OnCellChange)
        self.grid.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onRowSelected)
        self.grid.Bind(wx.EVT_KEY_DOWN, self.OnKey)

    def initUI(self):
        ''' Cria a tabela. '''

        masterSizer = wx.BoxSizer(wx.VERTICAL)
        self.grid = gridlib.Grid(self)
        self.grid.CreateGrid(self.rowSize, 2)
        self.grid.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        self.grid.SetColLabelValue(0, 'Q')
        self.grid.SetColLabelValue(1, 'H')

        self.grid.SetColSize(0, 130)
        self.grid.SetColSize(1, 130)

        masterSizer.Add(self.toolbar, flag=wx.EXPAND)
        masterSizer.Add(self.grid, 1, flag=wx.EXPAND)

        self.SetSizer(masterSizer)

    def initToolbar(self):
        ''' Inicializa a toolbar. '''

        clear_tool = self.toolbar.AddTool(-1, 'Limpar tabela', wx.Bitmap('images/remove.png'), 'Limpar tabela')
        draw_tool = self.toolbar.AddTool(-1, 'Desenhar Gráfico', wx.Bitmap('images/graph.png'), 'Desenhar gráfico')
        info_tool = self.toolbar.AddTool(wx.ID_INFO, 'Ajuda', wx.Bitmap('images/info.png'), 'Ajuda')

        self.Bind(wx.EVT_TOOL, self._OnClear, clear_tool)
        self.Bind(wx.EVT_TOOL, self.OnDraw, draw_tool)
        self.Bind(wx.EVT_TOOL, self.OnInfo, info_tool)

        self.toolbar.Realize()

    def onGetSelection(self, event):
        """
        Pega todas as células que estão atualmente selecionadas.
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
            if j == 1:
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
        ''' Chamada quando o usuário clica em uma celula. '''

        self.curRow = event.GetRow()
        self.currentlySelectedCell = (event.GetRow(), event.GetCol())

        event.Skip()

    def OnKey(self, event):
        ''' Chamada quando o usuário apertar qualquer tecla. Só reage a Ctrl + C ou Ctrl + V. '''

        # Ctrl + C
        if event.ControlDown() and event.GetKeyCode() == 67:
            self.onGetSelection(None)

        # Ctrl + V
        if event.ControlDown() and event.GetKeyCode() == 86:
            text_data = wx.TextDataObject()
            if wx.TheClipboard.Open():
                success = wx.TheClipboard.GetData(text_data)
                wx.TheClipboard.Close()

            if success:
                text = text_data.GetText()
                self.copyClipboardToTable(text)

        event.Skip()

    def copyClipboardToTable(self, text):
        ''' Copia o `text` extraído do Clipboard para a tabela. '''

        row = self.curRow
        for line in text.splitlines():
            if row < self.rowSize:
                words = line.split()
                size = len(words)
                if size <= 2:
                    for i in range(0, size):
                        self.grid.SetCellValue(row, i, words[i].strip())
            else:
                break

            row += 1

        self.isSaved = False
        self.parent.updateTitleName()

    def OnSave(self):
        ''' Salva o arquivo. '''

        if not self.checkAndTransferToLists():
            wx.MessageBox('Erros encontrados na tabela da Bomba do Sistema. Consule a janela de ajuda, se necesário.', 'Curva da Bomba', wx.OK | wx.ICON_ERROR)
            return

        if gv.opened_file:
            if not self.isSaved:
                self.writePumpDataToFile()
                self.isSaved = True
                self.parent.updateTitleName()
                return True

        # Se o usuário estiver criando um arquivo do zero...
        else:
            dialog = wx.FileDialog(self, f"Escolha um nome para o arquivo {gv.file_suffix}", gv.file_dir, '', f'*{gv.file_suffix}*', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            if dialog.ShowModal() == wx.ID_OK:
                fm.saveAndUpdateFileVariables(dialog)

                # Cria o arquivo, apenas.
                with open(gv.file_path, "wb"):
                    pass

                gv.opened_file = open(gv.file_path, 'r')

                dialog.Destroy()
                self.writePumpDataToFile()
                self.isSaved = True
                self.parent.LoadFile()
                return True

            return False

    def LoadFile(self):
        if gv.opened_file and '#parameters_pump_start' in gv.fileStartIndices.keys():
            start = gv.fileStartIndices['#parameters_pump_start']
            end = gv.fileStartIndices['#parameters_pump_end']

            # Se a área de dados estiver vazia, start vai apontar para o mesmo lugar que end, afinal start sempre aponta para o início dos dados.
            if start == end:
                self.isSaved = True
                self._OnClear(None)
                return True

            count = 0
            for i in range(start, end):
                q, h = gv.fileLines[i].strip().split()

                self.grid.SetCellValue(count, 0, q)
                self.grid.SetCellValue(count, 1, h)
                count += 1

            self.isSaved = True

    def isTherePumpData(self):
        ''' Retorna True se houver dados de Curva do Sistema. '''

        if not '#parameters_pump_start' in gv.fileStartIndices:
            return False

        start = gv.fileStartIndices['#parameters_pump_start']
        end = gv.fileStartIndices['#parameters_pump_end']

        # Se a área de dados estiver vazia, start vai apontar para o mesmo lugar que end, afinal start sempre aponta para o início dos dados.
        if start == end:
            return False

        return True

    def OnDraw(self, event):
        ''' Chamada quando o usuário clica para desenhar. '''

        if not self.checkAndTransferToLists():
            wx.MessageBox('Erros encontrados na tabela. Consule a janela de ajuda, se necesário.', 'Erros encontrados', wx.OK | wx.ICON_ERROR)
            return

        else:
            self.plotGraph()

    def _OnClear(self, event):
        ''' Limpa a tabela e as listas de dados. Deve ser chamada apenas pela própria classe. '''

        self.grid.ClearGrid()
        self.q.clear()
        self.h.clear()
        self.isSaved = False
        self.parent.updateTitleName()

    def onFileBeingClosed(self):
        ''' Chamada quando o arquivo é fechado. Neste caso, é similar a _OnClear(), mas self.isSaved é setado para True. '''

        self.grid.ClearGrid()
        self.q.clear()
        self.h.clear()
        self.isSaved = True

    def OnCellChange(self, event):
        ''' Chamada quando o usuário modifica alguma célula. '''

        self.isSaved = False
        self.parent.updateTitleName()
        event.Skip()

    def OnInfo(self, event):
        ''' Chamada quando o usuário clica no botão de ajuda. '''

        text = """Preencha a coluna Q, vazão(m³/s), e a coluna H, altura nanométrica (m). Fique atento aos erros:
        Use ponto, (.), como separador de casa decimal e não use valores negativos.
        Células em vermelho significam erro numérico.
        Fileiras em amarelo significa que você não terminou de preencher aquela fileira.
        Os dados Q precisam estar ordenados.
        A tabela precisa ter, no mínimo, 4 pares de dados [Q, H].
        Quando terminar, use o ícone de desenhar o gráfico na parte superior da janela."""

        wx.MessageBox(text, 'Como usar', wx.ICON_INFORMATION, self)


    def writePumpDataToFile(self):
        ''' Escreve as modificações da tabela no arquivo. '''

        before = []

        # Sempre vamos colocar nossos dados no início do arquivo. Se dados de água ja existirem, vamos apagá-lo totalmente e reescrever os de agora.
        # Se não, vamos colocar esses dados no início e todo o resto depois.
        if '#parameters_pump_start' in gv.fileStartIndices.keys():
            before = gv.fileLines[ : gv.fileStartIndices['#parameters_pump_start'] - 1]
            after = gv.fileLines[gv.fileStartIndices['#parameters_pump_end'] + 1 : ] # O índice de fim aponta exatamente para o indicador.
        else:
            after = gv.fileLines

        outText = before
        outText += ['#parameters_pump_start\n']

        # Se a lista não estiver vazia, vamos escrever os dados.
        if self.q:
            for line in zip(self.q, self.h):
                outText.append(f"{line[0]} {line[1]}\n")

        outText += '#parameters_pump_end\n'
        outText += after

        # Fechamos o arquivo e o apagamos totalmente.
        gv.opened_file.close()
        gv.opened_file = open(gv.file_path, 'w')

        # Reescrevemos do zero.
        gv.opened_file.write(''.join(outText))
        gv.opened_file.close()

        # Reabrimos em modo de leitura.
        gv.opened_file = open(gv.file_path, 'r')

        fm.getEntrysDictAndFile()

    def isTableEmpty(self):
        ''' Verifica se a tabela está vazia. Retorna `True` caso sim. '''

        for i in range(0, self.rowSize):
            for j in range(0, 2):
                value =  self.grid.GetCellValue(i, j)
                if not value.isspace() and value != '':
                    return False
        return True

    def checkAndTransferToLists(self):
        ''' Procura por erros na tabela e transfere os dados para as listas. Caso encontre erros, retorna False e limpa as listas. Colore as células de acordo. '''

        self.q.clear()
        self.h.clear()

        # A checagem de células vazias é feita nas tabelas, não nas listas.
        # Demos clear() apenas para ter a certeza de que se a tabela estiver vazia, não haja nada nas listas.
        if self.isTableEmpty():
            return True

        count = 0

        isOK = True

        for i in range(0, self.rowSize):
            if self.isThereHole(i):
                isOK = False
                continue

            for j in range(0, 2):
                value = self.grid.GetCellValue(i, j)
                if (dp.isInt(value) or dp.isFloat(value)) and float(value) >= 0:
                    self.grid.SetCellBackgroundColour(i, j, wx.NullColour)
                    if j == 0:
                        self.q.append(float(value))
                        count += 1
                    else:
                        self.h.append(float(value))

                else:
                    if value != '':
                        self.grid.SetCellBackgroundColour(i, j, gv.RED_ERROR)
                        isOK = False

        if not isOK or not dp.checkSorting(self.q) or count < 4:
            self.q.clear()
            self.h.clear()
            isOK = False    # Precisamos disso caso apenas self.checkSorting() for falso.

        self.grid.ForceRefresh()
        return isOK

    def checkSorting(self, arr):
        ''' Verifica se a lista `arr` está ordenada. Retorna True se sim. `arr` não é modificado. '''

        sorted_arr = arr[:]
        sorted_arr.sort()

        for i in range(0, len(arr)):
            if sorted_arr[i] != arr[i]:
                return False

        return True

    def isThereHole(self, row):
        ''' Recebe uma fileira e verifica se há uma preenchida ou não. Retorna True em caso de sucesso.
        OBS: Retorna True apenas se haver uma preenchida e outra não. '''

        emptyCellFound = False
        notEmptyCellFound = False

        for i in range(0, 2):
            value = self.grid.GetCellValue(row, i)

            if value == '':
                emptyCellFound = True
            else:
                notEmptyCellFound = True

        isErrors = emptyCellFound and notEmptyCellFound
        if isErrors:
            self.grid.SetCellBackgroundColour(row, 0, gv.YELLOW_WARNING)
            self.grid.SetCellBackgroundColour(row, 1, gv.YELLOW_WARNING)
        else:
            self.grid.SetCellBackgroundColour(row, 0, wx.NullColour)
            self.grid.SetCellBackgroundColour(row, 1, wx.NullColour)

        return isErrors

    def calcultaP2(self):
        ''' Calcula o array P2. '''

        # Comeca a gerar a equação de 2 grau para a curva da bomba.
        self.valeur_T = np.array(self.q)
        self.valeur_min = np.array(self.h)
        self.P2 = np.polyfit(self.valeur_T, self.valeur_min, 2)

    def plotGraph(self, isToSave=False, path=''):
        ''' Desenha o gráfico. '''

        if isToSave:
            self.checkAndTransferToLists()

        self.calcultaP2()
        p = np.poly1d(self.P2)
        yhat = p(self.valeur_T)
        ybar = sum(self.valeur_min) / len(self.valeur_min)
        SST = sum((self.valeur_min - ybar) ** 2)
        SSreg = sum((yhat - ybar) ** 2)

        R2 = SSreg/SST

        fig, ax = plt.subplots(figsize=(11, 6))
        plt.suptitle('Curva da Bomba', x=0.06, y=0.98, ha='left', fontsize=15)

        # Informacoes do gráfico.
        ax.set_xlabel('Vazão (m³/s)')
        ax.set_ylabel('Altura Manométrica (m)')

        # remove spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        a = "{:.2f}".format(self.P2[0])
        b = "{:.2f}".format(self.P2[1])
        c = "{:.2f}".format(self.P2[2])
        R2 = "{:.2f}".format(R2)

        eq = f'f(x) = {a}x² + {b}x + {c}\n'
        eq += f'R²: {R2}'
        plt.title(eq, loc='left', fontsize=10)

        arr = dp.smoothGraph(np.array(self.valeur_T), np.array(self.valeur_min))

        plt.plot(arr[0], arr[1], '-', label='Curva da bomba', color='b')
        plt.plot(self.valeur_T, np.polyval(self.P2, self.valeur_T), 'o', label='Ponto [Q, H]')
        plt.legend(loc='best')

        plt.tight_layout()

        if isToSave:
            plt.savefig(path, bbox_inches='tight')
        else:
            plt.show()


class SystemWindow(wx.Panel):
    ''' Classe responsavel pela janela `Curva do Sistema`. '''

    def __init__(self, parent):
        super().__init__(parent)

        self.SetBackgroundColour('#bbbbbb')
        self.parent = parent
        self.isSaved = True

        self.isRugosidadeEnabled = True
        self.isSomatorioEnable = True

        self.toolbar = wx.ToolBar(self, -1)

        self.initToolbar()
        self.initUI()

        self.LoadFile()

    def initToolbar(self):
        ''' Inicializa a toolbar. '''

        draw_tool = self.toolbar.AddTool(-1, 'Desenhar Gráfico', wx.Bitmap('images/graph.png'), 'Desenhar gráfico')
        self.Bind(wx.EVT_TOOL, self.OnDraw, draw_tool)

        self.toolbar.Realize()

    def initUI(self):
        ''' Inicializa a UI. '''

        self.masterSizer = wx.BoxSizer(wx.VERTICAL)

        vBox = wx.BoxSizer(wx.VERTICAL)

        # Desnivel geométrico
        geoSizer = wx.BoxSizer(wx.HORIZONTAL)
        geoText = wx.StaticText(self, -1, 'Desnível geométrico (m)', size=(200,23))
        self.geoInput = wx.TextCtrl(self, -1)
        self.geoInput.Bind(wx.EVT_TEXT, self.OnValueChanged)
        geoImage = wx.Bitmap('images/question.png')
        geoBitmap = wx.StaticBitmap(self, -1, geoImage)
        geoTooltip = wx.ToolTip('Entre com o desnível geométrico em metros.')
        geoBitmap.SetToolTip(geoTooltip)
        geoSizer.Add(geoText, flag=wx.ALL, border=3)
        geoSizer.Add(self.geoInput)
        geoSizer.Add(geoBitmap, flag=wx.LEFT, border= 5)
        vBox.Add(geoSizer)

        # Comprimento da tubulação
        tubSizer = wx.BoxSizer(wx.HORIZONTAL)
        tubText = wx.StaticText(self, -1, 'Comprimento da tubulação (m)', size=(200,23))
        self.tubInput = wx.TextCtrl(self, -1)
        self.tubInput.Bind(wx.EVT_TEXT, self.OnValueChanged)
        tubImage = wx.Bitmap('images/question.png')
        tubBitmap = wx.StaticBitmap(self, -1, tubImage)
        tubTooltip = wx.ToolTip('Entre com o comprimento da tubulação em metros.')
        tubBitmap.SetToolTip(tubTooltip)
        tubSizer.Add(tubText, flag=wx.ALL, border=3)
        tubSizer.Add(self.tubInput)
        tubSizer.Add(tubBitmap, flag=wx.LEFT, border= 5)
        vBox.Add(tubSizer, flag=wx.TOP, border=5)

        # Diametro da tubulação
        diaTubSizer = wx.BoxSizer(wx.HORIZONTAL)
        diaTubText = wx.StaticText(self, -1, 'Diâmtro interno da tubulação (mm)', size=(200,23))
        self.diaTubInput = wx.TextCtrl(self, -1)
        self.diaTubInput.Bind(wx.EVT_TEXT, self.OnValueChanged)
        diaImage = wx.Bitmap('images/question.png')
        diaBitmap = wx.StaticBitmap(self, -1, diaImage)
        diaTooltip = wx.ToolTip('Entre com o comprimento interno da tubulação em milímetros.')
        diaBitmap.SetToolTip(diaTooltip)
        diaTubSizer.Add(diaTubText, flag=wx.ALL, border=3)
        diaTubSizer.Add(self.diaTubInput)
        diaTubSizer.Add(diaBitmap, flag=wx.LEFT, border= 5)
        vBox.Add(diaTubSizer, flag=wx.TOP, border=5)

        # Rugosidade do material
        rugMatSizer = wx.BoxSizer(wx.HORIZONTAL)
        rugMatStaticSizer = self.getRugosidadeStaticSizer()
        rugMatText = wx.StaticText(self, -1, 'Rugosidade do material (mm)', size=(200,23))
        self.rugMatInput = wx.TextCtrl(self, -1, name='rugosidade')
        self.rugMatInput.Bind(wx.EVT_TEXT, self.OnValueChanged)
        rugMatImage = wx.Bitmap('images/question.png')
        rugMatBitmap = wx.StaticBitmap(self, -1, rugMatImage)
        rugMatTooltip = wx.ToolTip('Entre com a rugosidade do material em milímetros. Se você não possuir este dado, preencha as variáveis abaixo. Para isto, deixe este campo em branco.')
        rugMatBitmap.SetToolTip(rugMatTooltip)
        rugMatSizer.Add(rugMatText, flag=wx.ALL, border=3)
        rugMatSizer.Add(self.rugMatInput)
        rugMatSizer.Add(rugMatBitmap, flag=wx.LEFT, border= 5)
        vBox.Add(rugMatSizer, flag=wx.TOP, border=5)
        vBox.Add(rugMatStaticSizer)

        # Somatório dos coeficientes de singularidade
        sumSizer = wx.BoxSizer(wx.HORIZONTAL)
        sumStaticSizer = self.getCoeficienteStaticSizer()
        sumText = wx.StaticText(self, -1, 'Somatório dos coeficientes de singularidade', size=(200,40))
        self.sumInput = wx.TextCtrl(self, -1, name='somatorio')
        self.sumInput.Bind(wx.EVT_TEXT, self.OnValueChanged)
        sumImage = wx.Bitmap('images/question.png')
        sumBitmap = wx.StaticBitmap(self, -1, sumImage)
        sumTooltip = wx.ToolTip('Entre com o somatório dos coeficientes de singularidade. Se você não possuir este dado, preencha as variáveis abaixo. Para isto, deixe este campo em branco.')
        sumBitmap.SetToolTip(sumTooltip)
        sumSizer.Add(sumText, flag=wx.ALL, border=3)
        sumSizer.Add(self.sumInput, flag=wx.TOP, border=5)
        sumSizer.Add(sumBitmap, flag=wx.LEFT | wx.TOP, border= 5)
        vBox.Add(sumSizer, flag=wx.TOP, border=10)
        vBox.Add(sumStaticSizer)

        self.masterSizer.Add(self.toolbar, flag=wx.EXPAND)
        self.masterSizer.Add(vBox, flag=wx.EXPAND | wx.RIGHT, border=2)
        self.SetSizer(self.masterSizer)
        self.Layout()

    def getRugosidadeStaticSizer(self):
        ''' Retorna o gridSizer das variáveis opcionais da rugosidade do material. '''

        gridSizer = wx.StaticBoxSizer(wx.VERTICAL, self, 'Preencha caso não possua o valor acima')

        # Material da tubulação
        matSizer = wx.BoxSizer(wx.HORIZONTAL)
        matText = wx.StaticText(self, -1, 'Material da tubulação', size=(150, 23))
        matList = ['Ferro Fundido', 'PVC', 'PEAD']
        self.matCombo = wx.ComboBox(self, -1, matList[0], choices=matList, style=wx.CB_READONLY, size=(102, 23))
        self.matCombo.Bind(wx.EVT_COMBOBOX, self.OnValueChanged)
        matSizer.Add(matText, flag=wx.TOP, border=3)
        matSizer.Add(self.matCombo)

        # Estado do material
        stateSizer = wx.BoxSizer(wx.HORIZONTAL)
        stateText = wx.StaticText(self, -1, 'Estado da tubulação', size=(150, 23))
        stateList = ['Nova', 'Antiga']
        self.stateCombo = wx.ComboBox(self, -1, stateList[0], choices=stateList, style=wx.CB_READONLY, size=(102, 23))
        self.stateCombo.Bind(wx.EVT_COMBOBOX, self.OnValueChanged)
        stateSizer.Add(stateText, flag=wx.TOP, border=3)
        stateSizer.Add(self.stateCombo)

        # Idade da tubulação
        ageSizer = wx.BoxSizer(wx.HORIZONTAL)
        ageText = wx.StaticText(self, -1, 'Idade da tubulação', size=(150, 23))
        self.ageInput = wx.TextCtrl(self, -1, size=(102, 23))
        self.ageInput.Bind(wx.EVT_TEXT, self.OnValueChanged)
        ageSizer.Add(ageText, flag=wx.TOP, border=3)
        ageSizer.Add(self.ageInput)

        # Adicionando os gridSizers.
        gridSizer.Add(matSizer)
        gridSizer.Add(stateSizer)
        gridSizer.Add(ageSizer)

        return gridSizer

    def getCoeficienteStaticSizer(self):
        ''' Retorna o gridSizer das variáveis opcionais do somatório dos coeficientes de singularidade. '''

        gridSizer = wx.StaticBoxSizer(wx.VERTICAL, self, 'Preencha caso não possua o valor acima')

        # Quantidade de curvas 45 graus
        _45Sizer = wx.BoxSizer(wx.HORIZONTAL)
        _45Text = wx.StaticText(self, -1, 'Quantidade de curvas 45°', size=(150, 23))
        self._45Input = wx.TextCtrl(self, -1, size=(102, 23))
        _45Sizer.Add(_45Text, flag=wx.TOP, border=3)
        _45Sizer.Add(self._45Input)

        # Quantidade de curvas 90 graus
        _90Sizer = wx.BoxSizer(wx.HORIZONTAL)
        _90Text = wx.StaticText(self, -1, 'Quantidade de curvas 90°', size=(150, 23))
        self._90Input = wx.TextCtrl(self, -1, size=(102, 23))
        _90Sizer.Add(_90Text, flag=wx.TOP, border=3)
        _90Sizer.Add(self._90Input)

        # Registros Globo
        globoSizer = wx.BoxSizer(wx.HORIZONTAL)
        globoText = wx.StaticText(self, -1, 'Registros globo', size=(150, 23))
        self.globoInput = wx.TextCtrl(self, -1, size=(102, 23))
        globoSizer.Add(globoText, flag=wx.TOP, border=3)
        globoSizer.Add(self.globoInput)

        # Registros Gaveta
        gavetaSizer = wx.BoxSizer(wx.HORIZONTAL)
        gavetaText = wx.StaticText(self, -1, 'Registros gaveta', size=(150, 23))
        self.gavetaInput = wx.TextCtrl(self, -1, size=(102, 23))
        gavetaSizer.Add(gavetaText, flag=wx.TOP, border=3)
        gavetaSizer.Add(self.gavetaInput)

        # Registros Esfera
        esferaSizer = wx.BoxSizer(wx.HORIZONTAL)
        esferaText = wx.StaticText(self, -1, 'Registro esfera', size=(150, 23))
        self.esferaInput = wx.TextCtrl(self, -1, size=(102, 23))
        esferaSizer.Add(esferaText, flag=wx.TOP, border=3)
        esferaSizer.Add(self.esferaInput)

        # Válvula de Retenção
        retencaoSizer = wx.BoxSizer(wx.HORIZONTAL)
        retencaoText = wx.StaticText(self, -1, 'Válvula de retenção', size=(150, 23))
        self.retencaoInput = wx.TextCtrl(self, -1, size=(102, 23))
        retencaoSizer.Add(retencaoText, flag=wx.TOP, border=3)
        retencaoSizer.Add(self.retencaoInput)

        # Quantidade de pé com crivo
        crivoSizer = wx.BoxSizer(wx.HORIZONTAL)
        crivoText = wx.StaticText(self, -1, 'Válvula de Pé com crivo', size=(150, 23))
        self.crivoInput = wx.TextCtrl(self, -1, size=(102, 23))
        crivoSizer.Add(crivoText, flag=wx.TOP, border=3)
        crivoSizer.Add(self.crivoInput)

        self.sumInputs = [self._45Input, self._90Input, self.globoInput, self.gavetaInput,
        self.esferaInput, self.retencaoInput, self.crivoInput] # Uma lista com as referencias dos wx.TextCtrl criados nesta função.

        for text in self.sumInputs:
            text.Bind(wx.EVT_TEXT, self.OnValueChanged)

        # Adicionando os gridSizers.
        gridSizer.Add(_45Sizer)
        gridSizer.Add(_90Sizer)
        gridSizer.Add(globoSizer)
        gridSizer.Add(gavetaSizer)
        gridSizer.Add(esferaSizer)
        gridSizer.Add(retencaoSizer)
        gridSizer.Add(crivoSizer)

        return gridSizer

    def checkErrors(self):
        ''' Procura por erros nos campos de texto e dropdown. Retorna True caso encontre erros, como também
        desabilita campos se certos campos de entrada estiverem preenchidos / corretos ou não. '''

        if self.isAllBlank():
            self.clearFields()
            self.isSaved = False    # Iremos sobreescrever o 'self.isSaved = True' existente na função acima.
            return False

        isOK = []

        # self.geoInput -> Desnivel geometrico
        isOK.append(self.checkValue(self.geoInput))

        # self.tubInput -> Comprimento da tubulação
        isOK.append(self.checkValue(self.tubInput))

        # self.diaTubInput - > # Diametro da tubulação
        isOK.append(self.checkValue(self.diaTubInput))

        # self.rugMatInput - > Rugosidade do material (possui name='rugosidade')
        if not self.checkValue(self.rugMatInput):
            if self.rugMatInput.GetValue().strip() != '':
                isOK.append(self.checkValue(self.rugMatInput))

        # self.sumInput -> Somatorio dos coeficientes de singularidade (possui name='somatorio')
        if not self.checkValue(self.sumInput):
            if self.sumInput.GetValue().strip() != '':
                isOK.append(self.checkValue(self.sumInput))

        if self.isRugosidadeEnabled:
            isOK.append(self.checkValue(self.ageInput))

        if self.isSomatorioEnable:
            isOK.append(self.checkOptionalSomatorio())

        return not all(isOK)

    def checkValue(self, srcInput):
        ''' Analisa o valor de uma caixa de texto e colore de acordo. Retorna True se estiver OK. '''

        isOK = True
        value = srcInput.GetValue()
        name = srcInput.GetName()

        isOpcional = name == 'rugosidade' or name == 'somatorio'
        isValueOK = (dp.isInt(value) or dp.isFloat(value)) and float(value) >= 0

        if isOpcional:
            if value == '' or value.isspace():
                # Ainda vamos retornar False se o campo estiver vazio, mas não vamos colorir de vermelho porque o campo é opcional.
                srcInput.SetOwnBackgroundColour(wx.NullColour)
                isOK = False
            else:
                if isValueOK:
                    srcInput.SetOwnBackgroundColour(wx.NullColour)
                else:
                    isOK = False
                    srcInput.SetOwnBackgroundColour(gv.RED_ERROR)
        else:
            if isValueOK:
                srcInput.SetOwnBackgroundColour(wx.NullColour)
            else:
                isOK = False
                srcInput.SetOwnBackgroundColour(gv.RED_ERROR)

        srcInput.Refresh()
        return isOK

    def checkOptionalSomatorio(self):
        ''' Checa os valores opcionais de Somatório dos coeficientes de singularidade. Retorna True se todos estiverem OK. '''

        isOK = True

        for field in self.sumInputs:
            value = field.GetValue().strip()

            if not ( dp.isInt(value) and int(value) >= 0 ):
                isOK = False
                field.SetOwnBackgroundColour(gv.RED_ERROR)
            else:
                field.SetOwnBackgroundColour(wx.NullColour)

            field.Refresh()

        return isOK

    def OnSave(self):
        ''' Chamada quando o usuário clica para salvar. '''

        if self.checkErrors():
            dlg = wx.MessageDialog(self, 'Por favor, corriga os erros da Curva do Sistema antes de continuar.', 'Curva do Sistema', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return False

        if gv.opened_file:
            self.writeSystemDataToFile()
            self.isSaved = True
            return True

        else:
            dialog = wx.FileDialog(self, f"Escolha um nome para o arquivo {gv.file_suffix}", gv.file_dir, '', f'*{gv.file_suffix}*', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            if dialog.ShowModal() == wx.ID_OK:
                fm.saveAndUpdateFileVariables(dialog)

                # Cria o arquivo, apenas.
                with open(gv.file_path, "w"):
                    pass

                gv.opened_file = open(gv.file_path, 'r')
                dialog.Destroy()

                self.writeSystemDataToFile()
                self.isSaved = True

                return True

            return False

    def OnDraw(self, event):
        ''' Chamada quando o usuário clica para desenhar o gráfico. '''

        if not self.checkErrors():
            if '#parameters_pump_start' in gv.fileStartIndices.keys():
                win = PumpWindow(self)
                win.checkAndTransferToLists()
                q = win.q
                win.Destroy()
                self.plotGraph(q)

            else:
                dlg = wx.MessageDialog(self, 'Entre com dados em "Curva da Bomba" para desenhar este gráfico, por favor.', 'Dados não encontrados', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
        else:
            dlg = wx.MessageDialog(self, 'Por favor, corriga os erros antes de continuar.', 'Erros encontrados', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()

    def getATMValues(self, q):
        ''' Preenche a lista self.h com os valores ATM. '''

        self.h = []
        for vazao in q:
            if vazao == 0:
                self.h.append(self.HG)
            else:
                self.h.append(self.calculateAMT(vazao))


    def plotGraph(self, q, isToSave=False, path=''):
        ''' Desenha o gráfico. '''

        if isToSave:
            win = PumpWindow(self)
            win.checkAndTransferToLists()
            q = win.q
            win.Destroy()

        self.HG = float(self.geoInput.GetValue())   # Desnivel geometrico (m)
        self.L = float(self.tubInput.GetValue())    # Comprimento da tubulação (m)
        self.D = float(self.diaTubInput.GetValue()) # Diametro interno da tubulação (m)
        self.rug = float(self.rugMatInput.GetValue())   # Rugosidade do material

        self.KS = 0
        value = self.sumInput.GetValue()            # Somatorio dos coeficientes de singularidades
        if value == '' or value.isspace():
            self.getSumInputValue()
        else:
            self.KS = float(self.sumInput.GetValue())

        self.D = self.D / 1000

        self.getATMValues(q)

        fig, ax = plt.subplots(figsize=(11, 6))
        plt.suptitle('Curva do Sistema', x=0.06, y=0.98, ha='left', fontsize=15)

        # Informacoes do gráfico.
        ax.set_xlabel('Vazão (m³/s)')
        ax.set_ylabel('Altura Nanométrica (m)')

        # remove spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        arr = dp.smoothGraph(np.array(q), np.array(self.h))

        plt.plot(arr[0], arr[1], '-', label='Curva do Sistema', color='r')
        plt.legend(loc='best')
        plt.tight_layout()

        if isToSave:
            plt.savefig(path, bbox_inches='tight')
        else:
            plt.show()

    def calculateAMT(self, vazao):
        ''' Calcula o valor da altura nanometrica. '''

        G = 9.81    # Aceleracao da gravidade (m/s²)
        V = vazao / (np.pi * (pow(self.D, 2) / 4))  # Velocidade (m/s)
        reynolds = (V * self.D) / 0.000001
        F = self.calculatePerdaCarga(self.rug, self.D, reynolds)  # Fator perda de carga

        return self.HG + ( (F * self.L * pow(V, 2)) / (2 * G * self.D) ) + self.KS * ( (pow(V, 2)) / (2 * G) )

    def calculatePerdaCarga(self, rugosidade, diametro, reynolds):
        ''' Calcula o fator perda de carga. '''

        if reynolds < 2300:
            result = 64 / reynolds

        else:
            f0 = 0.000001
            f1 = (1 / 4) * pow(np.log10(rugosidade / (3.706 * diametro) + 2.51 / (reynolds * np.sqrt(f0))), -2)
            k = abs((f1 - f0) / f1)

            while k > 0.000001:
                f1 = (1 / 4) * pow(np.log10(rugosidade / (3.706 * diametro) + 2.51 / (reynolds * np.sqrt(f0))), -2)
                k = abs((f1 - f0) / f1)
                f0 = f1

            result = f1

        return result

    def getSumInputValue(self):
        ''' Chamada para conseguir um valor para o somatório dos coeficientes de singularidade, quando este
        não for preenchido. '''

        self.KS = 0

        for i in range(0, 7):
            if i == 0:
                self.KS += int(self.sumInputs[i].GetValue()) * 0.2  # Curvas 45 graus
            elif i == 1:
                self.KS += int(self.sumInputs[i].GetValue()) * 0.4  # Curvas 90 graus
            elif i == 2:
                self.KS += int(self.sumInputs[i].GetValue()) * 10   # Registros globo
            elif i == 3:
                self.KS += int(self.sumInputs[i].GetValue()) * 0.2  # Registros gaveta
            elif i == 4:
                self.KS += int(self.sumInputs[i].GetValue()) * 5    # Registros esfera
            elif i == 5:
                self.KS += int(self.sumInputs[i].GetValue()) * 10   # Valvula de retencao
            elif i == 6:
                self.KS += int(self.sumInputs[i].GetValue()) * 3    # Valvula pe com crivo

    def clearFields(self):
        ''' Limpa os campos de texto. '''

        inputs = [self.geoInput, self.tubInput, self.diaTubInput, self.rugMatInput, self.ageInput, self.sumInput]

        self.matCombo.SetValue('Ferro Fundido')
        self.stateCombo.SetValue('Nova')

        for field in inputs:
            field.Clear()
            field.SetBackgroundColour(wx.NullColour)
            field.Refresh()

        for field in self.sumInputs:
            field.Clear()
            field.SetBackgroundColour(wx.NullColour)
            field.Refresh()

        self.isSaved = True
        self.parent.updateTitleName()

    def isAllBlank(self):
        ''' Checa se todos os campos estão vazios. Naturalmente, desconsidera as dropdown
        `Material da tubulação` e `Estado da tubulação`. Retorna True em caso afirmativo. '''

        fields = [self.geoInput, self.tubInput, self.diaTubInput, self.rugMatInput, self.sumInput,
        self.ageInput]

        for item in self.sumInputs:
            fields.append(item)

        for item in fields:
            value = item.GetValue()
            if not value.isspace() and value != '':
                return False

        return True

    def writeSystemDataToFile(self):
        ''' Escreve os dados no arquivo. '''

        index = gv.fileStartIndices['#parameters_system_start']
        self.flushFields(index)

        # Fechamos o arquivo e o apagamos totalmente.
        gv.opened_file.close()
        gv.opened_file = open(gv.file_path, 'w')

        # Reescrevemos do zero.
        gv.opened_file.write(''.join(gv.fileLines))
        gv.opened_file.close()

        # Reabrimos em modo de leitura.
        gv.opened_file = open(gv.file_path, 'r')

    def isThereSystemData(self):
        ''' Retorna True se houver dados da Curva do Sistema no arquivo. '''

        if not '#parameters_system_start' in gv.fileStartIndices:
            return False

        start = gv.fileStartIndices['#parameters_system_start']
        end = gv.fileStartIndices['#parameters_system_end']

        if start == end:
            return False

        return True

    def LoadFile(self):
        ''' Carrega o arquivo aberto. '''

        if gv.opened_file and '#parameters_system_start' in gv.fileStartIndices.keys():
            index = gv.fileStartIndices['#parameters_system_start']

            # Se a área de dados estiver vazia...
            if index == gv.fileStartIndices['#parameters_system_end']:
                self.isSaved = True
                self.checkErrors()  # Usamos isso para pintar os campos de volta pra wx.NullColour.
                return

            self.geoInput.SetValue(gv.fileLines[index].strip())
            index += 1
            self.tubInput.SetValue(gv.fileLines[index].strip())
            index += 1
            self.diaTubInput.SetValue(gv.fileLines[index].strip())
            index += 1

            if gv.fileLines[index].strip() == '':   # Rugosidade do material
                self.rugMatInput.Clear()
                index += 1
                self.matCombo.SetValue(gv.fileLines[index].strip())
                index += 1
                self.stateCombo.SetValue(gv.fileLines[index].strip())
                index += 1
                self.ageInput.SetValue(gv.fileLines[index].strip())
                index += 1
            else:
                self.rugMatInput.SetValue(gv.fileLines[index].strip())
                index += 1
                # Material da tubulação. Vamos deixar o valor default.
                index += 1
                # Estado da tubulação. Vamos deixar o valor default.
                index += 1
                self.ageInput.Clear()
                index += 1

            if gv.fileLines[index].strip() == '':
                self.sumInput.Clear()
                index += 1

                for field in self.sumInputs:
                    field.SetValue(gv.fileLines[index].strip())
                    index += 1

            else:
                self.sumInput.SetValue(gv.fileLines[index].strip())
                index += 1

                for field in self.sumInputs:
                    field.Clear()
                    index += 1

            self.isSaved = True
            self.checkErrors()  # Usamos isso para pintar os campos de volta pra wx.NullColour.

    def flushFields(self, index):
        ''' Substitui os dados de todos os campos no arquivo. '''

        if self.isAllBlank():
            if self.isThereSystemData():    # Se a tabela estover vazia e existe dados ali, então só precisamos apagar tudo.
                for _ in range(0, 15):
                    del gv.fileLines[index]

                gv.fileStartIndices['#parameters_system_end'] -= 15
                return
            else:
                return

        else:
            if not self.isThereSystemData(): # Se a tabela contém dados, mas o arquivo tá sem, precisamos criar espaço.
                for _ in range(0, 15):
                    gv.fileLines.insert(index, '\n')
                gv.fileStartIndices['#parameters_system_end'] += 15

        gv.fileLines[index] = f'{self.geoInput.GetValue().strip()}\n'
        index += 1
        gv.fileLines[index] = f'{self.tubInput.GetValue().strip()}\n'
        index += 1
        gv.fileLines[index] = f'{self.diaTubInput.GetValue().strip()}\n'
        index += 1

        if self.rugMatInput.GetValue().strip() == '':
            gv.fileLines[index] = '\n'
            index += 1
            gv.fileLines[index] = f'{self.matCombo.GetValue()}\n'
            index += 1
            gv.fileLines[index] = f'{self.stateCombo.GetValue()}\n'
            index += 1
            gv.fileLines[index] = f'{self.ageInput.GetValue().strip()}\n'
            index += 1
        else:
            gv.fileLines[index] = f'{self.rugMatInput.GetValue().strip()}\n'
            index += 1
            gv.fileLines[index] = '\n'
            index += 1
            gv.fileLines[index] = '\n'
            index += 1
            gv.fileLines[index] = '\n'
            index += 1

        if self.sumInput.GetValue().strip() == '':
            gv.fileLines[index] = '\n'
            index += 1

            for field in self.sumInputs:
                gv.fileLines[index] = f'{field.GetValue().strip()}\n'
                index += 1
        else:
            gv.fileLines[index] = f'{self.sumInput.GetValue().strip()}\n'
            index += 1

            for field in self.sumInputs:
                gv.fileLines[index] = f'\n'
                index += 1

    def OnValueChanged(self, event):
        """ Evento chamado quando usuário aperta alguma tecla em qualquer um dos campos de texto ou muda de opcao em um dropdown. """

        evtName = event.GetEventObject().Name

        if evtName == 'rugosidade':
            if self.checkValue(self.rugMatInput):
                self.setRugosidadeEnabled(False)
            else:
                self.setRugosidadeEnabled(True)

        elif evtName == 'somatorio':
            if self.checkValue(self.sumInput):
                self.setSomatorioEnabled(False)
            else:
                self.setSomatorioEnabled(True)

        self.isSaved = False
        self.parent.updateTitleName()

    def setRugosidadeEnabled(self, isEnable):
        ''' Habilita ou desabilita os campos opcionais de ``Rugosidade do Material``. '''

        if self.isRugosidadeEnabled == isEnable:
            return

        self.matCombo.Enable(isEnable)
        self.stateCombo.Enable(isEnable)
        self.ageInput.Enable(isEnable)

        self.isRugosidadeEnabled = isEnable

    def setSomatorioEnabled(self, isEnable):
        ''' Habilita ou desabilita os campos opcionais de ``Rugosidade do Material``. '''

        if self.isSomatorioEnable == isEnable:
            return

        for field in self.sumInputs:
            field.Enable(isEnable)

        self.isSomatorioEnable = isEnable


class OperationPoint(wx.Panel):
    ''' Classe responsavel pela janela Ponto de Operacao presente em Parametros do Sistema. '''

    def __init__(self, parent):
        super().__init__(parent)

        self.SetBackgroundColour('#bbbbbb')
        self.parent = parent

        self.toolbar = wx.ToolBar(self, -1)
        self.initToolbar()
        self.initUI()

    def initToolbar(self):
        ''' Inicializa a toolbar. '''

        draw_tool = self.toolbar.AddTool(-1, 'Desenhar Gráfico', wx.Bitmap('images/graph.png'), 'Desenhar gráfico')
        self.Bind(wx.EVT_TOOL, self.OnDraw, draw_tool)

        self.toolbar.Realize()


    def initUI(self):
        ''' Inicializa a UI. '''

        masterSizer = wx.BoxSizer(wx.VERTICAL)

        masterSizer.Add(self.toolbar, flag=wx.EXPAND)
        masterSizer.Add( wx.StaticText(self, -1, 'Nesta janela você pode calcular o ponto de operação do sistema.') )

        self.SetSizer(masterSizer)

    def OnDraw(self, event):
        ''' Chamada quando o usuário clica para desenhar o gráfico. '''

        if not self.parent.pumpRef.isTherePumpData():
            dlg = wx.MessageDialog(self, 'Por favor, preencha os dados em Curva da Bomba antes de continuar.', 'Dados não encontrados', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return

        if not self.parent.systemRef.isThereSystemData():
            dlg = wx.MessageDialog(self, 'Por favor, preencha os dados em Curva do Sistema antes de continuar.', 'Dados não encontrados', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return

        self.plotGraph()

    def getSumInputValue(self):
        ''' Funcao chamada para conseguir um valor para o somatorio dos coeficientes de singularidade, quando este
        não estiver preenchido no arquivo. '''

        start = gv.fileStartIndices['#parameters_system_start'] + 8

        for i in range(0, 7):
            if i == 0:
                self.KS += int(gv.fileLines[i + start]) * 0.2  # Curvas 45 graus
            elif i == 1:
                self.KS += int(gv.fileLines[i + start]) * 0.4  # Curvas 90 graus
            elif i == 2:
                self.KS += int(gv.fileLines[i + start]) * 10   # Registros globo
            elif i == 3:
                self.KS += int(gv.fileLines[i + start]) * 0.2  # Registros gaveta
            elif i == 4:
                self.KS += int(gv.fileLines[i + start]) * 5    # Registros esfera
            elif i == 5:
                self.KS += int(gv.fileLines[i + start]) * 10   # Valvula de retencao
            elif i == 6:
                self.KS += int(gv.fileLines[i + start]) * 3    # Valvula pe com crivo

    def getSystemVariables(self):
        ''' Pega as variáveis de Curva do Sistema no arquivo. '''

        i = gv.fileStartIndices['#parameters_system_start']
        self.G = 9.81    # Aceleracao da gravidade (m/s²)
        self.HG = float(gv.fileLines[i])        # Desnivel geometrico (m)
        self.L = float(gv.fileLines[i + 1])     # Comprimento da tubulação (m)
        self.D = float(gv.fileLines[i + 2])     # Diametro interno da tubulação (m)
        self.rug = float(gv.fileLines[i + 3])   # Rugosidade do material

        self.KS = gv.fileLines[i + 7]           # Somatorio dos coeficientes de singularidades
        if self.KS.strip() == '':
            self.KS = 0
            self.getSumInputValue()
        else:
            self.KS = float(gv.fileLines[i + 7])

        self.D = self.D / 1000

    def plotGraph(self, isToSave=False, path=''):
        ''' Desenha o gráfico. '''

        self.getSystemVariables()

        win = PumpWindow(self)
        win.checkAndTransferToLists()
        self.xData = np.array(win.q)
        self.yData = np.array(win.h)
        win.Destroy()

        fig, ax = plt.subplots(figsize=(11, 6))
        plt.suptitle('Análise do Ponto de Operação', x=0.06, y=0.98, ha='left', fontsize=15)

        # Informacoes do gráfico.
        ax.set_xlabel('Vazão (m³/s)')
        ax.set_ylabel('Altura Nanométrica (m)')

        # remove spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        self.getATMValues(isToSave)

        if isToSave:
            plt.savefig(path, bbox_inches='tight')
        else:
            plt.show()

    def calculateReynolds(self, vazao):
        ''' Calcula o valor da altura nanometrica. '''

        V = vazao / (np.pi * (pow(self.D, 2) / 4))  # Velocidade (m/s)
        reynolds = (V * self.D) / 0.000001
        F = self.calculatePerdaCarga(self.rug, self.D, reynolds)  # Fator perda de carga

        return F

    def calculatePerdaCarga(self, rugosidade, diametro, reynolds):
        ''' Calcula o fator perda de carga. '''

        if reynolds < 2300:
            result = 64 / reynolds

        else:
            f0 = 0.000001
            f1 = (1 / 4) * pow(np.log10(rugosidade / (3.706 * diametro) + 2.51 / (reynolds * np.sqrt(f0))), -2)
            k = abs((f1 - f0) / f1)

            while k > 0.000001:
                f1 = (1 / 4) * pow(np.log10(rugosidade / (3.706 * diametro) + 2.51 / (reynolds * np.sqrt(f0))), -2)
                k = abs((f1 - f0) / f1)
                f0 = f1

            result = f1

        return result

    def curveFitHelper(self, X, C, d):
        return C * pow(X, d)

    def getATMValues(self, isToSave=False):
        ''' Gera um dado na lista operation_Y para cada valor na lista q (Curva da Bomba). '''

        self.HPL = []
        for X in self.xData:
            if X == 0:
                self.HPL.append(X)
                continue

            vel = ( X ) / (0.25 * np.pi * pow(self.D, 2))

            B = self.KS / (2 * self.G * pow(0.25, 2) * pow(np.pi, 2) * pow(self.D, 4))
            hps = B * pow(X, 2)

            self.F = self.calculateReynolds(X)
            hpl = ( self.F * self.L * pow(vel, 2) ) / ( 2 * self.G * self.D )

            self.HPL.append(hpl)

        xDataCopy = self.xData[:]
        yDataCopy = self.yData[:]

        self.yData = np.array(self.HPL)
        initialGuess = [1.0, 1.0]

        popt, pcov = curve_fit(self.curveFitHelper, self.xData[1:], self.yData[1:], initialGuess) # Tirando os primeiros zeros da lista.
        AMT = self.HG + (popt[0] * pow(self.xData, popt[1]) + (B * pow(self.xData, 2)))

        # plt.plot(self.xData, self.yData, 'r', label='fit params: a=%5.3f, d=%5.3f' % tuple(popt))

        self.systemEq = (B, popt[0], popt[1], self.HG)
        B = "{:.2f}".format(B)
        C = "{:.2f}".format(popt[0])
        d = "{:.3f}".format(popt[1])
        HG = "{:.2f}".format(self.HG)

        # Curva da Bomba
        arrPump = dp.smoothGraph(xDataCopy, yDataCopy)
        eq = self.getPumpCurveEquation()
        newX = dp.cutLastPieceGraph(arrPump[0], 5)
        newY = dp.cutLastPieceGraph(arrPump[1], 5)
        plt.plot(newX, newY, '-', label=eq, color='b')

        # Curva do Sistema
        arrSystem = dp.smoothGraph(self.xData, AMT)

        plt.plot(arrSystem[0], arrSystem[1], '-', color='r', label=f'{B}Q² + {C}Q^{d} + {HG}')
        plt.plot(self.xData, AMT, 'o', color='black')

        try:
            x, y = intersection(arrPump[0], arrPump[1], arrSystem[0], arrSystem[1])
            plt.plot(x, y, 'ro', label=f'Interseção [{"{:.4f}".format(x[0])}, {"{:.4f}".format(y[0])}]', color='green')
            plt.annotate('Ponto de operação', xy=(x[0], y[0]), xycoords='data', xytext=(0.8, 0.95),
            textcoords='axes fraction', arrowprops=dict(facecolor='green', shrink=0.05), horizontalalignment='right', verticalalignment='top')

            self.intersect = (x[0], y[0])
            self.updateVazaoAltura(isToSave)
        except:
            pass

        plt.legend(loc='lower right')
        plt.tight_layout()

    def updateVazaoAltura(self, isToSave=False):
        ''' Atualiza o campos de Vazao Bombeada e Altura Nanometrica em Parametros do Sistema. '''

        textRef_0 = self.parent.textBoxesRefs[0]
        textRef_1 = self.parent.textBoxesRefs[1]

        textRef_0.SetValue(str(self.intersect[0]))
        textRef_0.SetOwnBackgroundColour('#cef5d2')
        textRef_0.Refresh()

        textRef_1.SetValue(str(self.intersect[1]))
        textRef_1.SetOwnBackgroundColour('#cef5d2')
        textRef_1.Refresh()

        self.parent.status_bar.SetStatusText('Variáveis Vazão Bombeada e Altura Nanométrica foram atualizadas.')

        if (textRef_0.GetValue != str(self.intersect[0])) or (textRef_1.GetValue != str(self.intersect[0])):
            self.parent.isSaved = False
            self.parent.updateTitleName()

        if not isToSave:
            dlg = wx.MessageDialog(self, 'As variáveis Vazão Bombeada e Altura Nanométrica em Parâmetros do Sistema foram atualizadas com os valores do ponto de interseção.',
            'Informações atualizadas', wx.ICON_INFORMATION)
            dlg.ShowModal()


    def getPumpCurveEquation(self):
        ''' Retorna a string da equacao da bomba do sistema. Retorna uma string vazia em caso de erro. '''

        if '#parameters_pump_start' in gv.fileStartIndices.keys():
            win = PumpWindow(self)
            win.checkAndTransferToLists()
            win.calcultaP2()
            P2 = win.P2
            win.Destroy()

            a = "{:.2f}".format(P2[0])
            b = "{:.2f}".format(P2[1])
            c = "{:.2f}".format(P2[2])
            self.pumpEq = (P2[0], P2[1], P2[2])
            eq = f'f(x) = {a}x² + {b}x + {c}\n'

            return eq

        else:
            return ''