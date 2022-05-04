"""
data_processing.py
Arquivo contem as funcoes para a manipulacao dos dados
"""

import wx
import numpy as np
from scipy.interpolate import make_interp_spline
import datetime
import global_variables as gv

def is_date(date):
    """ Recebe uma string ``date`` e verifica se está no formato
    DD/MM/AAAA  (Ano restrito a 1901 ~ 2199).
    Retorna True em caso de sucesso. False, caso contrário.
    """

    if not isinstance(date, str):
        return False

    if len(date) != 10:
        return False

    date = date.strip()

    # Separa o dia, mes e ano para uma lista.
    words = date.split('/')

    # Verifica se o que existe na data sao realmente numeros
    numbers = []
    for w in words:
        try:
            numbers.append(int(w))
        except ValueError:
            return False

    day = numbers[0]
    month = numbers[1]
    year = numbers[2]

    try:
        datetime.datetime(year, month, day)
    except:
        return False

    return True

def is_timetable(time):
    """ Retorna True se a string fornecida estiver no padrão HH:MM (24hrs).
        Exemplo de string correta: '12:30' """

    # O comprimento do tempo e no formato hh:mm, entao time TEM que ter len = 5.
    if not (len(time)) == 5:
        return False

    hour = ''
    minute = ''
    sep_found = False

    for i in range(0, len(time)):
        if time[i] == ':':
            sep_found = True
            continue

        if not sep_found:
            hour += time[i]
        else:
            minute += time[i]

    if not hour.isdigit() or not minute.isdigit():
        return False

    hour = int(hour)
    minute = int(minute)

    if not ((hour >= 0 and hour <= 23) and (minute >= 0 and minute <= 59)):
        return False

    return True

def isInt(number):
    """ Verifica se `number` é um int. Retorna True se sim. """

    try:
        int(number)
    except ValueError:
        return False

    return True

def isFloat(number):
    """ Verifica se `number` é um float. Retorna True se sim. """

    try:
        float(number)
    except ValueError:
        return False

    return True

def addMinutes(hm, interval):
    """ Recebe uma lista de inteiros `hm` no formato [hour, minute] e retorna uma string deste horário convertida no formato HH:MM.
        Antes de haver o retorno, `interval` é adicionada na lista `hm`. `interval` não pode ser maior que 60. Exemplo:
        addMinutos([0, 0], 15) -> 00:00\n
        Após a chamada acima, `hm` -> [0, 15]
    """

    # Primeiramente, formata.
    out = ''
    if hm[0] < 10:
        out += '0'
        out += str(hm[0])
    else:
        out += str(hm[0])

    out += ':'

    if hm[1] < 10:
        out += '0'
        out += str(hm[1])
    else:
        out += str(hm[1])

    # Adicionando o interval na lista de horário.
    hm[1] += interval
    if hm[1] == 60:
        hm[1] = 0
        hm[0] += 1

    if hm[0] == 24:
        hm[0] = 0
        hm[1] = 0

    return out

def getMonthName(index):
    """ Recebe um inteiro (1 ~ 12) e retorna uma string com o nome do mês. """

    if index == 1:
        return 'Janeiro'
    elif index == 2:
        return 'Fevereiro'
    elif index == 3:
        return 'Março'
    elif index == 4:
        return 'Abril'
    elif index == 5:
        return 'Maio'
    elif index == 6:
        return 'Junho'
    elif index == 7:
        return 'Julho'
    elif index == 8:
        return 'Agosto'
    elif index == 9:
        return 'Setembro'
    elif index == 10:
        return 'Outubro'
    elif index == 11:
        return 'Novembro'
    elif index == 12:
        return 'Dezembro'
    else:
        return None

def excelDateToOurDate(date):
    """ O campo de data nos arquivos excel vem no formato '2021-03-31 00:00:00'.
    Essa função recebe uma string como essa e retorna a data no formato DD/MM/YYYY """

    out = date[:10]
    return datetime.datetime.strptime(out, '%Y-%m-%d').strftime('%d/%m/%Y')

def excelTimeToOurTime(time):
    """ O campo de horario nos arquivos excel vem no formato '00:00:00'.
    Essa função recebe uma string como essa e retorna o horário no formato '00:00' """

    return time[:5]

def getTableReadyData(data):
    """ Recebe uma lista com os dados de consumo de água e retorna a lista com os dados prontos para exibição.
    PS: ['value'] ja serão "entreges" como floats. """

    if not data:
        return None

    daysList = []

    # Ira conter os dados para um unico grafico / dia. Sera adicionada a daysList posteriormente.
    tempX = []
    tempY = []
    tempDic = {}    # Ira conter os dados de um dia: {'date': '14/03/2021', 'xyValues': [[01:00, 02:00, ...], [18.5, 17.2, ...]]}

    currentDate = data[0]['date']
    tempDic['date'] = currentDate

    for dic in data:
        if currentDate != dic['date']:
            xyList = [tempX, tempY]
            tempDic['xyValues'] = xyList
            daysList.append(tempDic)

            tempX = []
            tempY = []
            tempDic = {}

            currentDate = dic['date']
            tempDic['date'] = currentDate

        tempX.append(dic['time'])
        tempY.append(float(dic['value']))

    # Quando for o último dia de dados da lista, precisamos adicionar as informações fora do loop.
    xyList = [tempX, tempY]
    tempDic['xyValues'] = xyList
    daysList.append(tempDic)

    return daysList

def get_day_k2_factor(y_val):
    """ Retorna o fator K2 de um dia. """

    return max(y_val) / ( sum(y_val) / len(y_val) )

def get_fd(k2):
    """ Retorna o fator FD. Precisa do K2 para o input."""

    if k2 != 0:
        return 1 / k2

    return None

def getBiggerValue(in_list):
    """ Recebe uma lista e retorna um tupla contendo o índice do maior valor encontrado e o própio valor.
    Ex: (index, value) """

    bigger = -999
    index = -1

    for i in range(0, len(in_list)):
        if in_list[i] > bigger:
            bigger = in_list[i]
            index = i

    return (index, bigger)

def getTimesDifference(time1, time2):
    ''' Recebe duas datas no formato HH:MM e retorna a diferença entre elas em horas. Em caso de dados inválidos, retorna None.
    `time2` deve ser maior que `time1`. `OBS: 00:00 é maior que 23:59.` '''

    FMT = '%H:%M'
    try:
        tdelta = datetime.datetime.strptime(time1, FMT) - datetime.datetime.strptime(time2, FMT)
    except:
        return None

    if time1 == time2:
        return 0

    diff = abs(tdelta.total_seconds())
    if tdelta.days > -1:
        diff -= 86400

    return abs(diff / 3600)

def isTimeBigger(time1, time2):
    ''' Retorna True se ``time2`` for maior que ``time1``. '''

    FMT = '%H:%M'
    try:
        datetime.datetime.strptime(time1, FMT) - datetime.datetime.strptime(time2, FMT)
    except:
        return None

    if time2 > time1:
        return True
    else:
        return False

def isDateBigger(date1, date2):
    ''' Retorna True se ``date2`` for maior que ``date1``. '''

    # Nossas datas estão no formato dd/mm/yyyy
    d, m, y = date1.split('/')
    d1 = datetime.date(int(y), int(m), int(d))

    d, m, y = date2.split('/')
    d2 = datetime.date(int(y), int(m), int(d))

    if d2 > d1:
        return True
    else:
        return False

def smoothGraph(x, y, stops=10):
    ''' Recebe duas listas e suaviza os valores para a impressão. `x` e `y` precisam ser numpy.array. '''

    x_new = np.linspace(x.min(), x.max(), stops)
    a_BSpline = make_interp_spline(x, y)
    y_new = a_BSpline(x_new)

    return (x_new, y_new)

def cutLastPieceGraph(arr, percentage):
    ''' Retorna um novo numpy array sem os últimos ``percentage``. '''

    cut = int((len(arr) * percentage) / 100)
    length = len(arr) - cut
    newArr = np.array(arr[:length])

    return newArr

def checkSorting(arr):
    ''' Verifica se a lista `arr` de números está ordenada. Retorna True se sim. `arr` não é modificado. '''

    sorted_arr = arr[:]
    sorted_arr.sort()

    for i in range(0, len(arr)):
        if sorted_arr[i] != arr[i]:
            return False

    return True

def colorField(field, isThereError):
    ''' Recebe a referência, `field`, de um widget com a função "SetBackgroundColour()" e a colore
    de acordo com `isThereError`. '''

    if isThereError:
        field.SetBackgroundColour(gv.RED_ERROR)
    else:
        field.SetBackgroundColour(wx.NullColour)

    field.Refresh()

def isFieldEmpty(value):
    ''' Recebe um widget de texto com a função "GetValue()" e verifica se ele está vazio. Retorna True se sim.'''

    if not value.isspace() and value != '':
        return False
    else:
        return True