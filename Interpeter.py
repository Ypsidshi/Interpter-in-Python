# Типы лексем
import re

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
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.errors = []

    @classmethod
    def from_file(cls, filename):
        """Создает объект Lexer из содержимого файла."""
        try:
            with open(filename, 'r') as file:
                content = file.read()
            return cls(content)
        except FileNotFoundError:
            raise ValueError(f"Файл {filename} не найден.")

    def tokenize(self):
        pattern = r'(\bVAR\b|\bBEGIN\b|\bEND\b|\bFOR\b|\bTO\b|\bREAD\b|\bWRITE\b|\bDO\b|[+\-*/=(),;:]|\b\d+\b|\b[a-zA-Z_][a-zA-Z0-9_]*\b)'
        raw_tokens = re.findall(pattern, self.source)

        for raw_token in raw_tokens:
            token_type = self.identify_token_type(raw_token)
            if token_type:
                if token_type == 'IDENTIFIER' and len(raw_token) > 10:
                    self.errors.append(f"Имя переменной '{raw_token}' превышает допустимую длину (10 символов).")
                else:
                    self.tokens.append((token_type, raw_token))
                    self.add_to_symbol_table(token_type, raw_token)
            else:
                self.errors.append(f"Неизвестный токен: {raw_token}")

        return self.tokens if not self.errors else self.errors

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
        self.block_depth = 0  # Счётчик вложенных BEGIN/END

    def parse(self):
        if not self.current_token:
            raise ValueError("Нет токенов для анализа.")

        while self.current_token and self.current_token[1] == 'VAR':
            self.parse_variable_declaration()

        self.parse_program()

        if self.block_depth > 0:
            raise SyntaxError("Программа завершена без закрытия всех блоков BEGIN/END.")
        elif self.block_depth < 0:
            raise SyntaxError("Обнаружено больше ключевых слов END, чем BEGIN.")

    def parse_variable_declaration(self):
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
            else:
                raise SyntaxError("Ошибка в объявлении переменных. Ожидалось ',' или ':'.")
            symbol_table['identifiers'][var_name] = 0

    def parse_program(self):
        self.expect('KEYWORD', 'BEGIN')
        self.block_depth += 1  # Увеличиваем глубину блока

        while self.current_token and self.current_token[1] != 'END':
            self.parse_statement()
            if self.current_token and self.current_token[1] == ';':
                self.expect('OPERATOR', ';')

        if not self.current_token:
            raise SyntaxError("Программа завершена без ключевого слова END.")

        self.expect('KEYWORD', 'END')
        self.block_depth -= 1  # Уменьшаем глубину блока

        # Если после `END` остались токены, это ошибка
        if self.current_token:
            raise SyntaxError("Код после закрытия блока END недопустим.")

    def parse_statement(self):
        if self.current_token[0] == 'IDENTIFIER':
            self.parse_assignment()
        elif self.current_token[1] == 'WRITE':
            self.parse_write()
        elif self.current_token[1] == 'FOR':
            self.parse_for_loop()
        elif self.current_token[1] == 'READ':
            self.parse_read()
        else:
            raise SyntaxError(f"Неожиданное выражение: {self.current_token}")

    def parse_assignment(self):
        identifier = self.current_token[1]
        if identifier not in symbol_table['identifiers']:
            raise NameError(f"Переменная '{identifier}' не объявлена.")
        self.expect('IDENTIFIER')
        self.expect('OPERATOR', '=')
        value = self.parse_expression()
        symbol_table['identifiers'][identifier] = value

    def parse_for_loop(self):
        self.expect('KEYWORD', 'FOR')
        if self.current_token[0] != 'IDENTIFIER':
            raise SyntaxError("Ожидалось имя переменной после FOR.")
        loop_var = self.current_token[1]
        self.expect('IDENTIFIER')
        self.expect('OPERATOR', '=')
        start_value = self.parse_expression()
        self.expect('KEYWORD', 'TO')
        end_value = self.parse_expression()
        self.expect('KEYWORD', 'DO')
        self.expect('KEYWORD', 'BEGIN')

        saved_index = self.current_token_index
        self.block_depth += 1  # Увеличиваем вложенность блока

        for i in range(start_value, end_value + 1):
            symbol_table['identifiers'][loop_var] = i
            self.current_token_index = saved_index
            self.current_token = self.tokens[self.current_token_index]

            while self.current_token and self.current_token[1] != 'END':
                self.parse_statement()
                if self.current_token and self.current_token[1] == ';':
                    self.expect('OPERATOR', ';')

        if not self.current_token or self.current_token[1] != 'END':
            raise SyntaxError("Ожидалось ключевое слово END для завершения цикла FOR.")

        self.expect('KEYWORD', 'END')
        self.block_depth -= 1  # Уменьшаем вложенность блока

    def parse_read(self):
        self.expect('KEYWORD', 'READ')
        if self.current_token[0] == 'IDENTIFIER':
            var_name = self.current_token[1]
            self.expect('IDENTIFIER')
            if var_name in symbol_table['identifiers']:
                value = int(input(f"Введите значение для {var_name}: "))
                symbol_table['identifiers'][var_name] = value
            else:
                raise NameError(f"Переменная '{var_name}' не объявлена.")
        else:
            raise SyntaxError("Ожидалось имя переменной после READ.")

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
                if right_value == 0:
                    raise ZeroDivisionError("Ошибка: деление на ноль.")
                left_value //= right_value
        return left_value

    def parse_factor(self):
        if self.current_token[0] == 'CONSTANT':
            value = int(self.current_token[1])
            self.expect('CONSTANT')
            return value
        elif self.current_token[0] == 'IDENTIFIER':
            identifier = self.current_token[1]
            if identifier not in symbol_table['identifiers']:
                raise NameError(f"Переменная '{identifier}' не объявлена.")
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
        if self.current_token is None:
            raise SyntaxError(
                f"Неожиданный конец программы. Ожидалось {token_type} {token_value if token_value else ''}."
            )

        if self.current_token[0] == token_type:
            if token_value is None or self.current_token[1] == token_value:
                # Если встречается END вне контекста блока
                if token_value == 'END' and self.block_depth == 0:
                    raise SyntaxError("Ключевое слово END найдено вне блока BEGIN.")

                self.current_token_index += 1
                if self.current_token_index < len(self.tokens):
                    self.current_token = self.tokens[self.current_token_index]
                else:
                    self.current_token = None
            else:
                raise SyntaxError(f"Ожидалось '{token_value}', но получено '{self.current_token[1]}'.")
        else:
            raise SyntaxError(f"Ожидался тип токена '{token_type}', но получено '{self.current_token[0]}'.")


# Загрузка исходного кода из файла
filename = "source.txt"  # Укажите имя файла с исходным кодом
try:
    lexer = Lexer.from_file(filename)
    tokens_or_errors = lexer.tokenize()

    # Синтаксический анализ и интерпретация
    if not lexer.errors:
        parser = Parser(tokens_or_errors)
        try:
            parser.parse()
            print("\nТаблица символов после выполнения:")
            print("Идентификаторы:", symbol_table['identifiers'])
            print("Константы:", symbol_table['constants'])
        except Exception as e:
            print(f"Ошибка: {e}")
    else:
        print("Ошибки при лексическом анализе:")
        for error in lexer.errors:
            print(error)
except ValueError as e:
    print(e)