"""
Arquivos contem as funcoes necessarias para desenhar um gráfico.
graph_drawing.py
"""

import wx
import wx.lib.scrolledpanel as scrolled
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import app.data_processing as dp

class GraphCalendar(wx.Panel):
    def __init__(self, parent, data):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        wx.Panel.__init__(self, parent, style=style)

        self.SetBackgroundColour('#e3e3e8')
        self.isSaveToDisk = False
        self.path = ''

        self.data = data
        self.consumption = []
        self.index = -1
        self.value = 0
        self.k2 = 0
        self.fd = 0

        self.summaryBtn = wx.Button(self, wx.ID_ANY, 'Gráfico Geral de Consumo')
        self.summaryBtn.Bind(wx.EVT_BUTTON, self.OnSummary)

        self.text = wx.StaticText(self, wx.ID_ANY)
        self.scrollPanel = scrolled.ScrolledPanel(self, wx.ID_ANY, size=((290, 435)), style=wx.SUNKEN_BORDER)
        self.scrollPanel.ShowScrollbars(False, True)
        self.scrollPanel.SetupScrolling()

        self.topVerticalBox = wx.BoxSizer(wx.VERTICAL)
        self.sp_vbox1 = wx.BoxSizer(wx.VERTICAL)

        self.scrollPanel.SetSizer(self.sp_vbox1)

        self.topVerticalBox.Add(self.text, flag=wx.EXPAND | wx.LEFT, border=5)
        self.topVerticalBox.Add(self.summaryBtn, flag=wx.ALIGN_CENTER | wx.ALL, border=3)
        self.topVerticalBox.AddSpacer(10)
        self.topVerticalBox.Add(self.scrollPanel, flag=wx.EXPAND)

        self.SetSizerAndFit(self.topVerticalBox)

    def OrganizeData(self):

        self.sp_vbox1.Clear(True)
        self.consumption.clear()

        currentMonth = ''

        for i in range(0, len(self.data)):
            # words -> [0]dia, [1]mes and [2]ano.
            words = self.data[i]['date'].split('/')

            if currentMonth != words[1]:
                if currentMonth != '':
                    self.sp_vbox1.Add(vBox)

                currentMonth = words[1]
                text = wx.StaticText(self.scrollPanel, wx.ID_ANY, f"{dp.getMonthName(int((words[1])))} de {words[2]}")

                # Grid onde os botões dos dias serão adicionados
                gridSizer = wx.GridSizer(rows=5, cols=4, hgap=5, vgap=5)

                vBox = wx.BoxSizer(wx.VERTICAL)
                vBox.Add(text, flag=wx.ALL, border=5)
                vBox.Add(gridSizer, flag=wx.ALL, border=5)

            # Cria o botão para o dia e o adiciona ao grid.
            button = wx.Button(self.scrollPanel, 1000 + i, label=words[0], size=((60, 20)))
            button.Bind(wx.EVT_BUTTON, self.OnButtonClicked)
            gridSizer.Add(button, border=5)

            dayConsumption = sum(self.data[i]['xyValues'][1])
            self.consumption.append(dayConsumption)

        self.sp_vbox1.Add(vBox)
        self.sp_vbox1.Layout()

        # O gráfico fica bugado se tiver apenas um dia.
        if len(self.consumption) == 1:
            self.summaryBtn.Enable(False)
        else:
            self.summaryBtn.Enable(True)

        # Comeca a escrever os dados do gráfico de maior consumo.
        bigger = dp.getBiggerValue(self.consumption)
        self.index = bigger[0]
        self.value = bigger[1]

        self.k2 = dp.get_day_k2_factor(self.data[self.index]['xyValues'][1])
        self.fd = dp.get_fd(self.k2)

        msg = f"O dia de maior consumo foi em {self.data[self.index]['date']} com {'{:.2f}'.format(self.value)} m³/h.\n"
        msg += f"O fator K2 é de {'{:.2f}'.format(self.k2)} e o FD de {'{:.2f}'.format(self.fd)}"
        self.text.SetLabelText(msg)

    def OnButtonClicked(self, event):
        """ Chamada quando um botão é apertado. """

        ID = event.GetEventObject().Id
        ID -= 1000

        if ID == self.index:    # Se for o gráfico escolhido for o de maior consumo...
            self._plot_graph(self.data[ID], f"{self.data[ID]['date']}", True, index=ID)
        else:
            self._plot_graph(self.data[ID], f"{self.data[ID]['date']}", False, index=ID)



    def OnSummary(self, event):
        """ Chamada quando o usuário clica no botão para desenhar o gráfico geral. """

        x_val = []

        for dic in self.data:
            x_val.append(dic['date'])

        xy_val = [x_val, self.consumption]
        self._plot_graph(xy_val, 'Gráfico Geral de Consumo', False, isSummary=True)

    def _plot_graph(self, data, title, isBigger, isSummary=False, index=None):
        """
        Plota o gráfico. Cria uma nova janela. isBigger é um bool que sinaliza se o dia foi o de maior consumo.

        Parâmetros
        ----------
        ``isBigger`` : indica se o dia é o de maior consumo, portanto fatores KD e de demanda são escritos.
        ``isSummary`` : indica se o gráfico é o de consumo geral.
        ``index`` : é usado em _draw_graph_info() para buscar as horas abaixo e acima da vazão média.
        """

        fig, ax = plt.subplots(figsize=(11, 6))
        ax.xaxis.set_tick_params(rotation=30, labelsize=10)

        # Informacoes do gráfico.
        ax.set_xlabel('Hora')
        ax.set_ylabel('Consumo (m³/dia)')

        plt.suptitle(title, x=0.07, y=0.98, ha='left', fontsize=15)

        x = []
        # Define a formatacao do eixo Y.
        if isSummary:
            for date in data[0]:
                x.append(datetime.strptime(date, '%d/%m/%Y'))

            fmt = mdates.DateFormatter('%d/%m/%Y')
            y = self.consumption

        else:
            date = data['date']
            for hour in data['xyValues'][0]:
                x.append(datetime.strptime(date + hour, '%d/%m/%Y%H:%M'))

            fmt = mdates.DateFormatter('%H:%M')
            y = data['xyValues'][1]

        plt.plot(x, y, '-r', lw=2, label='Consumo')
        ax.xaxis.set_major_formatter(fmt)  # Aplica a formatacao.
        fig.autofmt_xdate()  # Aplica a 'organizacao'.

        # remove spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # estiliza o grid
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='gray', linestyle='dashed', alpha=0.2)
        ax.xaxis.grid(color='gray', linestyle='dashed', alpha=0.2)

        self._draw_graph_info(ax, fig, y, isBigger, isSummary, index)
        if self.isSaveToDisk:
            plt.savefig(self.path, bbox_inches='tight')
        else:
            plt.show()

    def _draw_graph_info(self, ax, fig, y_list, isBigger, isSummary, index):
        """ Imprime informacoes no gráfico.
        - Vazao maxima, media e minima,
        - Volume medio diario de consumo
        - Fator K2
        - Fator de Demanda
        - Imprime a linha de vazao media.
        """

        # Calculo dos parametros.
        vazao_maxima = "{:.2f}".format(max(y_list))
        vazao_media = float("{:.2f}".format(sum(y_list) / len(y_list)))
        vazao_minima = "{:.2f}".format(min(y_list))
        volume_diario = "{:.2f}".format(sum(y_list))
        fator_k2 = "{:.2f}".format(self.k2)
        fator_demanda = "{:.2f}".format(dp.get_fd(float(fator_k2)))

        # Contrucao da string com os resultados.
        if isSummary:
            string = f"Vazão Máxima: {vazao_maxima} | Vazão Média: {vazao_media} | Vazão Mínima: {vazao_minima}"

        else:
            if isBigger:
                string = f"Vazão Máxima: {vazao_maxima} | Vazão Média: {vazao_media} | Vazão Mínima: {vazao_minima} | Volume Diário: {volume_diario} | Fator K2: {fator_k2} | Fator de Demanda: {fator_demanda}"
            else:
                string = f"Vazão Máxima: {vazao_maxima} | Vazão Média: {vazao_media} | Vazão Mínima: {vazao_minima} | Volume Diário: {volume_diario}"

            infos = self.getUsageHours(self.data[index], vazao_media)
            string += f"\nHoras acima da vazão média: {infos[0]}, com consumo de {infos[6]} | Horas abaixo da vazão média: {infos[1]}, com consumo de {infos[7]}\n"
            string += f"Volume consumido no horário -> Ponta: {infos[2]} ({infos[3]}%), Fora da Ponta: {infos[4]} ({infos[5]}%)"

            # Adicionando o eixo da vazao media.
            ax.axhline(y=vazao_media, color='g', label='Vazão Média')

        # Adicionando o texto ao gráfico.
        plt.title(string, loc='left', fontsize=10)
        ax.legend(loc='best')

        plt.tight_layout()

    def getUsageHours(self, xyValues, vazao_media):
        ''' Funcao recebe ``xyValues``, que e um list com os valores X e Y do gráfico, respectivamente e retorna,
        em uma tupla, alguns indicadores do dia.

         Exemplo: (hoursAbove, hoursBelow, pontaConsumo, pontaPercent, foraPontaConsumo, foraPontaPercent, consumoAboveVazao, consumoBelowVazao) '''

        above = 0
        below = 0
        consumoTotal = 0
        pontaConsumo = 0
        foraPontaConsumo = 0
        consumoAboveVazao = 0
        consumoBelowVazao = 0

        lastTime = xyValues['xyValues'][0][0]

        for i in range(0, len(xyValues['xyValues'][1])):
            value = xyValues['xyValues'][1][i]
            now = xyValues['xyValues'][0][i]
            h, m = now.split(':')

            consumoTotal += value

            if int(h) >= 18 and int(h) <= 20:
                pontaConsumo += value
            else:
                foraPontaConsumo += value

            if value >= vazao_media:
                consumoAboveVazao += value
            else:
                consumoBelowVazao += value

            if value >= vazao_media:
                above += dp.getTimesDifference(lastTime, now)
            else:
                below += dp.getTimesDifference(lastTime, now)

            lastTime = xyValues['xyValues'][0][i]

        # transformação dos floats em strings com definição das casas decimais.
        outAbove = '{:.1f}'.format(above)
        outBelow = '{:.1f}'.format(below)
        outPontaConsumo = '{:.2f}'.format(pontaConsumo)
        outPontaPercent = '{:.1f}'.format((pontaConsumo / consumoTotal) * 100)
        outForaPontaConsumo = '{:.2f}'.format(foraPontaConsumo)
        outForaPontaPercent = '{:.1f}'.format((foraPontaConsumo / consumoTotal) * 100)
        outConsumoAboveVazao = '{:.2f}'.format(consumoAboveVazao)
        outConsumoBelowVazao = '{:.2f}'.format(consumoBelowVazao)

        return (outAbove, outBelow, outPontaConsumo, outPontaPercent, outForaPontaConsumo, outForaPontaPercent, outConsumoAboveVazao, outConsumoBelowVazao)