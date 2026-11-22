"""Модуль преобразования разобранной структуры данных в формат XML."""

import xml.etree.ElementTree as ET


def _build_node(parent: ET.Element, tag: str, value: object) -> None:
    """Рекурсивно построить XML-узел для значения."""
    elem = ET.SubElement(parent, tag)
    if isinstance(value, dict):
        elem.set("type", "dict")
        for key, item in value.items():
            _build_node(elem, key, item)
    elif isinstance(value, int):
        elem.set("type", "number")
        elem.text = str(value)
    elif isinstance(value, str):
        elem.set("type", "string")
        elem.text = value


def to_xml_string(items: list[tuple[str, object]]) -> str:
    """Сформировать отформатированный XML-документ из списка элементов."""
    root = ET.Element("config")
    for kind, payload in items:
        if kind == "const":
            name, val = payload
            const_elem = ET.SubElement(root, "constant")
            const_elem.set("name", str(name))
            _build_node(const_elem, "value", val)
        else:
            _build_node(root, "item", payload)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode")