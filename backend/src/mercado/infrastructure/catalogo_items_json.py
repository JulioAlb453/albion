"""Arma el catálogo con los dos archivos del volcado de datos del juego (ao-data/ao-bin-dumps):

- `items.json` (raíz): cada objeto con su tipo, su sección del mercado, calidad y encantamientos.
- `formatted/items.json`: los nombres traducidos.
"""

import re
from collections.abc import Iterable

from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto

_POR_SECCION: dict[str, CategoriaObjeto] = {
    "weapons": CategoriaObjeto.ARMA,
    "offhands": CategoriaObjeto.ARMA,
    "armors": CategoriaObjeto.ARMADURA,
    "head": CategoriaObjeto.ARMADURA,
    "shoes": CategoriaObjeto.ARMADURA,
    "capes": CategoriaObjeto.CAPA,
    "bags": CategoriaObjeto.BOLSA,
    "mounts": CategoriaObjeto.MONTURA,
    "consumables": CategoriaObjeto.CONSUMIBLE,
    "crafting": CategoriaObjeto.RECURSO,
    "artefacts": CategoriaObjeto.ARTEFACTO,
    "gathering": CategoriaObjeto.RECOLECCION,
    "farming": CategoriaObjeto.GRANJA,
    "furniture": CategoriaObjeto.MOBILIARIO,
    "vanity": CategoriaObjeto.APARIENCIA,
    "other": CategoriaObjeto.OTRO,
}

# Solo objetos con tier: el resto (tesoros, paquetes de comercio…) no encaja en `ObjetoRef`.
_CON_TIER = re.compile(r"^T[1-8]_[A-Z0-9_]+$")


def _lista(valor) -> list:
    if valor is None:
        return []
    return valor if isinstance(valor, list) else [valor]


def _encantamientos(entrada: dict) -> tuple[int, int]:
    fijo = entrada.get("@enchantmentlevel")
    if fijo is not None:  # recurso encantado: es su propio objeto
        return int(fijo), int(fijo)
    niveles = [int(e["@enchantmentlevel"]) for e in _lista((entrada.get("enchantments") or {}).get("enchantment"))]
    return 0, max(niveles, default=0)


def _vendible(entrada: dict) -> CategoriaObjeto | None:
    if entrada.get("@tradable") == "false" or entrada.get("@showinmarketplace") == "false":
        return None
    if not _CON_TIER.match(entrada.get("@uniquename", "")):
        return None
    return _POR_SECCION.get(entrada.get("@shopcategory", ""))


def _nombres(entradas: Iterable[dict]) -> dict[str, str]:
    nombres: dict[str, str] = {}
    for entrada in entradas:
        localizados = entrada.get("LocalizedNames") or {}  # a veces viene en null
        nombre = localizados.get("ES-ES") or localizados.get("EN-US")
        if entrada.get("UniqueName") and nombre:
            nombres.setdefault(entrada["UniqueName"], nombre)
    return nombres


def leer_catalogo(datos_items: dict, entradas_nombres: Iterable[dict]) -> list[Objeto]:
    """Todo lo que se puede vender en el mercado, uno por identificador."""
    nombres = _nombres(entradas_nombres)
    objetos: dict[str, Objeto] = {}
    for tipo, valor in datos_items["items"].items():
        if tipo.startswith("@") or tipo == "shopcategories":
            continue
        for entrada in _lista(valor):
            if not isinstance(entrada, dict):
                continue
            categoria = _vendible(entrada)
            base_id = entrada.get("@uniquename", "")
            if categoria is None or base_id in objetos:
                continue
            minimo, maximo = _encantamientos(entrada)
            nombre = nombres.get(base_id) or nombres.get(f"{base_id}@{minimo}") or base_id
            objetos[base_id] = Objeto(
                base_id, nombre, categoria,
                tiene_calidad=int(entrada.get("@maxqualitylevel", "1")) > 1,
                encantamiento_min=minimo, encantamiento_max=maximo,
            )
    return list(objetos.values())
