"""
global_variables.py
Contem as variaveis globais do programa.
"""

# Referencia da janela de boas vidas. Ou a exibimos e escondemos ou a destruimos.
welcome_screen = None

opened_file = None
filename = ''
file_dir = ''
file_path = ''
file_suffix = '.lenhs'

# Variavel deve conter as linhas do arquivo. Deve ser apagado, usando .clear(), quando o usuario modifica o arquivo em texto
# e re-populado quando com as modificacoes.
fileLines = []

# Dicionario contendo as linhas '...start' encontradas no arquivo e seus indices + 1, para que apontem para o inicio dos dados.
# Exemplo: {'#water_consumption_start': 1, '#parameters_start': 48, ...}
fileStartIndices = {}

tooltipList = [
    'Volume de água transportado que passa em uma determinada seção por intervalo de tempo.',
    'Definida pela soma do desnível geométrico mais a perda de carga existente entre diferentes pontos no sistema.',
    'É a razão entre a potência mecânica no eixo do motor e a potência elétrica fornecida pela rede elétrica.',
    'É a razão entre a potência hidráulica do escoamento e a potência mecânica no eixo do motor.',
    'Quantidade de bombas dispostas em paralelo no sistema analisado. Utiliza-se dessa técnica visando aumentar a vazão bombeada pelo sistema elevatório.',
    'Compreende o número de horas em que o(s) conjunto(s) motobomba(s) mantiveram-se operando na faixa horária que possui maior custo financeiro. Neste software, considerou-se que o horário de ponta compreende o período entre às 18h e 21h.',
    'Compreende o número de horas em que o(s) conjunto(s) motobomba(s) mantiveram-se operando na faixa horária que possui menor custo financeiro. Neste software, considerou-se que o horário fora de ponta na cobrança da fatura de energia elétrica compreende o período entre às 00h e 17:59h e 21:01h 23:59h.',
    'Total de energia consumida pelo(s) conjunto(s) motobombas(s) dentro dos limites da faixa horária definida como horário de ponta.',
    'Total de energia consumida pelo(s) conjunto(s) motobombas(s) dentro dos limites da faixa horária definida como horário fora de ponta.',
    'É a soma da parcela de consumo de energia no horário de ponta com a parcela de consumo na ponta.',
    'Volume total mensal aduzido pelo conjunto motobomba entre as diferentes unidades do sistema de abastecimento. O volume bombeado é o produto resultante entre a vazão bombeada e o número de horas mensais em que a bomba manteve-se operando com respectiva vazão de bombeamento.',
    'O consumo específico de energia define-se como sendo a energia necessária para se elevar 1m³ de água entre os locais de interesse.',
    'O consumo específico normalizado proposto pelo IWA (International Water Association), tem por objetivo a comparar estações de recalque distintas que operam com diferentes alturas manométricas. A formulação do CEN permite que as estações tenham a mesma base de comparação, ou seja, definida para 100m de altura para avaliar o desempenho energético. O CEN pode ser compreendido também, como o inverso do rendimento do conjunto moto-bomba.',
]

RED_ERROR = '#ffa6a6'
YELLOW_WARNING = '#fce9b3'

BACKGROUND_COLOR = '#a3a9b5'