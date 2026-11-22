"""Модуль синтаксического анализа и вычисления константных выражений."""

from lexer import SyntaxConfigError, Token

MIN_UNARY_STACK = 1
MIN_BINARY_STACK = 2


class Parser:
    """Рекурсивный нисходящий парсер учебного конфигурационного языка."""

    def __init__(self, tokens: list[Token]) -> None:
        """Инициализировать парсер списком токенов."""
        self.tokens = tokens
        self.pos = 0
        self.constants: dict[str, object] = {}

    def current(self) -> Token:
        """Вернуть текущий токен без сдвига указателя."""
        return self.tokens[self.pos]

    def consume(self, expected_kind: str) -> Token:
        """Проверить тип текущего токена и перейти к следующему."""
        tok = self.current()
        if tok.kind != expected_kind:
            raise SyntaxConfigError(
                f"Expected {expected_kind}, got {tok.kind} "
                f"at line {tok.line}, col {tok.col}"
            )
        self.pos += 1
        return tok

    def parse_program(self) -> list[tuple[str, object]]:
        """Разобрать программу до конца файла и вернуть список элементов."""
        items: list[tuple[str, object]] = []
        while self.current().kind != "EOF":
            items.append(self._parse_top_level())
        return items

    def _parse_top_level(self) -> tuple[str, object]:
        """Разобрать объявление константы или корневое значение."""
        tok = self.current()
        is_const = (
            tok.kind == "IDENT"
            and tok.value != "dict"
            and self._peek_kind() == "ASSIGN"
        )
        if is_const:
            name = str(self.consume("IDENT").value)
            self.consume("ASSIGN")
            val = self.parse_value()
            self.consume("SEMICOLON")
            self.constants[name] = val
            return ("const", (name, val))
        return ("value", self.parse_value())

    def _peek_kind(self) -> str:
        """Посмотреть тип следующего токена без смещения."""
        next_idx = self.pos + 1
        if next_idx < len(self.tokens):
            return self.tokens[next_idx].kind
        return "EOF"

    def parse_value(self) -> object:
        """Разобрать число, строку, словарь или константное выражение."""
        tok = self.current()
        if tok.kind in ("NUMBER", "STRING"):
            self.pos += 1
            return tok.value
        if tok.kind == "EXPR_START":
            return self._parse_const_expr()
        if tok.kind == "IDENT" and tok.value == "dict":
            return self._parse_dict()
        raise SyntaxConfigError(
            f"Invalid value '{tok.value}' at line {tok.line}, col {tok.col}"
        )

    def _parse_dict(self) -> dict[str, object]:
        """Разобрать конструкцию словаря dict(имя = значение, ...)."""
        self.consume("IDENT")
        self.consume("LPAREN")
        result: dict[str, object] = {}
        while self.current().kind != "RPAREN":
            key_tok = self.consume("IDENT")
            key = str(key_tok.value)
            if key == "dict":
                raise SyntaxConfigError(
                    f"Reserved keyword 'dict' at line {key_tok.line}"
                )
            self.consume("EQUAL")
            result[key] = self.parse_value()
            if self.current().kind == "COMMA":
                self.consume("COMMA")
            elif self.current().kind != "RPAREN":
                raise SyntaxConfigError(
                    f"Expected ',' or ')' at line {self.current().line}"
                )
        self.consume("RPAREN")
        return result

    def _parse_const_expr(self) -> object:
        """Разобрать и вычислить постфиксное выражение ?[...]."""
        start_tok = self.consume("EXPR_START")
        stack: list[object] = []
        while self.current().kind != "RBRACKET":
            if self.current().kind == "EOF":
                raise SyntaxConfigError(
                    f"Unclosed expression at line {start_tok.line}"
                )
            self._eval_expr_token(stack)
        self.consume("RBRACKET")
        if len(stack) != MIN_UNARY_STACK:
            raise SyntaxConfigError(
                f"Invalid expression result at line {start_tok.line}"
            )
        return stack[0]

    def _eval_expr_token(self, stack: list[object]) -> None:
        """Обработать один токен внутри постфиксного выражения."""
        tok = self.current()
        self.pos += 1
        if tok.kind in ("NUMBER", "STRING"):
            stack.append(tok.value)
        elif tok.kind == "PLUS":
            self._apply_plus(stack, tok)
        elif tok.kind == "IDENT":
            self._apply_ident(stack, tok)
        else:
            raise SyntaxConfigError(
                f"Unexpected token '{tok.value}' in expression "
                f"at line {tok.line}"
            )

    def _apply_ident(self, stack: list[object], tok: Token) -> None:
        """Выполнить функцию chr/mod или подставить значение константы."""
        name = str(tok.value)
        if name == "chr":
            self._apply_chr(stack, tok)
        elif name == "mod":
            self._apply_mod(stack, tok)
        elif name in self.constants:
            stack.append(self.constants[name])
        else:
            raise SyntaxConfigError(
                f"Unknown identifier '{name}' at line {tok.line}"
            )

    def _apply_plus(self, stack: list[object], tok: Token) -> None:
        """Выполнить операцию сложения для двух чисел или двух строк."""
        if len(stack) < MIN_BINARY_STACK:
            raise SyntaxConfigError(
                f"Not enough operands for '+' at line {tok.line}"
            )
        right = stack.pop()
        left = stack.pop()
        if isinstance(left, int) and isinstance(right, int):
            stack.append(left + right)
        elif isinstance(left, str) and isinstance(right, str):
            stack.append(left + right)
        else:
            raise SyntaxConfigError(
                f"Incompatible types for '+' at line {tok.line}"
            )

    def _apply_chr(self, stack: list[object], tok: Token) -> None:
        """Выполнить функцию chr() над верхним числовым элементом стека."""
        if len(stack) < MIN_UNARY_STACK:
            raise SyntaxConfigError(
                f"Not enough operands for 'chr' at line {tok.line}"
            )
        val = stack.pop()
        if not isinstance(val, int):
            raise SyntaxConfigError(
                f"'chr' expects integer at line {tok.line}"
            )
        try:
            stack.append(chr(val))
        except ValueError as err:
            raise SyntaxConfigError(
                f"Invalid code point for 'chr' at line {tok.line}"
            ) from err

    def _apply_mod(self, stack: list[object], tok: Token) -> None:
        """Выполнить функцию mod() (остаток от деления) для двух чисел."""
        if len(stack) < MIN_BINARY_STACK:
            raise SyntaxConfigError(
                f"Not enough operands for 'mod' at line {tok.line}"
            )
        right = stack.pop()
        left = stack.pop()
        if not isinstance(left, int) or not isinstance(right, int):
            raise SyntaxConfigError(
                f"'mod' expects integers at line {tok.line}"
            )
        if right == 0:
            raise SyntaxConfigError(
                f"Division by zero in 'mod' at line {tok.line}"
            )
        stack.append(left % right)