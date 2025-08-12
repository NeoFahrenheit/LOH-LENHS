'''
Classe responsável pela base de dados de consumo de água que pode ser usada pelo usuário como referência.
water_database.py
'''

import wx
import wx.richtext as rt
import wx.lib.scrolledpanel as scrolled
import json
import matplotlib.pyplot as plt
import unidecode
import app.data_processing as dp
import app.global_variables as gv

class WaterDataBase(wx.Frame):
    ''' Classe responsável pelo banco de dados do consumo de água. '''

    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.parent = parent

        self.SetTitle('Consumo de Água - Banco de Dados')
        self.SetBackgroundColour(gv.BACKGROUND_COLOR)

        self.waterData = []
        self.checkBoxRefs = []
        self.buttonRefs = []
        self.sizerRefs = []
        self.currentlyShown = []

        self.copyWindow = None

        self.setupSizers()
        self.LoadWaterData()

        self.updateWaterInfoSizer(0)
        self.setIndicadoresVariables(0)
        self.updateIndicadoresVariablesToSizer(0)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Layout()
        self.CenterOnScreen()

    def setupSizers(self):
        ''' Inicializa os sizers. '''

        masterSizer = wx.BoxSizer(wx.HORIZONTAL)
        itemsSizer = wx.BoxSizer(wx.VERTICAL)

        self.waterInfoSizer = wx.StaticBoxSizer(wx.VERTICAL, self)
        self.waterInfoSizer.SetMinSize(250, 625)
        self.initWaterInfoSizer()

        self.summarySizer = wx.StaticBoxSizer(wx.VERTICAL, self)
        self.initSummarySizer()

        self.scrolledPanelSizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolled_panel = scrolled.ScrolledPanel(self, wx.ID_ANY, style=wx.SUNKEN_BORDER, size=(308, 580))
        self.scrolled_panel.SetSizer(self.scrolledPanelSizer)
        self.scrolled_panel.SetOwnBackgroundColour('#ededed')
        self.scrolled_panel.SetupScrolling()

        itemsSizer.Add(self.addSearchControls(), flag=wx.ALL, border=7)
        itemsSizer.Add(self.scrolled_panel, flag=wx.ALL, border=7)

        masterSizer.Add(itemsSizer, flag=wx.ALL, border=5)
        masterSizer.Add(self.waterInfoSizer, flag=wx.ALL, border=5)
        masterSizer.Add(self.summarySizer, flag=wx.ALL, border=5)

        self.SetSizerAndFit(masterSizer)

    def initWaterInfoSizer(self):
        ''' Inicializa os widgets dentro do sizer `self.waterInfoSizer`. '''

        self.waterInfoTitle = wx.StaticText(self, -1, 'title', style=wx.ALIGN_CENTER)
        self.waterInfoTitle.SetFont( wx.Font(12, wx.FONTFAMILY_ROMAN, wx.DEFAULT, wx.BOLD) )
        self.waterInfoSizer.Add(self.waterInfoTitle, flag=wx.EXPAND)
        self.waterListCtrl = wx.ListCtrl(self, -1, size=(165, 485), style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.waterListCtrl.InsertColumn(0, 'Horário')
        self.waterListCtrl.InsertColumn(1, 'Consumo')

        for i in range(0, 24):
            self.waterListCtrl.InsertItem(i, '')
            self.waterListCtrl.SetItem(i, 1, '')

            if i % 2:
                self.waterListCtrl.SetItemBackgroundColour(i, '#d8daed')

        self.waterInfoSizer.Add(self.waterListCtrl, flag=wx.TOP | wx.ALIGN_CENTER, border=5)

        self.addTableBtn = wx.Button(self, -1, 'Copiar', size=(116, 23))
        self.addTableBtn.SetToolTip('Copiar dados de consumo para a área de transferência')
        self.addTableBtn.Bind(wx.EVT_BUTTON, self.OnCopy)
        self.waterInfoSizer.Add(self.addTableBtn, flag=wx.ALIGN_CENTER | wx.TOP, border=12)

        self.plotGraphsBtn = wx.Button(self, -1, 'Desenhar Gráficos', size=(116, 23))
        self.plotGraphsBtn.SetToolTip('Desenha os gráficos selecionados')
        self.plotGraphsBtn.Bind(wx.EVT_BUTTON, self.OnPlot)
        self.waterInfoSizer.Add(self.plotGraphsBtn, flag=wx.ALIGN_CENTER | wx.TOP, border=12)

    def updateWaterInfoSizer(self, index):
        ''' Atualiza os widgets dentro do sizer self.waterInfoSizer. '''

        values = self.waterData[index]['data'].split(',')
        values = [float(x) for x in values]
        time = [0, 0]
        data = []

        for value in values:
            data.append((dp.addMinutes(time, 60), value))

        self.waterInfoTitle.SetLabel(f"{self.waterData[index]['name']}\n")

        for i in range(0, len(data)):
            t = data[i]
            self.waterListCtrl.SetItem(i, 0, f"{t[0]}")
            self.waterListCtrl.SetItem(i, 1, f"{t[1]:.4f}")

        self.addTableBtn.SetId(1000 + index)
        self.waterInfoSizer.Layout()

    def initSummarySizer(self):
        ''' Inicializa o sizer `self.summarySizer`. '''

        self.dataDescriptionText = rt.RichTextCtrl(self, -1, 'Apenas um teste. A descrição do reservatório ficará aqui.', style=wx.TE_READONLY)
        self.dataDescriptionText.SetMinSize((285, 268))
        self.dataDescriptionText.SetOwnBackgroundColour('#ededed')
        self.summarySizer.Add(self.dataDescriptionText, flag=wx.ALL, border=5)

        self.summaryListCtrl = wx.ListCtrl(self, -1, size=(285, 320), style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.summaryListCtrl.SetMaxSize((285, 320))
        self.summaryListCtrl.InsertColumn(0, 'Indicador', width=200)
        self.summaryListCtrl.InsertColumn(1, 'Valor')

        self.summaryListCtrl.InsertItem(0, 'Média')
        self.summaryListCtrl.InsertItem(1, 'Máximo')
        self.summaryListCtrl.InsertItem(2, 'K2')
        self.summaryListCtrl.InsertItem(3, 'FD')
        self.summaryListCtrl.InsertItem(4, 'Volume Ponta')
        self.summaryListCtrl.InsertItem(5, 'Volume Ponta/Volume Total')
        self.summaryListCtrl.InsertItem(6, 'Tempo consumo ABM')
        self.summaryListCtrl.InsertItem(7, 'Tempo consumo ACM')
        self.summaryListCtrl.InsertItem(8, 'Volume Fora Ponta')
        self.summaryListCtrl.InsertItem(9, 'Volume Fora Ponta/Volume Total')
        self.summaryListCtrl.InsertItem(10, 'Volume Ponta/Volume Fora Ponta')
        self.summaryListCtrl.InsertItem(11, 'Consumo ABM')
        self.summaryListCtrl.InsertItem(12, 'Consumo ABM/Consumo Total')
        self.summaryListCtrl.InsertItem(13, 'Consumo ACM')
        self.summaryListCtrl.InsertItem(14, 'Consumo ACM/Consumo Total')

        for i in range(0, 15):
            if i % 2:
                self.summaryListCtrl.SetItemBackgroundColour(i, '#d8daed')

        self.summarySizer.Add(self.summaryListCtrl, flag=wx.ALL, border=5)

    def LoadWaterData(self):
        ''' Carrega o arquivo database.txt para `self.waterData`. '''

        with open('assets/files/water_database.json', 'r', encoding='utf-8') as f:
            text = f.read()
            self.waterData = json.loads(text)

        for dic in self.waterData:
            self.setWaterSizer(dic['index'])

        self.scrolled_panel.Layout()

    def createWaterPanel(self, index):
        ''' Cria um wx.BoxSizer(wx.HORIZONTAL) contendo uma wx.CheckBox e um wx.StaticText com o nome do reservatório. '''

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        checkBox = wx.CheckBox(self.scrolled_panel, 1000 + index)
        checkBox.Bind(wx.EVT_CHECKBOX, self.OnChecked)
        self.checkBoxRefs.append(checkBox)

        button = wx.Button(self.scrolled_panel, 1000 + index, self.waterData[index]['name'], size=(250, 22))
        button.Bind(wx.EVT_BUTTON, self.OnButton)
        self.buttonRefs.append(button)

        sizer.Add(checkBox, flag=wx.TOP, border=3)
        sizer.Add(button, flag=wx.LEFT, border=5)
        self.sizerRefs.append(sizer)
        self.currentlyShown.append(index)

        return sizer

    def addSearchControls(self):
        ''' Adiciona o sizer responsável pela checkBox de selecionar tudo, campo e filtro de pesquisa. Retorna o BoxSizer. '''

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.checkAll = wx.CheckBox(self, -1)
        self.checkAll.SetToolTip(wx.ToolTip('Selecionar todas'))
        self.checkAll.Bind(wx.EVT_CHECKBOX, self.OnCheckAll)

        searchText = wx.StaticText(self, -1, 'pesquisar:')
        self.searchField = wx.TextCtrl(self, -1)
        self.searchField.Bind(wx.EVT_TEXT, self.OnSearched)

        choices = ['todas', 'norte', 'nordeste', 'centro-oeste', 'sudeste', 'sul', 'exterior']
        self.filterCombo = wx.ComboBox(self, -1, 'todas', choices=choices, style=wx.CB_READONLY)
        self.filterCombo.Bind(wx.EVT_COMBOBOX, self.OnSearched)

        sizer.Add(self.checkAll, flag=wx.TOP | wx.LEFT | wx.RIGHT, border=6)
        sizer.Add(searchText, flag=wx.TOP | wx.LEFT, border=4)
        sizer.Add(self.searchField, flag=wx.LEFT, border=5)
        sizer.Add(self.filterCombo, flag=wx.LEFT, border=16)

        return sizer

    def getWaterItemByName(self, search):
        ''' Retorna uma lista contendo dicionários com as informações de um reservatório.
        Se `search` estiver vazio, todos os reservatórios são retornados na lista. Caso, contrário,
        são retornados aqueles que correspondem a `search`. A procura é feita no nome dos reservatórios. É esperado
        que tenha sido usado em `search` lower() e unidecode.unidecode().
        Exemplo: {'isSelected': False, 'name': 'Campus do Vale', 'region': 'sul', 'data': '0.27, 0.25, ...' } '''

        infos = []

        for line in self.waterData:
            if unidecode.unidecode(line['name'].lower()).find(search) != -1:
                infos.append(line)

        return infos

    def getWaterItemByRegion(self, region):
        ''' Retorna uma lista contendo dicionários com as informações de um reservatório.
        Se `region` for 'todas', todos os reservatórios (frames) são retornados na lista. Caso, contrário,
        são retornados aqueles que correspondem a `region`. A procura é feita no nome das regiões.
        Exemplo: {'isSelected': False, 'name': 'Campus do Vale', 'region': 'sul', 'data': '0.27, 0.25, ...' } '''

        infos = []

        if region == 'todas':
            return self.waterData[:]
        else:
            for line in self.waterData:
                if line['region'] == region:
                    infos.append(line)

        return infos

    def setWaterSizer(self, index):
        ''' Adiciona um wx.BoxSizer(wx.HORIZONTAL), contendo a estrutura de dado de um reservatório em `index`, na lista de pesquisa. '''

        sizer = self.createWaterPanel(index)
        self.scrolledPanelSizer.Add(sizer, flag=wx.ALL, border=5)

    def OnSearched(self, event):
        ''' Chamada quando o usuário digitar qualquer coisa no campo de pesquisa ou mudar a opção do filtro.
        Adiciona / remove os itens na scrolledPanel. '''

        # Para a pesquisar funcionar, precisamos colocar tudo em minúsculo e tirar os acentos.
        query = self.searchField.GetValue().lower()
        query = unidecode.unidecode(query)
        region_query = self.filterCombo.GetValue()

        search = self.getWaterItemByName(query)
        result = []

        for item in search:
            if region_query == 'todas':
                result.append(item['index'])
            elif region_query == item['region']:
                result.append(item['index'])

        # Destruímos todos os sizers dentro do scrolledPanel para adicionar apenas os que precisamos.
        self.currentlyShown.clear()
        for index in result:
            self.sizerRefs[index].ShowItems(True)
            self.currentlyShown.append(index)

        self.hideSizers(self.currentlyShown)
        self.SendSizeEvent()
        self.scrolled_panel.Scroll(0, 0)

    def hideSizers(self, sizers):
        ''' Esconde todos os `self.sizerRefs` que não estiverem na lista de indexes `sizers`. '''

        size = len(self.waterData)
        for i in range(0, size):
            if i not in sizers:
                self.sizerRefs[i].ShowItems(False)

    def getSelected(self):
        ''' Retorna uma lista com todos os indexes dos dados que foram selecionados. '''

        toPlot = []
        for i in range(0, len(self.waterData)):
            if self.waterData[i]['isSelected']:
                toPlot.append(i)

        return toPlot

    def OnPlot(self, event):
        ''' Desenha todos os gráficos selecionados. '''

        toPlot = self.getSelected()
        if len(toPlot) < 1:
            dlg = wx.MessageDialog(self, 'Por favor, selecione ao menos um local.', 'Seleção insuficiente', wx.ICON_ERROR)
            dlg.ShowModal()
            return

        fig, ax = plt.subplots(figsize=(11, 6))

        # Informacoes do grafico.
        ax.set_xlabel('Hora')
        ax.set_ylabel('Q/Qmédia')
        ax.xaxis.set_tick_params(rotation=30, labelsize=10)

        plt.suptitle('Gráficos de Consumo', x=0.07, y=0.98, ha='left', fontsize=15)

        # remove spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # estiliza o grid
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='gray', linestyle='dashed', alpha=0.2)
        ax.xaxis.grid(color='gray', linestyle='dashed', alpha=0.2)

        for index in toPlot:
            time = [0, 0]
            y = self.waterData[index]['data'].split(',')
            y = [float(value) for value in y]
            x = [dp.addMinutes(time, 60) for _ in y]

            plt.plot(x, y, label=f"{self.waterData[index]['name']}")

        ax.legend(loc='best')
        plt.tight_layout()
        plt.show()

    def OnChecked(self, event):
        ''' Chamada quando houver um clique na checkBox da água. '''

        ID = event.GetEventObject().Id
        ID -= 1000

        value = self.checkBoxRefs[ID].GetValue()
        self.waterData[ID]['isSelected'] = value

    def OnCheckAll(self, event):
        ''' Chamada quando houver um clique na checkBox de selecionar todas. '''

        # Se o clique marcou a checkBox...
        if self.checkAll.GetValue():
            for index in self.currentlyShown:
                self.waterData[index]['isSelected'] = True
                self.checkBoxRefs[index].SetValue(True)
        else:
            for i in range(0, len(self.waterData)):
                self.waterData[i]['isSelected'] = False
                self.checkBoxRefs[i].SetValue(False)

    def OnButton(self, event):
        ''' Chamada quando houver um clique em algum botão na lista de pesquisa. '''

        ID = event.GetEventObject().Id
        ID -= 1000

        self.updateWaterInfoSizer(ID)
        self.setIndicadoresVariables(ID)
        self.updateIndicadoresVariablesToSizer(ID)

    def OnCopy(self, event):
        ''' Chamada quando o botao de `Enviar para tabela` for clicado. '''

        ID = event.GetEventObject().Id
        ID -= 1000

        data = []
        for value in self.waterData[ID]['data'].split(','):
            data.append(float(value.strip()))

        if not self.copyWindow:
            self.copyWindow = ConversionWindow(self, data)
            self.copyWindow.Show()


    def OnCloseWindow(self, event):
        ''' Função chamada quando o usuario clica no botao de fechar no canto superior direito. '''

        self.parent.Show()

        self.parent.waterWindow = None
        self.Destroy()


    #### ----------------------------------------------------- ####
    #### Inicialização das variáveis de exibição e de cálculo. ####
    #### ----------------------------------------------------- ####

    def setVolumeTotal(self, index):
        ''' Inicializa a variável `self.volumeTotal` e `self.max`. '''

        values = self.waterData[index]['data'].split(',')
        self.yValues = [float(x) for x in values]
        self.max = max(self.yValues)
        self.volumeTotal = sum(self.yValues)

    def setMedia(self):
        ''' Inicializa a variável `self.media`. '''

        self.media = self.volumeTotal / 24

    def setK2(self):
        ''' Inicializa a variável `self.K2`.  '''

        self.K2 = self.max / self.media

    def setFD(self):
        ''' Inicializa a variável `self.FD`.  '''

        self.FD = 1 / self.K2

    def setVolumePonta(self):
        ''' Inicializa a variável `self.volumePonta`.  '''

        self.volumePonta = sum(self.yValues[18:21])

    def setVolumePonta_Total(self):
        ''' Inicializa a variável `self.VolumePonta_Total`.  '''

        self.volumePonta_Total = self.volumePonta / self.volumeTotal

    def setTempoConsumoABM(self):
        ''' Inicializa a variável `self.tempoConsumoABM`.  '''

        self.tempoConsumoABM = 0
        for value in self.yValues:
            if value < self.media:
                self.tempoConsumoABM += 1

    def setTempoConsumoACM(self):
        ''' Inicializa a variável `self.tempoConsumoACM`.  '''

        self.tempoConsumoACM = 24 - self.tempoConsumoABM

    def setVolumeForaPonta(self):
        ''' Inicializa a variável `self.volumeForaPonta`.  '''

        self.volumeForaPonta = self.volumeTotal - self.volumePonta

    def setVolumeForaPonta_Total(self):
        ''' Inicializa a variável `self.volumeForaPonta_Total`.  '''

        self.volumeForaPonta_Total = self.volumeForaPonta / self.volumeTotal

    def setVolumePonta_ForaPonta(self):
        ''' Inicializa a variável `self.volumePonta_ForaPonta`.  '''

        self.volumePonta_ForaPonta = self.volumePonta / self.volumeForaPonta

    def setConsumoABM(self):
        ''' Inicializa a variável `self.consumoABM`. '''

        self.consumoABM = 0
        for value in self.yValues:
            if value < self.media:
                self.consumoABM += value

    def setConsumoABM_ConsumoTotal(self):
        ''' Inicializa a variável `self.consumoABM_ConsumoTotal`.  '''

        self.consumoABM_ConsumoTotal = self.consumoABM / self.volumeTotal

    def setConsumoACM(self):
        ''' Inicializa a variável `self.consumoACM`.  '''

        self.consumoACM = 0

        for value in self.yValues:
            if value > self.media:
                self.consumoACM += value

    def setConsumoACM_Total(self):
        ''' Inicializa a variável `self.consumoACM_Total`.  '''

        self.consumoACM_Total = self.consumoACM / self.volumeTotal

    def setIndicadoresVariables(self, index):
        ''' Inicializa as variáves dos indicadores. '''

        self.setVolumeTotal(index)
        self.setMedia()
        self.setK2()
        self.setFD()
        self.setVolumePonta()
        self.setVolumePonta_Total()
        self.setTempoConsumoABM()
        self.setTempoConsumoACM()
        self.setVolumeForaPonta()
        self.setVolumeForaPonta_Total()
        self.setVolumePonta_ForaPonta()
        self.setConsumoABM()
        self.setConsumoABM_ConsumoTotal()
        self.setConsumoACM()
        self.setConsumoACM_Total()

        self.dataDescriptionText.Clear()
        self.dataDescriptionText.WriteText(self.waterData[index]['info'])

    def updateIndicadoresVariablesToSizer(self, index):
        ''' Atualiza o texto dos resultados dos indicadores. '''

        self.summaryListCtrl.SetItem(0, 1, f'{self.media:.2f}')
        self.summaryListCtrl.SetItem(1, 1, f'{self.max:.2f}')
        self.summaryListCtrl.SetItem(2, 1, f'{self.K2:.2f}')
        self.summaryListCtrl.SetItem(3, 1, f'{self.FD:.2f}')
        self.summaryListCtrl.SetItem(4, 1, f'{self.volumePonta:.2f}')
        self.summaryListCtrl.SetItem(5, 1, f'{self.volumePonta_Total:.2f}')
        self.summaryListCtrl.SetItem(6, 1, f'{self.tempoConsumoABM:.2f}')
        self.summaryListCtrl.SetItem(7, 1, f'{self.tempoConsumoACM:.2f}')
        self.summaryListCtrl.SetItem(8, 1, f'{self.volumeForaPonta:.2f}')
        self.summaryListCtrl.SetItem(9, 1, f'{self.volumeForaPonta_Total:.2f}')
        self.summaryListCtrl.SetItem(10, 1, f'{self.volumePonta_ForaPonta:.2f}')
        self.summaryListCtrl.SetItem(11, 1, f'{self.consumoABM:.2f}')
        self.summaryListCtrl.SetItem(12, 1, f'{self.consumoABM_ConsumoTotal:.2f}')
        self.summaryListCtrl.SetItem(13, 1, f'{self.consumoACM:.2f}')
        self.summaryListCtrl.SetItem(14, 1, f'{self.consumoACM_Total:.2f}')


class ConversionWindow(wx.Frame):
    """ Classe responsável pela janela que vai perguntar ao usuário o fator de conversão da tabela de consumo. """

    def __init__(self, parent, data):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, style=style)

        self.CenterOnScreen()
        self.SetTitle('Converter e copiar')

        self.parent = parent
        self.data = data
        self.setupUI()

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def setupUI(self):
        ''' Inicializa os sizers e os widgets da interface. '''

        sizer = wx.BoxSizer(wx.VERTICAL)
        message = wx.StaticText(self, -1, 'Entre com o fator de conversão (vazão média de consumo)\ndos dados da tabela de consumo:')
        self.text = wx.TextCtrl(self, -1, style=wx.TE_PROCESS_ENTER)
        btn = wx.Button(self, -1, 'Converter e copiar')
        btn.SetToolTip('Converte todos os dados de consumo pelo fator e copia para a área de transferência.')

        btn.Bind(wx.EVT_BUTTON, self.OnButton)
        self.text.Bind(wx.EVT_TEXT_ENTER, self.OnButton)

        sizer.Add(message, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        sizer.Add(self.text, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        sizer.Add(btn, flag=wx.ALIGN_CENTER | wx.ALL, border=5)

        self.SetSizerAndFit(sizer)

    def OnButton(self, event):
        ''' Chamada quando o usuário clicar no botão de converter. '''

        fator = self.text.GetValue()

        if not dp.isFloat(fator) or float(fator) <= 0:
            self.text.SetOwnBackgroundColour('#ff8f8f')
            self.text.Refresh()
            return

        data = wx.TextDataObject()
        temp = ''
        for value in self.data:
            temp += f"{value * float(fator)}\n"

        data.SetText(temp)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

            self.OnCloseWindow(None)

    def OnCloseWindow(self, event):
        ''' Função chamada quando o usuario clica no botao de fechar no canto superior direito. '''

        self.Destroy()
        self.parent.copyWindow = None