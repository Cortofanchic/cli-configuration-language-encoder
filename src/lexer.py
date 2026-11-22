"""Модуль лексического анализа входного конфигурационного языка."""

import re
from dataclasses import dataclass

BINARY_BASE = 2
BINARY_PREFIX_LEN = 2
QUOTE_OFFSET = 1


class SyntaxConfigError(Exception):
    """Исключение при обнаружении синтаксической или семантической ошибки."""


@dataclass(frozen=True)
class Token:
    """Токен входного языка с типом, значением и позицией."""

    kind: str
    value: object
    line: int
    col: int


TOKEN_SPECS = [
    ("SKIP", r"[ \t\r\n]+"),
    ("ASSIGN", r"<-"),
    ("EXPR_START", r"\?\["),
    ("RBRACKET", r"\]"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("EQUAL", r"="),
    ("COMMA", r","),
    ("SEMICOLON", r";"),
    ("PLUS", r"\+"),
    ("NUMBER", r"0[bB][01]+"),
    ("STRING", r"'[^']*'"),
    ("IDENT", r"[a-zA-Z]+"),
    ("MISMATCH", r"."),
]

MASTER_PATTERN = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECS)
)


def _convert_token_value(kind: str, raw: str) -> object:
    """Преобразовать строковое представление токена в целевой тип."""
    if kind == "NUMBER":
        return int(raw[BINARY_PREFIX_LEN:], BINARY_BASE)
    if kind == "STRING":
        return raw[QUOTE_OFFSET:-QUOTE_OFFSET]
    return raw


def tokenize(text: str) -> list[Token]:
    """Разбить исходный текст на последовательность токенов."""
    tokens: list[Token] = []
    line = 1
    line_start = 0

    for match in MASTER_PATTERN.finditer(text):
        kind = match.lastgroup
        raw = match.group()
        col = match.start() - line_start + 1

        if kind == "SKIP":
            newlines = raw.count("\n")
            if newlines > 0:
                line += newlines
                line_start = match.end()
            continue

        if kind == "MISMATCH":
            raise SyntaxConfigError(
                f"Unexpected character '{raw}' at line {line}, col {col}"
            )

        value = _convert_token_value(kind, raw)
        tokens.append(Token(kind, value, line, col))

    tokens.append(Token("EOF", None, line, 1))
    return tokens