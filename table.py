'''
table.py
Arquivo contem a classe responsável pela tabela.
'''

import wx
import wx.grid as gridlib
import data_processing as dp
import global_variables as gv

class Table(wx.Frame):

    def __init__(self, parent, row, col):
        wx.Frame.__init__(parent, None, wx.ID_ANY)

        self.parent = parent

        self.panel = wx.Panel(parent, wx.ID_ANY)
        self.panel.SetMinSize((475, 490))
        self.grid = gridlib.Grid(self.panel)
        self.grid.CreateGrid(row, col)
        self.grid.ShowScrollbars(False, True)
        self.grid.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        # "Esticando" as colunas para caber números com muitas casas decimais.
        self.grid.SetColSize(0, 125)
        self.grid.SetColSize(1, 125)
        self.grid.SetColSize(2, 125)

        self.grid.SetColLabelValue(0, 'Data')
        self.grid.SetColLabelValue(1, 'Horário')
        self.grid.SetColLabelValue(2, 'Consumo')

        # A fileira comeca do índice 0, mas o número é atualizado com a quantidade de dados, ou seja, aponta para a fileira seguinte da última inserção.
        # Usamos disso para inserir os próximos dados exatamente em self.lastFilledRow.
        self.lastFilledRow = 0
        self.rowLength = row
        self.curRow = 0
        self.currentlySelectedCell = (0, 0)
        self.makeCellsReadOnly()

        self.grid.Bind(gridlib.EVT_GRID_EDITOR_CREATED, self.onCellEdit)
        self.grid.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onRowSelected)
        self.grid.Bind(wx.EVT_KEY_DOWN, self.OnKey)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid, 1, wx.EXPAND, 5)
        self.panel.SetSizer(sizer)

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


    def onEditorKey(self, event):
        ''' Mantém a vigia pelas setas de CIMA e BAIXO do teclado. '''

        keycode = event.GetKeyCode()
        if keycode == wx.WXK_UP:
            self.grid.MoveCursorUp(False)
        elif keycode == wx.WXK_DOWN:
            self.grid.MoveCursorDown(False)

        event.Skip()

    def onRowSelected(self, event):
        ''' Chamada quando o usuário mudar de célula. '''

        self.curRow = event.GetRow()
        self.currentlySelectedCell = (event.GetRow(), event.GetCol())

        event.Skip()

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


    def copyClipboardToTable(self, text):
        ''' Copia o `text` extraido do Clipboard para a tabela. '''

        row = self.curRow

        for line in text.splitlines():
            if row < self.rowLength:
                self.grid.SetCellValue(row, 2, line.strip())
            else:
                break

            row += 1

        self.parent.isSaved = False
        self.parent.updateTitleName()

    def transferTableToList(self, out_list):
        """ Transfere os dados da tabela para a lista ``list`` no formato:
        [{'date': '09/03/2021', 'time': '12:30', 'value': '12.9'}, ...]
        """

        out_list.clear()

        empytStrFound = False
        i = 0
        j = 0
        dic = {}

        while i < self.rowLength:
            if empytStrFound:
                break

            while j < 3:
                data = self.grid.GetCellValue(i, j)

                # Se encontrar uma célula vazia, para.
                if data == '':
                    empytStrFound = True
                    break

                if j == 0:
                    dic['date'] = data
                elif j == 1:
                    dic['time'] = data
                else:
                    dic['value'] = data

                j += 1

            i += 1
            j = 0

            if not empytStrFound:
                out_list.append(dic)
                dic = {}


    def transferListToTable(self, in_list):
        """ Transfere os dados da ``in_list`` para as tabelas. """

        self.grid.ClearGrid()

        i = 0
        j = 0
        length = len(in_list)

        while i < length:
            while j < 3:
                if j == 0:
                    date = in_list[i]['date']
                    self.grid.SetCellValue(i, j, date)
                elif j == 1:
                    self.grid.SetCellValue(i, j, in_list[i]['time'])
                else:
                    self.grid.SetCellValue(i, j, in_list[i]['value'])

                j += 1

            if i == length - 1:
                self.parent.lastDate = date
                self.lastFilledRow = length

            i += 1
            j = 0

    def clearTable(self):
        """ Limpa toda a tabela. """

        self.grid.ClearGrid()
        self.lastFilledRow = 0
        self.deleteRows(self.rowLength - self.parent.defaultRowSize)
        self.makeCellsReadOnly()


    def checkConsumoValue(self, row):
        """ Analiza a célula por erros. Se algum erro for encontrado, retorna True. """

        value = self.grid.GetCellValue(row, 2)

        if value == '':
            self.grid.SetCellBackgroundColour(row, 2, gv.RED_ERROR)
            return True

        if not dp.isFloat(self.grid.GetCellValue(row, 2)):
            self.grid.SetCellBackgroundColour(row, 2, gv.RED_ERROR)
            return True

        else:
            if float(self.grid.GetCellValue(row, 2)) < 0:
                self.grid.SetCellBackgroundColour(row, 2, gv.RED_ERROR)
                return True
            else:
                self.grid.SetCellBackgroundColour(row, 2, wx.NullColour)
                return False


    def paintAllBlank(self):
        """ Descolore todas as células de consumo. Geralmente chamada quando um arquivo e aberto. """

        i = 0
        while i < self.rowLength:
            self.grid.SetCellBackgroundColour(i, 2, wx.NullColour)
            i += 1

        self.grid.ForceRefresh()


    def checkOneRowHole(self, row):
        """ Checa por células vazias em apenas UMA fileira. Retorna True se um buraco
        for encontrado. """

        emptyCellFound = False
        notEmptyCellFound = False

        for i in range(0, 3):
            value = self.grid.GetCellValue(row, i)

            if value == '':
                emptyCellFound = True
            else:
                notEmptyCellFound = True

        if emptyCellFound and notEmptyCellFound:
            return True
        else:
            return False


    def generateDate(self, interval, date):
        """ Funcao preenche os campos da tabela com datas. """

        interval = int(24 * (60 / interval))# Quantos dados terao que ser inseridos.

        for i in range(self.lastFilledRow, self.lastFilledRow + interval):
            self.grid.SetCellValue(i, 0, date)


    def generateTime(self, interval):
        """ Funcao preenche os campos da tabela com horarios. """

        rowsNumber = int(24 * (60 / interval))  # Quantos dados terao que ser inseridos.
        hm = [0, 0]

        for i in range(self.lastFilledRow, self.lastFilledRow + rowsNumber):
            self.grid.SetCellValue(i, 1, dp.addMinutes(hm, interval))


    def rearrangeRows(self, rowsNeeded):
        ''' Recebe a quantidade de fileiras necessarias, ``rowsNeeded``, e gera fileiras de acordo.
        Deve ser chamada antes dos dados serem inseridos na tabela. '''

        freeSpace = self.rowLength - self.lastFilledRow
        self.generateRows(rowsNeeded - freeSpace)


    def updateTimeDateVariables(self, interval, date):
        ''' Atualiza as variaveis referentes as datas e horarios, como tambem faz as células de consumo ficarem editaveis novamente.
        Deve ser chamada, obrigatoriamente, depois de generateDate() e generateTime(). '''

        rowsAdded = int(24 * (60 / interval))

        self.lastFilledRow += rowsAdded
        self.parent.lastDate = date


    def generateRows(self, number):
        """ Funcao cria mais ``number`` fileiras na tabela. """

        oldLength = self.rowLength
        self.grid.AppendRows(number)
        self.rowLength += number
        self.makeCellsReadOnly(oldLength)


    def deleteRows(self, number, start=0):
        """ Funcao deleta fileiras na tabela. """

        if self.rowLength <= 0:
            return

        self.grid.DeleteRows(start, number)
        self.rowLength -= number


    def makeCellsReadOnly(self, startOffset=0):
        ''' Faz as células Data e Horário ficarem apenas no modo leitura. Usa self.rowLength para saber onde parar. '''

        for row in range(0 + startOffset, self.rowLength):
            for col in range(0, 2):
                self.grid.SetReadOnly(row, col)
