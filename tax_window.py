import wx
import energy_consumption
import parameters

class ResultWindow(wx.Frame):
    ''' Classe responsavel pela criacao das janelas de calculo das Tarifas Verdes e Azuis. '''

    def __init__(self, parent, color, aliFields, greenFields, blueFields):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, parent, style=style)

        self.grabDataFromFile()
        self.parent = parent
        self.color = color

        # aliFields -> Em ordem, ICMS, PIS e CONFINS
        # greenFields -> Em ordem, Custo de Energia Dentro da Ponta, Fora da Ponta e Preco da Demanda
        # blueFields -> Em ordem, Preco Da Demanda no Horario de Ponta, Fora de Ponta, Preco da Energia Dentro da Ponta, Fora da ponta.

        self.aliFields = []
        for field in aliFields:
            self.aliFields.append(float(field.GetValue()))

        if self.color == 'GREEN':
            self.SetMinSize((666, 201))
            self.SetMaxSize((666, 201))

            self.greenFields = []
            for field in greenFields:
                self.greenFields.append(float(field.GetValue()))

        elif self.color == 'BLUE':
            self.SetMinSize((666, 228))
            self.SetMaxSize((666, 228))

            self.blueFields = []
            for field in blueFields:
                self.blueFields.append(float(field.GetValue()))

        else:
            self.Destoy()
            return

        self.Center()
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.Bind(wx.EVT_CLOSE, self.OnCloseApp)

        if color == 'GREEN':
            self.showGreenResult()
        elif color == 'BLUE':
            self.showBlueResult()

    def getDisplayField(self, text, value):
        ''' Retorna uma Horizontal Box Sizer com dois textos, um para a descricao e outro para o valor. '''

        lPanel = wx.Panel(self)
        rPanel = wx.Panel(self)

        hBox = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(13, wx.MODERN, wx.NORMAL, wx.NORMAL, False)

        lText = wx.StaticText(lPanel, wx.ID_ANY, text, size=(500, 5))
        lText.SetFont(font)
        rText = wx.StaticText(rPanel, wx.ID_ANY, f"{value} ", size=(150, 5), style=wx.TE_RIGHT)
        rText.SetBackgroundColour('#e0e0e0')
        rText.SetFont(font)

        hBox.Add(lPanel)
        hBox.Add(rPanel)

        return hBox

    def showGreenResult(self):
        ''' Mostra os resultados de calculo para a tarifa verde. '''

        self.SetTitle('Resultados: Tarifa Verde')

        CEEP = self.consumoPonta * self.greenFields[0] / (1 - (self.aliFields[0] - self.aliFields[1] - self.aliFields[2]) / 100)
        CEEFP = self.consumoForaPonta * self.greenFields[1] / (1 - (self.aliFields[0] - self.aliFields[1] - self.aliFields[2]) / 100)

        num = 9.81 * self.vazaoBombeada * self.alturaNanometrica / ( (self.rendimentoMotor / 100) * (self.rendimentoBomba / 100) ) * self.greenFields[2]
        den = 1 - (self.aliFields[0] - self.aliFields[1] - self.aliFields[2]) / 100
        CD = num / den

        CTEE = CEEP + CEEFP + CD
        CMEE = CTEE / self.consumoTotal
        CMMB = CTEE / self.volumeBombeado

        self.sizer.Add(self.getDisplayField(' Custo de Energia Elétrica na Ponta \t(R$/mês)', self.returnFormatted(CEEP)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo de Energia Elétrica Fora da Ponta(R$/mês)', self.returnFormatted(CEEFP)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo da Demanda \t\t\t(R$/mês)', self.returnFormatted(CD)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo Total de Energia Elétrica \t(R$/mês)', self.returnFormatted(CTEE)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo Médio da Energia Elétrica \t(R$/mês)', self.returnFormatted(CMEE)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo Médio por m³ de Água Bombeado \t(R$/m³)', self.returnFormatted(CMMB)), flag=wx.TOP | wx.BOTTOM, border=3)

        self.SetSizer(self.sizer)

    def showBlueResult(self):
        ''' Mostra os resultados de cálculo para a tarifa azul. '''

        self.SetTitle('Resultados: Tarifa Azul')

        CEEP = self.consumoPonta * self.blueFields[2] / (1 - (self.aliFields[0] - self.aliFields[1] - self.aliFields[2]) / 100)
        CEEFP = self.consumoForaPonta * self.blueFields[3] / (1 - (self.aliFields[0] - self.aliFields[1] - self.aliFields[2]) / 100)

        num = 9.81 * self.vazaoBombeada * self.alturaNanometrica / ( (self.rendimentoMotor / 100) * (self.rendimentoBomba / 100)) * self.blueFields[0]
        den = 1 - (self.aliFields[0] - self.aliFields[1] - self.aliFields[2]) / 100
        CDP = num / den

        num = 9.81 * self.vazaoBombeada * self.alturaNanometrica / ( (self.rendimentoMotor / 100) * (self.rendimentoBomba / 100)) * self.blueFields[1]
        CDFP = num / den

        CTEE = CEEP + CEEFP + CDP + CDFP
        CMEE = CTEE / self.consumoTotal
        CMMB = CTEE / self.volumeBombeado

        self.sizer.Add(self.getDisplayField(' Custo de Energia Elétrica na Ponta \t(R$/mês)', self.returnFormatted(CEEP)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo de Energia Elétrica Fora da Ponta(R$/mês)', self.returnFormatted(CEEFP)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo da Demanda na Ponta \t\t(R$/mês)', self.returnFormatted(CDP)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo da Demanda Fora da Ponta \t(R$/mês)', self.returnFormatted(CDFP)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo Total de Energia Elétrica \t(R$/mês)', self.returnFormatted(CTEE)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo Médio da Energia Elétrica \t(R$/kWh)', self.returnFormatted(CMEE)), flag=wx.TOP | wx.BOTTOM, border=3)
        self.sizer.Add(self.getDisplayField(' Custo Médio por m³ de Água Bombeado \t(R$/m³)', self.returnFormatted(CMMB)), flag=wx.TOP | wx.BOTTOM, border=3)

        self.SetSizer(self.sizer)

    def grabDataFromFile(self):
        ''' Funcao retira todas as informações necessárias do arquivo e retorna True se todas as variaveis e informações necessarias
        estão presentes. '''

        # Os item dentro da lista correspondem ao botao Parametros do Sistema, ja convertidos em float, em ordem...
        # [0] --> Vazao Bombeada
        # [1] --> Altura nanometrica
        # [2] --> Rendimento do Motor
        # [3] --> Rendimento da Bomba
        # [4] --> Numero de bombas em paralelo
        # [5] --> Tempo de operacao no horario da ponta
        # [6] --> Tempo de operacao no horario fora da ponta
        self.parametersValues = []

        par = parameters.ParametersWindow(None)
        for i in range(0, len(par.textBoxesRefs)):
            value = float(par.textBoxesRefs[i].GetValue().strip())
            self.parametersValues.append(value)
        par.Destroy()

        # Essas sao as variaveis de "Parametros do Sistema"
        self.vazaoBombeada = self.parametersValues[0]
        self.alturaNanometrica = self.parametersValues[1]
        self.rendimentoMotor = self.parametersValues[2]
        self.rendimentoBomba = self.parametersValues[3]
        self.bombasParalelo = self.parametersValues[4]
        self.operacaoDentroPonta = self.parametersValues[5]
        self.operacaoForaPonta = self.parametersValues[6]

        # Estas variaveis sao calculadas em "Consumo de Energia e Indicadores Hidroenergeticos" com as
        # variaveis de "Parametros do Sistema"
        energy = energy_consumption.EnergyConsumption(None)
        self.consumoPonta = energy.energiaPonta(True) # Consumo de Energia dentro da Ponta
        self.consumoForaPonta = energy.energiaPonta(False) # Consumo de Energia Fora da Ponta
        self.consumoTotal = energy.consumoTotal() # Consumo de Energia Total
        self.volumeBombeado = energy.volumeBombeado() # Volume Bombeado
        self.consumoEspecifico = energy.consumoEspecifico() # Consumo Específico
        self.consumoEspecificoNor = energy.consumoEspecificoNormalizado() # Consumo Especifico Normalizado
        energy.Destroy()

        return True

    def returnFormatted(self, number):
        """ Retorna o numero formato em string com 2 casas decimais. """

        return "{:.2f}".format(number)

    def OnCloseApp(self, event):
        ''' Chamada quando o usuario clica em fechar no campo superior direito da janela. '''

        if self.color == 'GREEN':
            self.parent.greenResultWindow = None
        elif self.color == 'BLUE':
            self.parent.blueResultWindow = None

        self.Destroy()