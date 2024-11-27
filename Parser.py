import re

# Типы лексем
TOKEN_TYPES = {
    'KEYWORD': ['VAR', 'BEGIN', 'END', 'FOR', 'TO', 'READ', 'WRITE'],
    'OPERATOR': ['+', '-', '*', '/', '=', '(', ')', ';', ','],
    'IDENTIFIER': r'^[a-zA-Z_][a-zA-Z0-9_]*$',
    'CONSTANT': r'^\d+$'
}

# Таблица символов
symbol_table = {
    'identifiers': {},  # Для хранения идентификаторов
    'constants': {}  # Для хранения констант
}


# Лексический анализатор
class Lexer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []  # Список лексем
        self.errors = []  # Список ошибок
        self.current_position = 0

    def tokenize(self):
        # Разбиваем исходный код на токены по пробелам и операторам
        pattern = r'(\bVAR\b|\bBEGIN\b|\bEND\b|\bFOR\b|\bTO\b|\bREAD\b|\WRITE\b|[+\-*/=(),;]|\b\d+\b|\b[a-zA-Z_][a-zA-Z0-9_]*\b)'
        raw_tokens = re.findall(pattern, self.source_code)

        for raw_token in raw_tokens:
            token_type = self.identify_token_type(raw_token)
            if token_type:
                self.tokens.append((token_type, raw_token))
                self.add_to_symbol_table(token_type, raw_token)
            else:
                self.errors.append(f"Unknown token: {raw_token}")

        if not self.errors:
            return self.tokens
        else:
            return self.errors

    def identify_token_type(self, token):
        # Проверка на ключевое слово
        if token in TOKEN_TYPES['KEYWORD']:
            return 'KEYWORD'

        # Проверка на оператор
        if token in TOKEN_TYPES['OPERATOR']:
            return 'OPERATOR'

        # Проверка на идентификатор
        if re.match(TOKEN_TYPES['IDENTIFIER'], token):
            return 'IDENTIFIER'

        # Проверка на числовую константу
        if re.match(TOKEN_TYPES['CONSTANT'], token):
            return 'CONSTANT'

        # Неопознанный токен
        return None

    def add_to_symbol_table(self, token_type, token):
        if token_type == 'IDENTIFIER':
            if token not in symbol_table['identifiers']:
                symbol_table['identifiers'][token] = None  # Начальное значение идентификатора
        elif token_type == 'CONSTANT':
            if token not in symbol_table['constants']:
                symbol_table['constants'][token] = int(token)  # Числовая константа


# Пример исходного кода программы
source_code = """
VAR x, y, z : integer;
BEGIN
x = 5;
y = -x + 3;
z = x - y;
WRITE y;
FOR i = 1 TO 10 DO BEGIN    
    WRITE i;
END
END
"""

# Лексический анализ
lexer = Lexer(source_code)
tokens_or_errors = lexer.tokenize()

# Вывод результатов лексического анализа
if lexer.errors:
    print("Ошибки при лексическом анализе:")
    for error in lexer.errors:
        print(error)
else:
    print("Лексемы:")
    for token_type, token in tokens_or_errors:
        print(f"{token_type}: {token}")

    print("\nТаблица символов:")
    print("Идентификаторы:", symbol_table['identifiers'])
    print("Константы:", symbol_table['constants'])
