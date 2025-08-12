"""
pdf_export.py
Arquivo responsável pela exportação em .PDF
"""

import os
import shutil
import wx
from fpdf import FPDF, XPos
import app.global_variables as gv
import app.file_manager as fm

import app.windows.water_consumption as water_consumption
import app.windows.parameters as parameters
import app.windows.energy_consumption as energy_consumption
import app.windows.custos as custos
import app.windows.hydric as hydric

class PDF(FPDF):
    def footer(self):
        self.set_left_margin(0)
        self.set_y(-15)
        self.set_font("helvetica", "I", 12)
        self.set_text_color(128)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


    def colored_table(self, headings, rows, col_widths=(80, 20, 40), fill_color=(255, 100, 0)):
        # Colors, line width and bold font:
        self.set_fill_color(fill_color[0], fill_color[1], fill_color[2])
        self.set_text_color(255)
        self.set_draw_color(fill_color[0], fill_color[1], fill_color[2])
        self.set_line_width(0.3)
        self.set_font(style="B")
        for col_width, heading in zip(col_widths, headings):
            self.cell(col_width, 7, heading, XPos.LEFT, XPos.RIGHT, align="C", fill=True)
            # self.cell(60, 10, 'Powered by FPDF.', new_x=XPos.LMARGIN, new_y=YPos.NEXT, , align='C')

        self.ln()
        # Color and font restoration:
        self.set_fill_color(224, 235, 255)
        self.set_text_color(0)
        self.set_font()
        fill = False
        for row in rows:
            self.cell(col_widths[0], 6, row[0], "LR", fill=fill)
            self.cell(col_widths[1], 6, row[1], "LR", fill=fill)
            self.cell(col_widths[2], 6, row[2], "LR", fill=fill)
            self.ln()
            fill = not fill
        self.cell(sum(col_widths), 0, "", "T")

class ExportPDF(wx.Dialog):
    ''' Responsável pela exportação para um arquivo .pdf. '''

    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        super().__init__(parent, style=style)

        self.userPath = f"{os.path.expanduser('~')}"
        self.grabData()

    def grabEnergyData(self):
        ''' Coleta os dados de energia. '''

        energy = energy_consumption.EnergyConsumption(self)
        self.parameters_keys = [
            ('Vazão Bombeada', 'm³/h', energy.summaryTextField[0].GetLabel().strip()),
            ('Altura Manométrica', 'm', energy.summaryTextField[1].GetLabel().strip()),
            ('Rendimento do Motor', '%', energy.summaryTextField[2].GetLabel().strip()),
            ('Rendimento da Bomba', '%', energy.summaryTextField[3].GetLabel().strip()),
            ('Bombas em paralelo', '', energy.summaryTextField[4].GetLabel().strip()),
            ('Tempo dentro do Horário de Ponta', 'h/dia', energy.summaryTextField[5].GetLabel().strip()),
            ('Tempo fora do Horário de Ponta', 'h/dia', energy.summaryTextField[6].GetLabel().strip())
            ]

        energy.OnCalculate(None)
        self.energy_keys = [
            ('Consumo na ponta', 'kWh/mês', energy.resultTextField[0].GetLabel().strip()),
            ('Consumo fora da ponta', 'kWh/mês', energy.resultTextField[1].GetLabel().strip()),
            ('Consumo Total', 'kWh/mês', energy.resultTextField[2].GetLabel().strip()),
            ('Volume Bombeado', 'm³/mês', energy.resultTextField[3].GetLabel().strip()),
            ('Consumo Específico', 'kWh/m³', energy.resultTextField[4].GetLabel().strip()),
            ('Consumo Específico Normalizado', 'kWh/m³/100m', energy.resultTextField[5].GetLabel().strip())
            ]

    def grabCustosData(self):
        ''' Coleta os dados de custos do sistema. '''

        custo = custos.Custos(self)
        self.custosTaxes_keys = [
            ('Alíquota ICMS', '%', custo.icms[1].GetValue()),
            ('Alíquota PIS', '%', custo.pis[1].GetValue()),
            ('Alíquota CONFINS', '%', custo.confins[1].GetValue()),
        ]

        self.custosGreenTax_keys = [
            ('Energia Ponta', 'R$/kWh', custo.greenEnergiaPonta[1].GetValue()),
            ('Energia Fora Ponta', 'R$/kWh', custo.greenEnergiaForaPonta[1].GetValue()),
            ('Preço Demanda', 'R$', custo.greenEnergiaDemanda[1].GetValue()),
        ]

        self.custosBlueTax_keys = [
            ('Demanda Ponta', 'R$/kWh',  custo.blueDemandaPonta[1].GetValue()),
            ('Demanda Fora Ponta', 'R$/kWh',  custo.blueDemandaForaPonta[1].GetValue()),
            ('Energia Ponta', 'R$/kWh',  custo.blueEnergiaPonta[1].GetValue()),
            ('Energia Fora Ponta', 'R$/kWh',  custo.blueEnergiaForaPonta[1].GetValue()),
        ]

        self.greenResult_keys = custo.OnGreenCalculate(None)
        self.blueResult_keys = custo.OnBlueCalculate(None)

    def grabHydricData(self):
        ''' Coleta os dados hídricos do sistema. '''

        hyd = hydric.HydricBalance(None, True, f"{self.userPath}/iph_cache")
        self.hydricFields1 = hyd.getOpt1Fields()
        self.hydricFields2 = hyd.getOpt2Fields()

        hyd.gatherData(0)
        hyd.gatherData(1)

    def grabData(self):
        ''' Coleta os dados necessários para a construção do .pdf. '''

        try:
            os.mkdir(f"{self.userPath}/iph_cache")
        except:
            pass

        pdf = None
        isAllIn = []
        isAllIn.append('#water_consumption_start' in gv.fileStartIndices.keys())
        isAllIn.append('#parameters_start' in gv.fileStartIndices.keys())
        isAllIn.append('#expenses_start' in gv.fileStartIndices.keys())
        isAllIn.append('#parameters_system_start' in gv.fileStartIndices.keys())
        isAllIn.append('#hydric_start' in gv.fileStartIndices.keys())

        if not all(isAllIn):
            dialog = wx.MessageDialog(self, 'O arquivo não contém os dados completos. Por favor, preencha todos os campos.', 'Dados insuficientes', wx.ICON_ERROR)
            dialog.ShowModal()
            self.Destroy()

        try:
            water = water_consumption.CreateWaterWindow(self)
            water.SaveOverallGraph(f"{self.userPath}/iph_cache/water.png")

            params = parameters.ParametersWindow(self)
            params.SaveAllGraphs(f"{self.userPath}/iph_cache")

            self.grabEnergyData()
            self.grabCustosData()
            self.grabHydricData()

            pdf = self.export()

        except:
            dialog = wx.MessageDialog(self, 'Erro durante a geração do .PDF. O arquivo pode estar corrompido ou com dados incorretos.', 'Erro', wx.ICON_ERROR)
            dialog.ShowModal()
            shutil.rmtree(f"{self.userPath}/iph_cache", True)
            self.Destroy()

        path = self.askFileName()
        if path:
            path = fm.putFileSuffix(path, '.pdf')
            pdf.output(path)
            dialog = wx.MessageDialog(self, 'Relatório gerado com sucesso.', 'Sucesso', wx.ICON_INFORMATION)
            dialog.ShowModal()
            shutil.rmtree(f"{self.userPath}/iph_cache", True)

        self.Destroy()

    def export(self):
        ''' Constrói o relário em .pdf. Retorna o objeto FPDF. '''

        headings = ['Parâmetro', 'Unidade', 'Valor']
        pdf = PDF('L', 'mm', 'A3')

        # Primeira página.
        pdf.add_page()
        pdf.image('assets/images/logo.png', 10, 10, 280)
        pdf.image('assets/images/iph_logo.png', 300, 12, 60)
        pdf.image('assets/images/lenhs_logo.png', 370, 9, 40)
        pdf.image(f"{os.path.expanduser('~')}/iph_cache/water.png", 30, 80, 350)

        pdf.set_font("helvetica", "BI", 20)
        pdf.cell(40, 100, "Relatório Geral")

        # Segunda página
        pdf.add_page()
        pdf.set_left_margin(10)
        pdf.set_font("Times", "", 14)
        pdf.set_y(95)
        pdf.colored_table(headings, self.parameters_keys)

        pdf.set_font("helvetica", "B", 32)
        pdf.set_xy(10, 50)
        pdf.cell(0, 0, "Parâmetros Operacionais")

        pdf.image(f"{os.path.expanduser('~')}/iph_cache/operation.png", 160, 20, 250)
        pdf.image(f"{os.path.expanduser('~')}/iph_cache/pump.png", 20, 180, 180)
        pdf.image(f"{os.path.expanduser('~')}/iph_cache/system.png", 220, 180, 180)

        # Terceira página
        pdf.add_page()
        pdf.set_left_margin(10)
        pdf.set_font("helvetica", "B", 32)
        pdf.cell(10, 10, "Consumo Energético e")
        pdf.cell(0, 40, "Indicadores Hidroenergéticos")
        pdf.set_y(60)

        pdf.set_font("Times", "", 16)
        pdf.colored_table(headings, self.energy_keys, (90, 40, 50))
        pdf.set_xy(10, 100)

        pdf.set_font("helvetica", "B", 32)
        pdf.cell(10, 100, "Impostos")
        pdf.set_y(180)
        pdf.set_font("Times", "", 16)
        pdf.colored_table(['Imposto', 'Unidade', 'Valor'], self.custosTaxes_keys, (90, 40, 50))

        pdf.set_font("helvetica", "B", 26)
        pdf.set_xy(200, 20)
        pdf.cell(0, 0, "Custos de Operação e Indicadores Financeiros")

        # Tarifa Verde
        pdf.set_y(60)
        pdf.set_left_margin(200)
        pdf.set_font("helvetica", "BI", 20)
        pdf.cell(10, 10, "Tarifa Verde")

        pdf.set_font("Times", "", 12)
        pdf.set_y(80)
        pdf.colored_table(headings, self.custosGreenTax_keys, (40, 20, 25), (164, 237, 176))
        pdf.set_left_margin(295)
        pdf.set_y(80)
        pdf.colored_table(headings, self.greenResult_keys, (75, 20, 20), (164, 237, 176))

        # Tarifa Azul
        pdf.set_y(180)
        pdf.set_left_margin(200)
        pdf.set_font("helvetica", "BI", 20)
        pdf.cell(10, 10, "Tarifa Azul")

        pdf.set_font("Times", "", 12)
        pdf.set_y(200)
        pdf.colored_table(headings, self.custosBlueTax_keys, (40, 20, 25), (90, 142, 219))
        pdf.set_left_margin(295)
        pdf.set_y(200)
        pdf.colored_table(headings, self.blueResult_keys, (75, 20, 20), (90, 142, 219))

        # Quarta página
        pdf.add_page()
        pdf.set_left_margin(15)
        pdf.set_font("helvetica", "B", 32)
        pdf.cell(400, 10, "Balanço Hídrico de Reservatório", align='C')

        pdf.set_x(25)
        pdf.set_font("helvetica", "BI", 20)
        pdf.cell(25, 65, "Opção 1 - Dados de Volume do Reservatório")
        pdf.set_y(70)
        pdf.set_font("Times", "", 16)
        pdf.colored_table(headings, self.hydricFields1, (90, 40, 50))

        pdf.image(f"{os.path.expanduser('~')}/iph_cache/opt0.png", 7, 140, 185)

        # "Opção 2 - Dados de Níveis do Reservatório"
        pdf.set_font("helvetica", "BI", 20)
        pdf.set_left_margin(225)
        pdf.set_xy(330, 30)
        pdf.cell(50, 25, "Opção 2 - Dados de Nível do Reservatório", align='R')
        pdf.set_y(70)
        pdf.set_font("Times", "", 16)
        pdf.colored_table(headings, self.hydricFields2, (90, 40, 50))

        pdf.image(f"{os.path.expanduser('~')}/iph_cache/opt1.png", 215, 140, 185)

        return pdf

    def askFileName(self):
        ''' Pergunta o nome e o diretório para salvar o arquivo. Retorna o path completo ou None, se cancelado. '''

        dialog = wx.FileDialog(self, f"Escolha um diretório...", gv.file_dir, '', '*.pdf*', wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetFilename()
            file_dir = dialog.GetDirectory()
            file_path = os.path.join(file_dir, filename)
            return file_path

        else:
            return None
