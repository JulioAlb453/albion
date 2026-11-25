"""Lee `items.json` del volcado de datos del juego (ao-data/ao-bin-dumps, carpeta `formatted`)."""

import re
from collections.abc import Iterable

from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto

# El orden importa poco: los patrones no se solapan. Las variantes encantadas (`@1`…) no
# coinciden con ninguno, porque el encantamiento lo guarda `ObjetoRef`, no el catálogo.
_PATRONES: tuple[tuple[re.Pattern[str], CategoriaObjeto], ...] = (
    # `2H_TOOL_*` son herramientas de recolección, no armas.
    (re.compile(r"^T[1-8]_(?:MAIN|OFF|2H)_(?!TOOL_)[A-Z0-9_]+$"), CategoriaObjeto.ARMA),
    (re.compile(r"^T[1-8]_(?:ARMOR|HEAD|SHOES)_[A-Z0-9_]+$"), CategoriaObjeto.ARMADURA),
    (re.compile(r"^T[1-8]_ARTEFACT_[A-Z0-9_]+$"), CategoriaObjeto.ARTEFACTO),
)


def categoria_de(unique_name: str) -> CategoriaObjeto | None:
    for patron, categoria in _PATRONES:
        if patron.match(unique_name):
            return categoria
    return None


def _nombre(entrada: dict, unique_name: str) -> str:
    # Algunas entradas traen `LocalizedNames` en null.
    nombres = entrada.get("LocalizedNames") or {}
    return nombres.get("ES-ES") or nombres.get("EN-US") or unique_name


def leer_catalogo(entradas: Iterable[dict]) -> list[Objeto]:
    """Armas, armaduras y artefactos de crafteo, uno por identificador y en el orden del archivo."""
    objetos: dict[str, Objeto] = {}
    for entrada in entradas:
        unique_name = entrada.get("UniqueName")
        categoria = categoria_de(unique_name) if unique_name else None
        if categoria is not None and unique_name not in objetos:
            objetos[unique_name] = Objeto(unique_name, _nombre(entrada, unique_name), categoria)
    return list(objetos.values())
