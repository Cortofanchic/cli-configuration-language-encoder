"""Точка входа инструмента командной строки."""

import argparse
import sys
from pathlib import Path

from lexer import SyntaxConfigError, tokenize
from parser import Parser
from xml_writer import to_xml_string


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Convert educational config language to XML."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input configuration file.",
    )
    return parser.parse_args(argv)


def convert_text(source: str) -> str:
    """Выполнить полный цикл трансляции текста конфигурации в XML."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    items = parser.parse_program()
    return to_xml_string(items)


def main(argv: list[str] | None = None) -> int:
    """Прочитать файл, выполнить трансляцию и вывести XML в stdout."""
    args = parse_args(argv)
    file_path = Path(args.input)
    try:
        content = file_path.read_text(encoding="utf-8")
        xml_output = convert_text(content)
        sys.stdout.write(f"{xml_output}\n")
        return 0
    except OSError as err:
        sys.stderr.write(f"File error: {err}\n")
        return 1
    except SyntaxConfigError as err:
        sys.stderr.write(f"Syntax error: {err}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())