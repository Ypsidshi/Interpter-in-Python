import re

# Типы лексем
TOKEN_TYPES = {
    'KEYWORD': ['VAR', 'BEGIN', 'END', 'FOR', 'TO', 'READ', 'WRITE', 'DO'],
    'OPERATOR': ['+', '-', '*', '/', '=', '(', ')', ';', ',', ':'],
    'IDENTIFIER': r'^[a-zA-Z_][a-zA-Z0-9_]*$',
    'CONSTANT': r'^\d+$'
}

# Таблица символов
symbol_table = {
    'identifiers': {},
    'constants': {}
}

class Lexer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.errors = []
        self.current_position = 0

    def tokenize(self):
        pattern = r'(\bVAR\b|\bBEGIN\b|\bEND\b|\bFOR\b|\bTO\b|\bREAD\b|\bWRITE\b|\bDO\b|[+\-*/=(),;:]|\b\d+\b|\b[a-zA-Z_][a-zA-Z0-9_]*\b)'
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
        if token in TOKEN_TYPES['KEYWORD']:
            return 'KEYWORD'
        if token in TOKEN_TYPES['OPERATOR']:
            return 'OPERATOR'
        if re.match(TOKEN_TYPES['IDENTIFIER'], token):
            return 'IDENTIFIER'
        if re.match(TOKEN_TYPES['CONSTANT'], token):
            return 'CONSTANT'
        return None

    def add_to_symbol_table(self, token_type, token):
        if token_type == 'IDENTIFIER':
            if token not in symbol_table['identifiers']:
                symbol_table['identifiers'][token] = None
        elif token_type == 'CONSTANT':
            if token not in symbol_table['constants']:
                symbol_table['constants'][token] = int(token)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = tokens[self.current_token_index] if tokens else None

    def parse(self):
        if not self.current_token:
            raise ValueError("Нет токенов для анализа.")

        self.parse_variable_declaration()
        self.parse_program()

    def parse_variable_declaration(self):
        if self.current_token and self.current_token[1] == 'VAR':
            self.expect('KEYWORD', 'VAR')
            while self.current_token and self.current_token[0] == 'IDENTIFIER':
                var_name = self.current_token[1]
                self.expect('IDENTIFIER')
                if self.current_token and self.current_token[1] == ',':
                    self.expect('OPERATOR', ',')
                elif self.current_token and self.current_token[1] == ':':
                    self.expect('OPERATOR', ':')
                    self.expect('IDENTIFIER', 'integer')
                    self.expect('OPERATOR', ';')
                    break
                symbol_table['identifiers'][var_name] = 0

    def parse_program(self):
        self.expect('KEYWORD', 'BEGIN')
        while self.current_token and self.current_token[1] != 'END':
            self.parse_statement()
            # Ожидаем ; после каждого оператора, если это не конец блока
            if self.current_token and self.current_token[1] == ';':
                self.expect('OPERATOR', ';')
        self.expect('KEYWORD', 'END')

    def parse_statement(self):
        if self.current_token[0] == 'IDENTIFIER':
            self.parse_assignment()
        elif self.current_token[1] == 'WRITE':
            self.parse_write()
        elif self.current_token[1] == 'FOR':
            self.parse_for_loop()
        else:
            raise SyntaxError(f"Неожиданное выражение: {self.current_token}")

    def parse_assignment(self):
        identifier = self.current_token[1]
        self.expect('IDENTIFIER')
        self.expect('OPERATOR', '=')
        value = self.parse_expression()
        symbol_table['identifiers'][identifier] = value
        # Завершение выражения
        if self.current_token and self.current_token[1] == ';':
            self.expect('OPERATOR', ';')

    def parse_for_loop(self):
        self.expect('KEYWORD', 'FOR')
        loop_var = self.current_token[1]
        self.expect('IDENTIFIER')
        self.expect('OPERATOR', '=')
        start_value = self.parse_expression()
        self.expect('KEYWORD', 'TO')
        end_value = self.parse_expression()
        self.expect('KEYWORD', 'DO')
        self.expect('KEYWORD', 'BEGIN')

        saved_index = self.current_token_index
        for i in range(start_value, end_value + 1):
            symbol_table['identifiers'][loop_var] = i
            self.current_token_index = saved_index
            self.current_token = self.tokens[self.current_token_index]
            while self.current_token and self.current_token[1] != 'END':
                self.parse_statement()
                if self.current_token and self.current_token[1] == ';':
                    self.expect('OPERATOR', ';')

        self.expect('KEYWORD', 'END')

    def parse_write(self):
        self.expect('KEYWORD', 'WRITE')
        value = self.parse_expression()
        print(f"OUTPUT: {value}")


    def parse_expression(self):
        left_value = self.parse_term()
        while self.current_token and self.current_token[1] in ('+', '-'):
            operator = self.current_token[1]
            self.expect('OPERATOR', operator)
            right_value = self.parse_term()
            if operator == '+':
                left_value += right_value
            elif operator == '-':
                left_value -= right_value
        return left_value

    def parse_term(self):
        left_value = self.parse_factor()
        while self.current_token and self.current_token[1] in ('*', '/'):
            operator = self.current_token[1]
            self.expect('OPERATOR', operator)
            right_value = self.parse_factor()
            if operator == '*':
                left_value *= right_value
            elif operator == '/':
                left_value //= right_value
        return left_value

    def parse_factor(self):
        if self.current_token[0] == 'CONSTANT':
            value = int(self.current_token[1])
            self.expect('CONSTANT')
            return value
        elif self.current_token[0] == 'IDENTIFIER':
            identifier = self.current_token[1]
            self.expect('IDENTIFIER')
            return symbol_table['identifiers'].get(identifier, 0)
        elif self.current_token[1] == '(':
            self.expect('OPERATOR', '(')
            value = self.parse_expression()
            self.expect('OPERATOR', ')')
            return value
        elif self.current_token[1] == '-':  # Унарный минус
            self.expect('OPERATOR', '-')
            return -self.parse_factor()
        else:
            raise SyntaxError(f"Неправильное выражение: {self.current_token}")

    def expect(self, token_type, token_value=None):
        if self.current_token and self.current_token[0] == token_type:
            if token_value is None or self.current_token[1] == token_value:
                self.current_token_index += 1
                if self.current_token_index < len(self.tokens):
                    self.current_token = self.tokens[self.current_token_index]
                else:
                    self.current_token = None
            else:
                raise SyntaxError(f"Ожидалось {token_value}, но получено {self.current_token[1]}")
        else:
            raise SyntaxError(f"Ожидалось {token_type}, но получено {self.current_token[0]}")

# Пример исходного кода программы
#-6 + 3 = -3
# 6 / -3 =  -2
#result = 6
source_code = """
VAR x, y, z : integer;
BEGIN
x = 6;
d = 100;
y = -x + 3; 
z = (-x - y) * (x / y);
WRITE y;
WRITE z;
FOR i = 1 TO 10 DO BEGIN    
    WRITE i;
END
END
"""

# Лексический анализ
lexer = Lexer(source_code)
tokens_or_errors = lexer.tokenize()

# Синтаксический анализ и интерпретация
if not lexer.errors:
    parser = Parser(tokens_or_errors)
    try:
        parser.parse()
        print("\nТаблица символов после выполнения:")
        print("Идентификаторы:", symbol_table['identifiers'])
        print("Константы:", symbol_table['constants'])
    except SyntaxError as e:
        print(f"Синтаксическая ошибка: {e}")
else:
    print("Ошибки при лексическом анализе:")
    for error in lexer.errors:
        print(error)
