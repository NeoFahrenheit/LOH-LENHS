""" Arquivo que contem as funcoes necessarias para as operacoes ligadas
    ao gerenciamento de arquivos. """

import os
import csv
import global_variables as gv
import data_processing as dp

def getFileExtension(filename):
    """ Recebe um string com o nome do arquivo e retorna a extensao.
    Exemplo: 'myfile.txt' --> '.txt'
    Retorna '' caso a string esteja em um formato incorreto. """

    return os.path.splitext(filename)[1]


def putFileSuffix(filename, suffix):
    ''' Verifica se filename ja possui o sufixo informado. Se nao, adiciona e retorna filename modificado.
    Caso contrário, retorna filename não modificado. '''

    size = len(suffix)
    fileSuffix = filename[-size:]

    if fileSuffix == suffix:
        return filename
    else:
        return filename + suffix


def validate_line(line):
    """ Analisa uma linha de texto e ve se ela esta no padrao correto:
        hh:mm Consumo
    Retorna uma tupla (data, horario, consumo) em caso de sucesso. Caso contratio, None.
    Se `line` estiver vazia, retorna uma string vazia. """

    # Se a linha estiver vazia, ignora.
    if line.strip() == '':
        return ''

    words = line.split()

    # Se nao tiver tres palavras na linha...
    if not len(words) == 3:
        return None

    # Se a data nao tiver na formatacao e numeracao correta...
    if not dp.is_date(words[0]):
        return None

    # Se o horario nao tiver na formatacao correta...
    if not dp.is_timetable(words[1]):
        return None

    # Se a terceira palavra nao for um numero...
    if not dp.isFloat(words[2]):
        return None

    # Finalmente, retornamos a tupla.
    return (words[0], words[1], float(words[2]))

def createEmptyFile():
    ''' Cria e abre um arquivo "vazio". Utiliza `gv.file_path` para a criação. '''

    text = ['#parameters_pump_start\n', '#parameters_pump_end\n', '#parameters_system_start\n', '#parameters_system_end\n']

    with open(gv.file_path, "w") as f:
        f.write(''.join(text))

    gv.opened_file = open(gv.file_path, 'r')
    getEntrysDictAndFile()

def copyWaterFileDataToList():
    """ Abre o arquivo e retorna uma lista contendo apenas os dados.
    Exemplo: [{'date': '09/03/2021', 'time': '12:30', 'value': '12.9'}, ...]
    Retorna uma lista vazia em caso de erro ou falta de dados.
    """

    if not gv.fileLines or not '#water_consumption_start' in gv.fileStartIndices.keys():
        return []

    data = []
    dic = {}

    for i in range(gv.fileStartIndices['#water_consumption_start'], len(gv.fileLines)):
        if gv.fileLines[i].strip() == '#water_consumption_end': # Procura pela string que sinaliza o fim dos dados de consumo de agua.
            break

        if gv.fileLines[i][0] != '#':
            if not validate_line(gv.fileLines[i]):
                return []

            else:
                words = gv.fileLines[i].split()
                if(len(words)) == 3:
                    dic['date'] = words[0]
                    dic['time'] = words[1]
                    dic['value'] = words[2]

                    data.append(dic)
                    dic = {}

    return data

def analizeWaterData(data):
    ''' Recebe a lista de dados de agua e analiza para ver se estao de acordo com as regras. Retorna True em caso de sucesso. Exemplo de entrada:\n
    [{'date': '08/03/2021', 'time': '00:00', 'value': '20.16'}, {'date': '08/03/2021', 'time': '01:00', 'value': '19.70'}, ...]
     Retorna True se data estiver vazio. '''

    if not data:
        return True

    intervals = [60, 30, 15, 5, 1]
    curDate = data[0]['date']
    diff = 0
    timesList = []
    count = 1   # Conta os dias. Comeca em 1 pois 'curDate' ja contem a data da primeira linha de dados.

    for line in data:
        if curDate != line['date']:
            # Precisamos saber se a quantidade de dados e exatamente igual ao esperado para o diferenca de tempo entre uma hora e outra.
            if diff == 0 or len(timesList) != int(24 * (60 / round(diff * 60))):
                return False

            # A proxima data tem que ser maior que a anterior.
            if not dp.isDateBigger(curDate, line['date']):
                return False

            curDate = line['date']
            timesList.clear()
            diff = 0
            count += 1

        timesList.append(line['time'])

        # Quando tivermos dois ou mais horarios, podemos comecar a monitorar a diferenca entre eles.
        if len(timesList) >= 2:
            if len(timesList) == 2:
                diff = dp.getTimesDifference(timesList[-2], timesList[-1])
                # Se a diferenca de horarios nao estiver dentro daquelas que o programa aceita.
                if round(diff * 60) not in intervals: # diff esta em horas. Precisamos converter para minutos para comparar com intervals.
                    return False

            else:
                # A partir daqui, a diferena entre os dois ultimos horarios tem que ser sempre a mesma dos dois primeiros.
                if round(dp.getTimesDifference(timesList[-2], timesList[-1]) * 60) != round(diff * 60):
                    return False

        else:
            # O primeiro horario tem que ser sempre '00:00'.
            if line['time'] != '00:00':
                return False

    # Aqui vamos lidar se o arquivo tiver apenas dados para uma data.
    if count == 1:
        if diff == 0 or len(timesList) != int(24 * (60 / round(diff * 60))):
            return False

    return True


def analizeParametersData():
    ''' Analiza no arquivo os dados de Parametros do Sistema. Se tudo estiver OK, retorna True. '''

    start = gv.fileStartIndices['#parameters_start']
    count = 0

    for i in range(start, start + 7):
        value = gv.fileLines[i].strip()
        if not (dp.isInt(value) or dp.isFloat(value)):
            return False

        if float(value) <= 0:
            return False

        # Os valores entre os indices 0 e 3 precisam ser Flaot.
        else:
            if count == 2:
                n = float(value)
                if (n <= 0 or n > 100):
                    return False

            elif count == 3:
                n = float(value)
                if (n <= 0 or n > 100):
                    return False

            elif count == 4:
                if not dp.isInt(value):
                    return False

        count += 1

    return True

def analizeParametersPumpData():
    ''' Analiza no arquivo os dados da Curva da Bomba, pertencente a janela Parametros do Sistema. Se tudo estiver OK, retorna True. '''

    start = gv.fileStartIndices['#parameters_pump_start']
    end = gv.fileStartIndices['#parameters_pump_end']

    # Se o arquivo não contiver dados de Curva da Bomba, retorna True.
    # Como os '_start' já apontam para o inicío dos dados, se estes dados estiverem vazios, irá apontar para '_end' também.
    if end == start:
        return True

    count = 0
    qValues = []

    for i in range(start, end):
        line = gv.fileLines[i].strip().split()
        qValues.append(float(line[0]))

        if len(line) != 2:
            return False

        for value in line:
            if not ( (dp.isInt(value) or dp.isFloat(value)) and float(value) >= 0):
                return False

        count += 1

    if count < 4:
        return False

    if not dp.checkSorting(qValues):
        return False

    return True

def analizeParametersSystemData():
    ''' Analiza no arquivo os dados da Curva do Sistema, pertencente a janela Parametros do Sistema. Se tudo estiver OK, retorna True. '''

    i = gv.fileStartIndices['#parameters_system_start']
    e = gv.fileStartIndices['#parameters_system_end']

    # Se o arquivo não contiver dados de Curva do Sistema, retorna True.
    # Como os '_start' já apontam para o inicío dos dados, se estes dados estiverem vazios, irá apontar para '_end' também.
    if e == i:
        return True

    for i in range(i, i + 3):
        value = gv.fileLines[i].strip()
        if not ( (dp.isInt(value) or dp.isFloat(value) ) and float(value) > 0):
            return False

    i += 1

    rugValue = gv.fileLines[i].strip() # Rugosidade do material
    i += 1

    # Analisando o valor de rugosidade do material
    if rugValue == '':
        # Agora analisamos a idade da tubulacao
        value = gv.fileLines[i].strip()
        i += 1
        if value not in ['Ferro Fundido', 'PVC', 'PEAD']:
            return False

        value = gv.fileLines[i].strip()
        i += 1
        if value not in ['Nova', 'Antiga']:
            return False

        value = gv.fileLines[i].strip()
        i += 1
        if not ( (dp.isInt(value) or dp.isFloat(value) ) and float(value) > 0):
            return False

    else:
        for i in range(i, i + 3):
            value = gv.fileLines[i].strip()
            if not value == '':
                return False
        i += 1

    # Aqui, vamos verificar o somatorio dos coeficientes de singularidade
    sumValue = gv.fileLines[i].strip()
    i += 1

    if sumValue == '':
        for _ in range(0, 7):
            value = gv.fileLines[i].strip()
            i += 1
            if not (dp.isInt(value) and int(value) >= 0):
                return False

    else:
        if not ( (dp.isInt(sumValue) or dp.isFloat(sumValue)) and int(sumValue) >= 0):
            return False

        for _ in range(0, 7):
            value = gv.fileLines[i].strip()
            i += 1
            if not value == '':
                return False

    return True


def analizeExpensesData():
    ''' Analiza no arquivo os dados de Custos de Operacao e Indicadores Financeiros. Se tudo estiver OK, retorna True. '''

    start = gv.fileStartIndices['#expenses_start']
    bIsFirst = True

    for i in range(start, start + 11): # 10 sao os numeros e 1 e a cor.
        if bIsFirst:
            bIsFirst = False
            color = gv.fileLines[i].strip()
            if not (color == 'green' or color == 'blue'):
                return False

        else:
            value = gv.fileLines[i].strip()
            if not (dp.isInt(value) or dp.isFloat(value) or value == ''):
                return False

            if value != '':
                value = float(value)
                if value < 0:
                    return False

    return True

def analizeHydricData():
    ''' Analiza no arquivo os dados de Balanço Hídrico de Reservatório. Se tudo estiver OK, retorna True. '''

    index = gv.fileStartIndices['#hydric_start']

    for _ in range(0, 2):
        # Se uma string vazia existir aqui, todas as 7 a seguir tem que ser vazias também.
        if gv.fileLines[index].strip() == '':
            for _ in range(0, 7):
                if gv.fileLines[index].strip() != '':
                    return False
                index += 1
            continue

        for j in range(0, 7):
            # [0] Volume útil (m³)
            if j == 0:
                value = gv.fileLines[index].strip()
                if not (dp.isFloat(value) and float(value) >= 1):
                    return False
                index += 1

            # [1] Volume mínimo (m³) ou # [5] Volume inicial (m³)
            elif j == 1 or j == 5:
                value = gv.fileLines[index].strip()
                if not (dp.isFloat(value) and float(value) >= 0):
                    return False
                index += 1

            # [2] Volume máximo (m³)
            elif j == 2:
                value = gv.fileLines[index].strip()
                if not (dp.isFloat(value) and float(value) > float(gv.fileLines[index - 1].strip())):
                    return False
                index += 1

            # [3] Curva da demanda
            elif j == 3:
                words = gv.fileLines[index].strip().split()
                length = len(words)
                if length == 1:
                    if not (dp.isInt(words[0]) and int(words[0]) == -1):
                        return False
                elif length == 24:
                    for k in range(0, 24):
                        if not (dp.isFloat(words[k]) and float(words[k]) > 0):
                            return False
                else:
                    return False

                index += 1

            # [4] Dias de simulação
            elif j == 4:
                value = gv.fileLines[index].strip()
                if not (dp.isInt(value) and int(value) > 0):
                    return False
                index += 1

             # [6] Número de bombas
            elif j == 6:
                words = gv.fileLines[index].strip().split()
                if not (dp.isInt(words[0]) and int(words[0]) > 0):
                    return False

                values = words[1:]
                if int(words[0]) != len(values):
                    return False

                for k in range(0, len(values)):
                    if not (dp.isFloat(values[k]) and float(values[k]) > 0):
                        return False

                index += 1

    return True

def isFileIntegrityOK():
    """ Verifica a integridade dos dados do arquivo. Em caso de erro, retorna False. """

    if not gv.opened_file:
        return False

    if not gv.fileStartIndices:
        return False

    status = []

    try:
        if '#water_consumption_start' in gv.fileStartIndices.keys():
            data = copyWaterFileDataToList()
            status.append(analizeWaterData(data))

        if '#parameters_start' in gv.fileStartIndices.keys():
            status.append(analizeParametersData())

        if '#parameters_pump_start' in gv.fileStartIndices.keys():
            status.append(analizeParametersPumpData())

        if '#parameters_system_start' in gv.fileStartIndices.keys():
            status.append(analizeParametersSystemData())

        if '#expenses_start' in gv.fileStartIndices.keys():
            status.append(analizeExpensesData())

        if '#hydric_start' in gv.fileStartIndices.keys():
            status.append(analizeHydricData())

    except:
        return False

    return all(status)

def getEntrysDictAndFile():
    ''' Analiza o arquivo aberto e atualiza gv.fileStartIndices com um dicionario contendo as linhas '...start' e '...end' encontradas no arquivo e seus indices.
     Exemplo: {'#water_consumption_start': 1, '#water_consumption_end': 27, '#parameters_start': 48, ...}
    Atualiza gv.fileLines com todas as linhas do arquivo tambem. '''

    gv.fileStartIndices.clear()

    gv.opened_file.seek(0)
    gv.fileLines = gv.opened_file.readlines()

    i = 0

    for line in gv.fileLines:
        # if line[0] != '#':
        #     continue

        if line.strip()[-5:] == 'start':
            gv.fileStartIndices[f'{line.strip()}'] = i + 1  # O indice ja vai apontar para o inicio dos dados.

        if line.strip()[-3:] == 'end':
            gv.fileStartIndices[f'{line.strip()}'] = i  # O indice vai apontar exatamente para o indicador de fim de dados.

        i += 1

def getCSVFileObject(file_path, file_object):
    ''' Tenta abrir um arquivo .csv com ',' ou ';' como delimitador. Se os dois falharem, retorna None.
    Caso contrário, retorna o arquivo lido. '''

    try:
        file_object = open(file_path, 'r')
        csvRead = csv.reader(file_object, delimiter=',')
        return csvRead  # Se chegar até aqui, a leitura foi um sucesso.
    except:
        pass

    try:
        file_object = open(file_path, 'r')
        csvRead = csv.reader(file_object, delimiter=';')
        return csvRead  # Se chegar até aqui, a leitura foi um sucesso.
    except:
        return None

def openAndUpdateFileVariables(dialog):
    ''' Faz inicializacoes de abertura de arquivo nas variaves de arquivo em global_variables.py: `filename`, `file_dir`, `file_path`, `opened_file`
    e chamada função `getEntrysDictAndFile()`. '''

    gv.filename = dialog.GetFilename()
    gv.file_dir = dialog.GetDirectory()
    gv.file_path = os.path.join(gv.file_dir, gv.filename)
    gv.opened_file = open(gv.file_path, 'r')
    getEntrysDictAndFile()

def saveAndUpdateFileVariables(dialog):
    ''' Faz inicializacoes de salvamento de arquivo nas variaves de arquivo em global_variables.py: `filename`, `file_dir` e `file_path`. '''

    gv.filename = dialog.GetFilename()
    gv.filename = putFileSuffix(gv.filename, gv.file_suffix)
    gv.file_dir = dialog.GetDirectory()
    gv.file_path = os.path.join(gv.file_dir, gv.filename)

def clearFileVariables():
    ''' Seta as strings das variaveis gv. para vazias e fecha o arquivo, se tiver aberto. '''

    if gv.opened_file:
        gv.opened_file.close()

    gv.opened_file = None
    gv.filename = ''
    gv.file_dir = ''
    gv.file_path = ''
    gv.fileLines.clear()
    gv.fileStartIndices.clear()