"""
Arquivo responsável pela janela do banco de dados onde contém todos os outros tipos de banco de dados.
Os bancos de dados de Impostos e Rendimentos de Motores Elétricos estão implementados neste próprio arquivo.
database.py
"""

import wx
import wx.richtext as rt
import wx.grid as gridlib
import matplotlib.pyplot as plt
import json
import water_database
import global_variables as gv

class Database(wx.Frame):
    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.SetTitle('Banco de Dados')
        self.CentreOnScreen()

        self.parent = parent
        self.waterWindow = None
        self.taxesWindow = None
        self.rendimentoWindow = None

        self.initUI()

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def initUI(self):
        """ Inicializa a UI. """

        sizer = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(15, wx.FONTFAMILY_ROMAN, wx.DEFAULT, wx.DEFAULT)

        text = wx.StaticText(self, -1, "O banco de dados é um espaço onde você pode conseguir referências e conjuntos de dados para usar nas suas próprias simulações.",
                            style=wx.ALIGN_CENTER, size=(300, 50))

        waterBtn = wx.Button(self, -1, "Consumo de Água", size=(300, 40))
        waterBtn.SetFont(font)
        waterBtn.Bind(wx.EVT_BUTTON, self.OnWater)

        taxesBtn = wx.Button(self, -1, "Impostos", size=(300, 40))
        taxesBtn.SetFont(font)
        taxesBtn.Bind(wx.EVT_BUTTON, self.OnTaxes)

        rendimentoBtn = wx.Button(self, -1, "Rendimentos de Motores Elétricos", size=(300, 40))
        rendimentoBtn.SetFont(font)
        rendimentoBtn.Bind(wx.EVT_BUTTON, self.OnRendimento)

        sizer.Add(text, flag=wx.ALIGN_CENTER | wx.ALL, border=15)
        sizer.Add(waterBtn, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        sizer.Add(taxesBtn, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        sizer.Add(rendimentoBtn, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

        self.SetSizerAndFit(sizer)

    def OnWater(self, event):
        ''' Abre a janela de bando de dados de consumo de água e esconde esta. '''

        if not self.waterWindow:
            self.waterWindow = water_database.WaterDataBase(self)
            self.waterWindow.Show()
            self.Hide()

    def OnTaxes(self, event):
        ''' Abre a janela de impostos e esconde esta. '''

        if not self.taxesWindow:
            self.taxesWindow = Taxes(self)
            self.taxesWindow.Show()
            self.Hide()

    def OnRendimento(self, event):
        ''' Abre a janela de Rendimentos de Motores Elétricos e esconde esta. '''

        if not self.rendimentoWindow:
            self.rendimentoWindow = Rendimento(self)
            self.rendimentoWindow.Show()
            self.Hide()

    def OnCloseWindow(self, event):
        """ Fecha a janela. """

        self.parent.databaseWindow = None
        self.Destroy()


class Taxes(wx.Dialog):
    ''' Classe responsável pela janela de Impostos dentro do banco de dados. '''

    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.SetTitle('Impostos')
        self.SetBackgroundColour(gv.BACKGROUND_COLOR)

        self.parent = parent

        self.getTaxesValues()
        self.initUI()

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.CentreOnParent()

    def getPIS_COFINS_Ctrl(self):
        ''' Cria e inicializa a wx.ListCtrl com as informações do PIS e COFINS e retorna a referência. '''

        listCtrl = wx.ListCtrl(self, -1, size=(324, 166), style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        listCtrl.InsertColumn(0, 'Ano')
        listCtrl.InsertColumn(1, 'PIS (%)')
        listCtrl.InsertColumn(2, 'COFINS (%)')
        listCtrl.InsertColumn(3, 'Total (%)')

        for i in range (0, len(self.PIS_COFINS)):
            dic = self.PIS_COFINS[i]
            listCtrl.InsertItem(i, str(dic['year']))
            listCtrl.SetItem(i, 1, str(dic['values'][0]))
            listCtrl.SetItem(i, 2, str(dic['values'][1]))
            listCtrl.SetItem(i, 3, str(dic['values'][2]))

            if i % 2:
                listCtrl.SetItemBackgroundColour(i, '#d8daed')

        return listCtrl

    def getPIS_COFINS_AVARAGE_Ctrl(self):
        ''' Cria e inicializa a wx.ListCtrl com as informações da média PIS e COFINS e retorna a referência. '''

        listCtrl = wx.ListCtrl(self, -1, size=(325, 260), style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        listCtrl.InsertColumn(0, 'Mês')
        listCtrl.InsertColumn(1, 'PIS (%)')
        listCtrl.InsertColumn(2, 'COFINS (%)')
        listCtrl.InsertColumn(3, 'Total (%)')

        for i in range (0, len(self.PIS_COFINS_AVARAGE)):
            dic = self.PIS_COFINS_AVARAGE[i]
            listCtrl.InsertItem(i, str(dic['month']))
            listCtrl.SetItem(i, 1, str(dic['values'][0]))
            listCtrl.SetItem(i, 2, str(dic['values'][1]))
            listCtrl.SetItem(i, 3, str(dic['values'][2]))

            if i % 2:
                listCtrl.SetItemBackgroundColour(i, '#d8daed')

        return listCtrl

    def getICMS_Ctrl(self):
        ''' Cria e inicializa a wx.ListCtrl com as informações do ICMS e retorna a referência. '''

        listCtrl = wx.ListCtrl(self, -1, size=(210, 525), style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        listCtrl.InsertColumn(0, 'Estado', width=125)
        listCtrl.InsertColumn(1, 'ICMS (%)')

        for i in range (0, len(self.ICMS)):
            dic = self.ICMS[i]
            listCtrl.InsertItem(i, str(dic['state']))
            listCtrl.SetItem(i, 1, str(dic['icms']))

            if i % 2:
                listCtrl.SetItemBackgroundColour(i, '#d8daed')

        return listCtrl

    def initUI(self):
        ''' Inicializa a UI. '''

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(11, wx.FONTFAMILY_ROMAN, wx.DEFAULT, wx.BOLD)

        mediaMsg = wx.StaticText(self, -1, 'Média de impostos por ano: 2015 ~ 2020')
        mediaMsg.SetFont(font)
        leftSizer.Add(mediaMsg, flag=wx.TOP, border=5 )
        leftSizer.Add(self.getPIS_COFINS_Ctrl(), flag=wx.TOP, border=5 )

        mediaMsg = wx.StaticText(self, -1, 'Média dos impostos por mês: 2015 ~ 2020')
        mediaMsg.SetFont(font)
        leftSizer.Add(mediaMsg, flag=wx.TOP, border=25 )
        leftSizer.Add(self.getPIS_COFINS_AVARAGE_Ctrl(), flag=wx.TOP, border=5 )

        ref = rt.RichTextCtrl(self, -1, size=(110, 46), style=wx.TE_READONLY)
        ref.WriteText('Fontes:\n')
        ref.AppendText("EDP. Tabela de Cálculo PIS/PASEP COFINS. Disponível em: https://www.edp.com.br/distribuicao-sp/saiba-mais/informativos/tabela-de-calculo-pispasep-cofins. Acesso em: 24 jun. 2021.\n")
        ref.AppendText("NUBANK. O que é ICMS? Quem paga e quem é isento desse tributo? Disponível em: https://blog.nubank.com.br/o-que-e-icms/. Acesso em: 24 jun. 2021.")
        leftSizer.Add(ref, flag=wx.TOP | wx.EXPAND, border=5)

        mediaMsg = wx.StaticText(self, -1, 'Ano de referência: 2019')
        mediaMsg.SetFont(font)
        rightSizer.Add(mediaMsg, flag=wx.TOP, border=5 )
        rightSizer.Add(self.getICMS_Ctrl(), flag=wx.TOP, border=5 )

        sizer.Add(leftSizer, flag=wx.ALL, border=10)
        sizer.Add(rightSizer, flag=wx.ALL, border=10)

        self.SetSizerAndFit(sizer)

    def getTaxesValues(self):
        ''' Inicializa as listas com os valores dos impostos. '''

        with open('files/pis_cofins.json', 'r', encoding='utf-8') as f:
            self.PIS_COFINS = json.load(f)

        with open('files/pis_cofins_avarage.json', 'r', encoding='utf-8') as f:
            self.PIS_COFINS_AVARAGE = json.load(f)

        with open('files/icms.json', 'r', encoding='utf-8') as f:
            self.ICMS = json.load(f)

    def OnCloseWindow(self, event):
        """ Fecha a janela. """

        self.parent.Show()
        self.parent.taxesWindow = None

        self.Destroy()


class Rendimento(wx.Dialog):
    ''' Classe responsável pela janela "Rendimento de Motores Elétricos" do bando de dados. '''

    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.SetTitle('Rendimentos de Motores Elétricos')
        self.SetBackgroundColour(gv.BACKGROUND_COLOR)

        self.parent = parent
        self.currentlySelectedCell = (0, 0)

        self.SetSize((915, 600))
        self.loadFile()
        self.initUI()

        self.grid.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onRowSelected)
        self.grid.Bind(wx.EVT_KEY_DOWN, self.OnKey)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.CentreOnParent()

    def initUI(self):
        ''' Inicializa a UI.'''

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer = wx.BoxSizer(wx.VERTICAL)

        leftSizer.Add(self.createColorsLegend())
        leftSizer.Add(self.initButtonsSizer(), flag=wx.TOP | wx.EXPAND, border=15)
        rightSizer.Add(self.createTable())
        self.printAjustePolos(2)

        sizer.Add(leftSizer, flag=wx.ALL, border=5)
        sizer.Add(rightSizer, flag=wx.ALL, border=5)
        self.SetSizer(sizer)

    def loadFile(self):
        ''' Carrega os arquivos. '''

        with open('files/rendimento.json', 'r') as f:
            self.RENDIMENTOS = json.load(f)

    def createTable(self):
        ''' Cria a tabela e a retorna (self.gridlib.Grid). '''

        # Criando a tabela... (350, 762)
        self.grid = gridlib.Grid(self, -1, size=(650, 550))
        self.grid.CreateGrid(40, 7)
        self.grid.SetColLabelSize(0)
        self.grid.SetRowLabelSize(30)
        self.grid.SetColSize(5, 100)
        self.grid.SetColSize(6, 100)
        self.grid.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        for i in range(0, 40):
            for j in range(0, self.grid.GetNumberRows()):
                self.grid.SetReadOnly(i, j)

        self.grid.SetCellSize(0, 0, 1, 4)
        self.grid.SetCellSize(1, 0, 1, 4)
        self.grid.SetCellValue(0, 0, 'Portaria Interministerial Número 1 - 29 de junho de 2017')
        self.grid.SetCellValue(1, 0, 'Rotor Gaiola de Esquilo')

        self.grid.SetCellSize(2, 0, 1, 2)
        self.grid.SetCellSize(2, 2, 1, 2)
        self.grid.SetCellValue(2, 0, 'Potência nominal')
        self.grid.SetCellValue(2, 2, 'Velocidade síncrona (rpm)')

        self.grid.SetCellSize(3, 0, 2, 1)
        self.grid.SetCellSize(3, 1, 2, 1)

        self.grid.SetCellValue(3, 2, '3.600')
        self.grid.SetCellValue(3, 3, '1.800')
        self.grid.SetCellValue(4, 2, '2 Polos')
        self.grid.SetCellValue(4, 3, '4 Polos')

        self.grid.SetCellValue(5, 0, 'kW')
        self.grid.SetCellValue(5, 1, 'cv')

        self.grid.SetCellSize(5, 2, 1, 2)
        self.grid.SetCellValue(5, 2, 'Rendimento Nominal')

        self.grid.SetCellBackgroundColour(11, 3, '#faec82')
        self.grid.SetCellBackgroundColour(12, 3, '#97f7a2')
        self.grid.SetCellBackgroundColour(14, 3, '#97dcf7')
        self.grid.SetCellBackgroundColour(18, 3, '#f5ab76')

        self.grid.SetCellSize(0, 5, 1, 2)
        self.grid.SetCellValue(0, 5, 'Ajuste Portaria - 2 Polos')
        self.grid.SetCellValue(1, 5, 'Potência (kW)')
        self.grid.SetCellValue(1, 6, 'Rendimento (%)')

        # A formatação dos dados em texto está concluída. Agora, começa a impressão
        # dos dados do arquivo, partir da fileira 6.

        start = 6   # Precisamos subtrair o offset de onde as celúlas começarão a ser escritas no grid.
        for i in range(start, len(self.RENDIMENTOS) + start):
            dic = self.RENDIMENTOS[i - start]
            for j in range(0, 4):
                if j == 0:
                    self.grid.SetCellValue(i, j, str(dic['kW']))
                elif j == 1:
                    self.grid.SetCellValue(i, j, str(dic['cv']))
                elif j == 2:
                    self.grid.SetCellValue(i, j, str(dic['2polos']))
                elif j == 3:
                    self.grid.SetCellValue(i, j, str(dic['4polos']))

        return self.grid

    def printAjustePolos(self, polo):
        ''' Atualiza a segunda tabela no self.grid com o ajuste de @`polo` polos. '''

        if not polo == 2 and not polo == 4:
            return

        self.grid.SetCellValue(0, 5, f'Ajuste Portaria - {polo} Polos')

        if polo == 2:
            key = '2polos'
        else:
            key = '4polos'

        start = 2   # Precisamos subtrair o offset de onde as celúlas começarão a ser escritas no grid.
        for i in range(start, len(self.RENDIMENTOS) + start):
            dic = self.RENDIMENTOS[i - start]
            for j in range(5, 7):
                if j == 5:
                    self.grid.SetCellValue(i, j, f"{dic['kW']}")
                else:
                    self.grid.SetCellValue(i, j, f"{dic[key]}")

    def createColorsLegend(self):
        ''' Cria o sizer com as legendas das cores. '''

        sizer = wx.BoxSizer(wx.VERTICAL)

        yellowPanel = wx.Panel(self, -1, size=(20, 20))
        yellowPanel.SetBackgroundColour('#faec82')

        greenPanel = wx.Panel(self, -1, size=(20, 20))
        greenPanel.SetBackgroundColour('#97f7a2')

        bluePanel = wx.Panel(self, -1, size=(20, 20))
        bluePanel.SetBackgroundColour('#97dcf7')

        orangePanel = wx.Panel(self, -1, size=(20, 20))
        orangePanel.SetBackgroundColour('#f5ab76')

        yellowBox = wx.BoxSizer(wx.HORIZONTAL)
        yellowBox.Add(yellowPanel, flag=wx.ALL, border=5)
        yellowBox.Add( wx.StaticText(self, -1, 'Para motores na carcaça 80, o valor mínimo de rendimento é 83%.', size=(200, 46)))

        greenBox = wx.BoxSizer(wx.HORIZONTAL)
        greenBox.Add(greenPanel, flag=wx.ALL, border=5)
        greenBox.Add( wx.StaticText(self, -1, 'Para motores na carcaça 80, o valor mínimo de rendimento é 84%.', size=(200, 46)))

        blueBox = wx.BoxSizer(wx.HORIZONTAL)
        blueBox.Add(bluePanel, flag=wx.ALL, border=5)
        blueBox.Add( wx.StaticText(self, -1, 'Para motores na carcaça 90, o valor mínimo de rendimento é 87.5%.', size=(200, 46)))

        orangeBox = wx.BoxSizer(wx.HORIZONTAL)
        orangeBox.Add(orangePanel, flag=wx.ALL, border=5)
        orangeBox.Add( wx.StaticText(self, -1, 'Para motores na carcaça 112, o valor mínimo de rendimento é 91%.', size=(200, 46)))

        sizer.Add(yellowBox, flag=wx.TOP, border=5)
        sizer.Add(greenBox)
        sizer.Add(blueBox)
        sizer.Add(orangeBox)

        return sizer

    def initButtonsSizer(self):
        ''' Cria o sizer que contém dados e widgets pro usuário desenhar um gráfico de ajuste. '''

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.ctrlsList = []

        hBox = wx.StaticBoxSizer(wx.VERTICAL, self)
        update2Btn = wx.Button(self, 1002, 'Atualizar 2 Polos')
        update2Btn.Bind(wx.EVT_BUTTON, self.OnUpdatePolo)
        hBox.Add(update2Btn, flag=wx.ALL | wx.EXPAND, border=10)

        plot2Btn = wx.Button(self, 1002, 'Desenhar gráfico')
        plot2Btn.Bind(wx.EVT_BUTTON, self.OnDraw)
        hBox.Add(plot2Btn, flag=wx.ALL | wx.EXPAND, border=10)
        sizer.Add(hBox, flag=wx.ALL | wx.EXPAND | wx.EXPAND, border=25)

        hBox = wx.StaticBoxSizer(wx.VERTICAL, self)
        update4Btn = wx.Button(self, 1004, 'Atualizar 4 Polos')
        update4Btn.Bind(wx.EVT_BUTTON, self.OnUpdatePolo)
        hBox.Add(update4Btn, flag=wx.ALL | wx.EXPAND, border=10)

        plot4Btn = wx.Button(self, 1004, 'Desenhar gráfico')
        plot4Btn.Bind(wx.EVT_BUTTON, self.OnDraw)
        hBox.Add(plot4Btn, flag=wx.ALL | wx.EXPAND, border=10)
        sizer.Add(hBox, flag=wx.ALL | wx.EXPAND | wx.EXPAND, border=25)

        return sizer

    def OnUpdatePolo(self, event):
        ''' Atualiza as informações do Ajuste de polos na tabela. '''

        ID = event.GetEventObject().Id
        ID -= 1000

        self.printAjustePolos(ID)

    def OnDraw(self, event):
        ''' Chamada quando o usuário clica para desenhar algum gráfico. '''

        ID = event.GetEventObject().Id
        ID -= 1000

        if ID == 2:
            key = '2polos'
        else:
            key = '4polos'

        fig, ax = plt.subplots(figsize=(11, 6))

        # Informacoes do grafico.
        ax.set_xlabel('Potência do Motor (kW)')
        ax.set_ylabel('Rendimento Nominal (%)')

        plt.suptitle(f'{ID} Polos', x=0.07, y=0.98, ha='left', fontsize=15)

        # remove spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # estiliza o grid
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='gray', linestyle='dashed', alpha=0.2)
        ax.xaxis.grid(color='gray', linestyle='dashed', alpha=0.2)

        x, y = [], []
        data = self.RENDIMENTOS
        for index in range(0, len(data)):
            x.append(float(data[index]['kW']))
            y.append(float(data[index][key]))

        plt.plot(x, self.getRendimento(ID, x), label=f"{self.getEquation(ID)}")
        plt.plot(x, y, 'o', label='Ponto [kW, Rendimento]')

        ax.legend(loc='lower right')
        plt.tight_layout()
        plt.show()

    def getEquation(self, polo):
        ''' Retorna a equação (str) da equação do ajuste @`polo`. '''

        if polo == 2:
            return "86.63 * 0.95 ^ (1 / kW) * kW ^ 0.01"
        else:
            return "(-39.21 * 0.10 + 96.88 * kW ^ 0.50) / (0.10 + kW ^ 0.50)"

    def getRendimento(self, polo, x):
        ''' Retorna uma lista contento os pontos `y`, dado a entrada (lista) `x`, que não é modificada. '''

        y = []
        if polo == 2:
            for kW in x:
                y.append(86.6318 * pow(0.9589, (1 / kW)) * pow(kW, 0.0191))
        else:
            for kW in x:
                y.append((-39.2162 * 0.1012 + 96.8826 * pow(kW, 0.5087)) / (0.1012 + pow(kW, 0.5087)))

        return y

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

    def onCellEdit(self, event):
        ''' Chamada quando uma célula é editada. '''

        editor = event.GetControl()
        editor.Bind(wx.EVT_KEY_DOWN, self.onEditorKey)

        event.Skip()

    def onRowSelected(self, event):
        ''' Chamada quando o usuário mudar de célula. '''

        self.currentlySelectedCell = (event.GetRow(), event.GetCol())

    def OnKey(self, event):
        ''' Chamada quando o usuário apertar qualquer tecla. Só reage a Ctrl + C. '''

        # Se Ctrl + C
        if event.ControlDown() and event.GetKeyCode() == 67:
            self.onGetSelection(None)

        event.Skip()

    def OnCloseWindow(self, event):
        ''' Função chamada quando o usuario clica no botao de fechar no canto superior direito. '''

        self.parent.Show()
        self.parent.rendimentoWindow = None

        self.Destroy()